#!/usr/bin/env bash
# ============================================================
#  Barounzx bot - Ubuntu VPS (Oracle Cloud Always Free) o'rnatuvchisi
#  Ishlatish:
#    git clone https://github.com/smuratbay957-dot/barounzx.git ~/barounzx
#    bash ~/barounzx/deploy/setup_vps.sh
# ============================================================
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/smuratbay957-dot/barounzx.git}"
APP_DIR="${APP_DIR:-$HOME/barounzx}"

echo "== 1/5: kerakli paketlar =="
sudo apt-get update -y
sudo apt-get install -y git python3 python3-venv python3-pip

echo "== 2/5: kodni olish =="
if [ -d "$APP_DIR/.git" ]; then
    git -C "$APP_DIR" pull --ff-only
else
    git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR/bot"

echo "== 3/5: virtualenv va kutubxonalar =="
python3 -m venv .venv
# shellcheck disable=SC1091
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "== 4/5: .env =="
if [ ! -f .env ]; then
    bash setup_env.sh
else
    echo ".env allaqachon bor, o'zgartirilmadi."
fi

echo "== 5/5: systemd xizmati =="
SERVICE_SRC="$APP_DIR/deploy/barounzx-bot.service"
SERVICE_DST="/etc/systemd/system/barounzx-bot.service"
sudo sed -e "s|__USER__|$USER|g" -e "s|__APP_DIR__|$APP_DIR|g" "$SERVICE_SRC" | sudo tee "$SERVICE_DST" >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now barounzx-bot
sleep 2
sudo systemctl --no-pager --full status barounzx-bot || true

echo
echo "Tayyor! Loglar:  journalctl -u barounzx-bot -f"
