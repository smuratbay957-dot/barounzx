# ============================================================
#  Barounzx Telegram bot - sozlamalar
#  Sirli ma'lumotlar .env faylidan o'qiladi (gitga yuklanmaydi!)
# ============================================================
import os

try:
    from dotenv import load_dotenv
except ImportError:  # web app uchun dotenv shart emas
    def load_dotenv(*args, **kwargs):
        return False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# --- Asosiy ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6154610636"))

# --- Majburiy obuna ---
# Private guruh uchun username o'rniga raqamli chat_id yozing (masalan -1001234567890).
def _chat_ref(value: str):
    value = (value or "").strip()
    if value.lstrip("-").isdigit():
        return int(value)
    return value


CHANNEL_USERNAME = _chat_ref(os.getenv("CHANNEL_USERNAME", "@megaskils"))
GROUP_USERNAME = _chat_ref(os.getenv("GROUP_USERNAME", "@megaskills"))
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/megaskils")
GROUP_URL = os.getenv("GROUP_URL", "https://t.me/megaskills")

# --- Iqtisod ---
STARS_TO_COINS = int(os.getenv("STARS_TO_COINS", "10"))   # 1 Star = 10 tanga
START_COINS = int(os.getenv("START_COINS", "0"))
DAILY_COINS = int(os.getenv("DAILY_COINS", "50"))
XP_PER_SKILL = int(os.getenv("XP_PER_SKILL", "20"))

# --- Saqlash ---
# Nisbiy yo'l bot papkasiga nisbatan hisoblanadi (web app va bot bir xil faylni ko'rsin).
_db_path = os.getenv("DB_PATH", "barounzx_bot.db")
DB_PATH = _db_path if os.path.isabs(_db_path) else os.path.join(BASE_DIR, _db_path)

# --- Sayt ---
# GitHub Pages manzili (botdagi "Saytni ochish" tugmasi uchun).
SITE_URL = os.getenv("SITE_URL", "https://smuratbay957-dot.github.io/barounzx/")

# --- Sayt API (ixtiyoriy, kelajakda) ---
SITE_API_URL = os.getenv("SITE_API_URL", "")
SITE_API_KEY = os.getenv("SITE_API_KEY", "")

# --- Proxy (PythonAnywhere FREE plan uchun) ---
# Free planda tashqi internetga faqat proxy orqali chiqiladi.
# PA'da .env ga:  PROXY_URL=http://proxy.server:3128
# Lokal/VPS'da bo'sh qoldiring.
PROXY_URL = os.getenv("PROXY_URL", "")
