# ============================================================
#  Barounzx Telegram bot - sozlamalar
#  Sirli ma'lumotlar .env faylidan o'qiladi (gitga yuklanmaydi!)
# ============================================================
import os
from dotenv import load_dotenv

load_dotenv()

# --- Asosiy ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6154610636"))

# --- Majburiy obuna ---
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@megaskils")
GROUP_USERNAME = os.getenv("GROUP_USERNAME", "@megaskills")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/megaskils")
GROUP_URL = os.getenv("GROUP_URL", "https://t.me/megaskills")

# --- Iqtisod ---
STARS_TO_COINS = int(os.getenv("STARS_TO_COINS", "10"))   # 1 Star = 10 tanga
START_COINS = int(os.getenv("START_COINS", "0"))
DAILY_COINS = int(os.getenv("DAILY_COINS", "50"))
XP_PER_SKILL = int(os.getenv("XP_PER_SKILL", "20"))

# --- Saqlash ---
DB_PATH = os.getenv("DB_PATH", "barounzx_bot.db")

# --- Sayt bilan bog'lanish (keyinroq PythonAnywhere) ---
# Bo'sh bo'lsa: login "offline rejim"da saqlanadi (tekshirilmaydi).
SITE_API_URL = os.getenv("SITE_API_URL", "")
SITE_API_KEY = os.getenv("SITE_API_KEY", "")

# --- Proxy (PythonAnywhere FREE plan uchun) ---
# Free planda tashqi internetga faqat proxy orqali chiqiladi.
# PA'da .env ga:  PROXY_URL=http://proxy.server:3128
# Lokal/VPS'da bo'sh qoldiring.
PROXY_URL = os.getenv("PROXY_URL", "")
