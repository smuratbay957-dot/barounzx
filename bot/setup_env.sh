#!/usr/bin/env bash
# ============================================================
#  Barounzx bot - .env faylini yaratish (PythonAnywhere / server)
#  Ishlatish:  bash setup_env.sh
# ============================================================
set -e
cd "$(dirname "$0")"

if [ -f .env ]; then
    echo "⚠️  .env allaqachon mavjud. Zaxira: .env.bak"
    cp .env .env.bak
fi

echo "==== Barounzx bot .env sozlamasi ===="
read -rp "BOT_TOKEN: " BOT_TOKEN
read -rp "ADMIN_ID [6154610636]: " ADMIN_ID; ADMIN_ID=${ADMIN_ID:-6154610636}
read -rp "CHANNEL_USERNAME [@megaskils]: " CHANNEL; CHANNEL=${CHANNEL:-@megaskils}
read -rp "GROUP_USERNAME [@megaskills]: " GROUP; GROUP=${GROUP:-@megaskills}
read -rp "SITE_API_URL (bo'sh qoldirsangiz ham bo'ladi): " SITE_API_URL

cat > .env <<EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_ID=$ADMIN_ID
CHANNEL_USERNAME=$CHANNEL
GROUP_USERNAME=$GROUP
CHANNEL_URL=https://t.me/${CHANNEL#@}
GROUP_URL=https://t.me/${GROUP#@}
STARS_TO_COINS=10
START_COINS=0
DAILY_COINS=50
XP_PER_SKILL=20
DB_PATH=barounzx_bot.db
SITE_API_URL=$SITE_API_URL
SITE_API_KEY=
EOF

chmod 600 .env
echo ""
echo "✅ .env yaratildi va himoyalandi (chmod 600)."
echo "▶️  Endi ishga tushiring:  python3 main.py"
