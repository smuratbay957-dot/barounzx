# ============================================================
#  Sayt hisobini ulash: sayt kod beradi -> /ulash <kod>
# ============================================================
from html import escape

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

import database as db
import keyboards as kb
import texts
from utils import is_subscribed

router = Router()

LINK_HELP = (
    "🔗 <b>Sayt hisobini ulash</b>\n\n"
    "1. Saytga kiring\n"
    "2. <b>Sozlamalar → Telegram ulash</b> ni bosing\n"
    "3. Chiqqan 6 xonali kodni <code>/ulash 123456</code> ko'rinishida yuboring"
)


@router.message(Command("ulash", "link"))
async def cmd_link(message: Message):
    db.get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.first_name
    )
    if not await is_subscribed(message.bot, message.from_user.id):
        await message.answer(texts.START_NEW, reply_markup=kb.subscribe_kb())
        return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer(LINK_HELP)
        return

    code = "".join(ch for ch in parts[1] if ch.isdigit())
    if len(code) != 6:
        await message.answer("❌ Kod 6 xonali bo'lishi kerak.\n\n" + LINK_HELP)
        return

    res = db.link_by_code(code, message.from_user.id)
    if not res:
        await message.answer(
            "❌ Kod noto'g'ri yoki muddati tugagan.\n"
            "Saytda <b>Sozlamalar → Telegram ulash</b> orqali yangi kod oling."
        )
        return

    user = db.get_user(message.from_user.id)
    await message.answer(
        "✅ <b>Telegram ulandi!</b>\n\n"
        f"🌐 Sayt: <b>{escape(str(res['site_username']))}</b>\n"
        f"💎 SP: <b>{user['skills']}</b>\n"
        f"⚡ XP: <b>{user['xp']}</b>  |  🏆 Level: <b>{user['level']}</b>\n\n"
        "Endi /start da sayt statistikasi ko'rinadi.",
        reply_markup=kb.main_menu_kb(),
    )


@router.message(Command("login"))
async def cmd_login(message: Message):
    await message.answer(LINK_HELP)


@router.message(Command("uzish", "unlink"))
async def cmd_unlink(message: Message):
    db.get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.first_name
    )
    db.unlink_user(message.from_user.id)
    await message.answer("🔓 Sayt hisobi uzildi. Qayta ulash uchun saytda yangi kod oling.")
