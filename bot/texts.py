# ============================================================
#  Barounzx bot - matnlar (o'zbekcha) va chiroyli kartalar
# ============================================================
from html import escape

from config import STARS_TO_COINS, XP_PER_SKILL

RARITY_EMOJI = {
    "common": "⚪",
    "uncommon": "🟢",
    "rare": "🔵",
    "epic": "🟣",
    "legendary": "🟠",
    "mythic": "🔴",
    "admin": "👑",
}


def rarity_emoji(rarity: str) -> str:
    return RARITY_EMOJI.get((rarity or "").strip().lower(), "✨")


# ---------------- Asosiy ----------------
START_NEW = (
    "👋 <b>Barounzx botiga xush kelibsiz!</b>\n\n"
    "Bu botda siz <b>SP</b> yig'asiz, <b>tanga</b> ishlaysiz va "
    "saytdagi darajangizni oshirasiz.\n\n"
    "📢 Avval kanal va guruhga obuna bo'ling."
)


def subscribed_text(user: dict) -> str:
    if user.get("site_linked") and user.get("site_username"):
        return (
            "✅ <b>Rahmat! Obuna tasdiqlandi.</b>\n\n"
            f"🌐 Sayt: <b>{escape(str(user['site_username']))}</b>\n"
            f"💎 SP: <b>{user['skills']}</b>\n"
            f"⚡ XP: <b>{user['xp']}</b>  |  🏆 Level: <b>{user['level']}</b>\n"
            f"🪙 Tanga: <b>{user['coins']}</b>\n\n"
            "Quyidagi menyudan tanlang 👇"
        )
    return (
        "✅ <b>Rahmat! Obuna tasdiqlandi.</b>\n\n"
        "🎮 <b>Web Appni oching:</b>\n"
        "1. Quyidagi <b>Web App</b> tugmasini bosing\n"
        "2. Hisob avtomatik ulanadi — kod kerak emas\n"
        "3. Eski usul: saytda kod olib, <code>/ulash 123456</code> yuboring\n\n"
        "Quyidagi menyudan tanlang 👇"
    )

NOT_SUBSCRIBED = (
    "❌ <b>Siz hali obuna bo'lmagansiz.</b>\n\n"
    "Botdan foydalanish uchun avval kanal va guruhga obuna bo'ling, "
    "so'ng <b>Tekshirish</b> tugmasini bosing."
)

HELP_ADMIN = (
    "👑 <b>Admin buyruqlari</b>\n\n"
    "/freeskill &lt;miqdor&gt; — kanalda Free SP e'loni\n"
    "/items &lt;nomi&gt;, &lt;narx&gt;, &lt;rarity&gt;, &lt;soni&gt;, &lt;sp&gt; — item yaratish\n"
    "   masalan: <code>/items Ninza qilish, 1200, epic, 10, 2</code>\n"
    "/broadcast &lt;xabar&gt; — hammaga xabar\n"
    "/give &lt;tg_id&gt; &lt;tanga&gt; &lt;sp&gt; — foydalanuvchiga berish\n"
    "/stats — statistika"
)

HELP_USER = (
    "ℹ️ <b>Buyruqlar</b>\n\n"
    "/start — boshlash\n"
    "/profile — profil\n"
    "/skills — SP larim\n"
    "/balance — tangam\n"
    "/shop — do'kon\n"
    "/star — Stars orqali tanga olish\n"
    "/ulash &lt;kod&gt; — sayt hisobini ulash\n"
    "/daily — kunlik bonus"
)


def profile_text(user: dict) -> str:
    linked = "✅ " + escape(str(user["site_username"])) if user.get("site_linked") else "❌ ulanmagan"
    return (
        "👤 <b>Profil</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: <code>{user['tg_id']}</code>\n"
        f"💎 SP: <b>{user['skills']}</b>\n"
        f"⚡ XP: <b>{user['xp']}</b>  |  🏆 Level: <b>{user['level']}</b>\n"
        f"🪙 Tanga: <b>{user['coins']}</b>\n"
        f"🔗 Sayt hisobi: {linked}\n"
        f"🔥 Kunlik seriya: <b>{user['streak']}</b>\n"
        "━━━━━━━━━━━━━━━━━━"
    )


def skills_text(user: dict) -> str:
    xp = user["skills"] * XP_PER_SKILL
    return (
        "💎 <b>SP laringiz</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"SP: <b>{user['skills']}</b>\n"
        f"⚡ XP: <b>{user['xp']}</b>  |  🏆 Level: <b>{user['level']}</b>\n"
        f"Taxminiy XP: <b>{xp}</b> ({XP_PER_SKILL} XP / SP)\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Saytda <b>SP ko'tarish</b> tugmasi 1 SP ni 20 XP ga aylantiradi."
    )


def balance_text(user: dict) -> str:
    return (
        "🪙 <b>Tanga balansingiz</b>\n\n"
        f"Balans: <b>{user['coins']}</b> tanga\n"
        f"💎 Stars kursi: <b>1 Star = {STARS_TO_COINS} tanga</b>\n\n"
        "Tanga olish uchun /star buyrug'ini yuboring."
    )


# ---------------- Free Skill kartasi ----------------
def freeskill_card(amount: int) -> str:
    return (
        "🎁 <b>FREE SP!</b> 🎁\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🎉 <b>Admin sovg'asi!</b>\n"
        f"💎 Miqdor: <b>+{amount} SP</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "⏳ Har bir o'yinchi bir marta oladi!\n"
        "👇 SP ni olish uchun tugmani bosing"
    )


def freeskill_announce(amount: int) -> str:
    return (
        "🎁 <b>YANGI FREE SP!</b>\n\n"
        f"Admin <b>+{amount} SP</b> sovg'a qildi!\n"
        "Olish uchun kanalga o'ting va tugmani bosing 👇"
    )


# ---------------- Item kartasi ----------------
def item_card(item: dict) -> str:
    emoji = rarity_emoji(item["rarity"])
    name = escape(str(item["name"]))
    rarity = escape(str(item["rarity"]))
    stock = item["stock"]
    stock_line = f"📊 Qoldi: <b>{stock} ta</b>" if stock > 0 else "🚫 <b>Tugadi!</b>"
    return (
        f"{emoji} <b>{rarity.upper()}</b> ITEM\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>{name}</b>\n"
        f"💠 Rarity: <b>{rarity}</b>\n"
        f"💰 Narx: <b>{item['price']} tanga</b>\n"
        f"💎 Beradi: <b>+{item['skill_value']} SP</b>\n"
        f"{stock_line}\n"
        "━━━━━━━━━━━━━━━━━━"
    )


def item_announce(item: dict) -> str:
    emoji = rarity_emoji(item["rarity"])
    name = escape(str(item["name"]))
    rarity = escape(str(item["rarity"]))
    return (
        f"{emoji} <b>YANGI ITEM!</b>\n\n"
        f"📦 <b>{name}</b>\n"
        f"💠 Rarity: <b>{rarity}</b>\n"
        f"💰 Narx: <b>{item['price']} tanga</b>\n"
        f"💎 Beradi: <b>+{item['skill_value']} SP</b>\n\n"
        "Guruhdagi xabardan sotib oling 👇"
    )


# ---------------- Xarid ----------------
def buy_success(item: dict, gained: int, stock: int) -> str:
    emoji = rarity_emoji(item["rarity"])
    name = escape(str(item["name"]))
    tail = f"📊 Qoldi: <b>{stock} ta</b>" if stock > 0 else "🚫 <b>Oxirgi dona sizga tegdi!</b>"
    return (
        "✅ <b>Xarid muvaffaqiyatli!</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"{emoji} {name}\n"
        f"💎 +{gained} SP qo'shildi!\n"
        f"{tail}\n"
        "━━━━━━━━━━━━━━━━━━"
    )
