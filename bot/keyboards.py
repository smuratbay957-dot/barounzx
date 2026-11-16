# ============================================================
#  Barounzx bot - klaviaturalar
# ============================================================
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import CHANNEL_URL, GROUP_URL, SITE_URL


def subscribe_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 Kanal", url=CHANNEL_URL),
            InlineKeyboardButton(text="💬 Guruh", url=GROUP_URL),
        ],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data="sub:check")],
    ])


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛒 Do'kon", callback_data="menu:shop"),
            InlineKeyboardButton(text="👤 Profil", callback_data="menu:profile"),
        ],
        [
            InlineKeyboardButton(text="💎 SP larim", callback_data="menu:skills"),
            InlineKeyboardButton(text="🪙 Tangam", callback_data="menu:balance"),
        ],
        [
            InlineKeyboardButton(text="⭐ Stars orqali tanga", callback_data="menu:stars"),
            InlineKeyboardButton(text="🌐 Saytni ochish", url=SITE_URL),
        ],
    ])


def freeskill_kb(fs_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 SP ni olish", callback_data=f"fs:{fs_id}")],
    ])


def item_kb(item_id: int, stock: int) -> InlineKeyboardMarkup:
    if stock <= 0:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚫 Tugadi", callback_data=f"buy:{item_id}")],
        ])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Sotib olish", callback_data=f"buy:{item_id}")],
    ])


def stars_kb() -> InlineKeyboardMarkup:
    # 1 Star = 10 tanga -> paketlar
    packages = [(10, 100), (25, 250), (50, 500), (100, 1000)]
    rows = []
    pair = []
    for stars, coins in packages:
        pair.append(InlineKeyboardButton(
            text=f"⭐ {stars} → {coins} tanga", callback_data=f"stars:{stars}"))
        if len(pair) == 2:
            rows.append(pair)
            pair = []
    if pair:
        rows.append(pair)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Menyu", callback_data="menu:home")],
    ])


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="login:cancel")],
    ])
