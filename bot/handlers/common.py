# ============================================================
#  Umumiy handlerlar: /start, obuna, profil, skill, balans, daily
# ============================================================
from datetime import date, timedelta

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

import database as db
import keyboards as kb
import texts
from config import ADMIN_ID, DAILY_COINS
from utils import is_admin, is_subscribed

router = Router()


def touch(message: Message):
    return db.get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )


@router.message(CommandStart())
async def cmd_start(message: Message):
    touch(message)
    if not await is_subscribed(message.bot, message.from_user.id):
        await message.answer(texts.START_NEW, reply_markup=kb.subscribe_kb())
        return
    await message.answer(texts.SUBSCRIBED, reply_markup=kb.main_menu_kb())


@router.callback_query(F.data == "sub:check")
async def cb_sub_check(cq: CallbackQuery):
    if not await is_subscribed(cq.bot, cq.from_user.id):
        await cq.answer(texts.NOT_SUBSCRIBED, show_alert=True)
        return
    await cq.answer("✅ Obuna tasdiqlandi!")
    try:
        await cq.message.edit_text(texts.SUBSCRIBED, reply_markup=kb.main_menu_kb())
    except Exception:
        await cq.message.answer(texts.SUBSCRIBED, reply_markup=kb.main_menu_kb())


@router.callback_query(F.data == "menu:home")
async def cb_home(cq: CallbackQuery):
    await cq.answer()
    try:
        await cq.message.edit_text("🏠 <b>Asosiy menyu</b>", reply_markup=kb.main_menu_kb())
    except Exception:
        await cq.message.answer("🏠 <b>Asosiy menyu</b>", reply_markup=kb.main_menu_kb())


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = texts.HELP_ADMIN if is_admin(message.from_user.id) else texts.HELP_USER
    await message.answer(text)


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    user = touch(message)
    await message.answer(texts.profile_text(user), reply_markup=kb.main_menu_kb())


@router.callback_query(F.data == "menu:profile")
async def cb_profile(cq: CallbackQuery):
    user = db.get_or_create_user(cq.from_user.id, cq.from_user.username, cq.from_user.first_name)
    await cq.answer()
    try:
        await cq.message.edit_text(texts.profile_text(user), reply_markup=kb.back_menu_kb())
    except Exception:
        await cq.message.answer(texts.profile_text(user), reply_markup=kb.back_menu_kb())


@router.message(Command("skills"))
async def cmd_skills(message: Message):
    user = touch(message)
    await message.answer(texts.skills_text(user))


@router.callback_query(F.data == "menu:skills")
async def cb_skills(cq: CallbackQuery):
    user = db.get_or_create_user(cq.from_user.id, cq.from_user.username, cq.from_user.first_name)
    await cq.answer()
    try:
        await cq.message.edit_text(texts.skills_text(user), reply_markup=kb.back_menu_kb())
    except Exception:
        await cq.message.answer(texts.skills_text(user), reply_markup=kb.back_menu_kb())


@router.message(Command("balance"))
async def cmd_balance(message: Message):
    user = touch(message)
    await message.answer(texts.balance_text(user))


@router.callback_query(F.data == "menu:balance")
async def cb_balance(cq: CallbackQuery):
    user = db.get_or_create_user(cq.from_user.id, cq.from_user.username, cq.from_user.first_name)
    await cq.answer()
    try:
        await cq.message.edit_text(texts.balance_text(user), reply_markup=kb.back_menu_kb())
    except Exception:
        await cq.message.answer(texts.balance_text(user), reply_markup=kb.back_menu_kb())


@router.message(Command("daily"))
async def cmd_daily(message: Message):
    user = touch(message)
    today = date.today().isoformat()
    if user["last_daily"] == today:
        await message.answer("⏳ Kunlik bonusni bugun allaqachon oldingiz. Ertaga qaytib keling!")
        return
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    streak = user["streak"] + 1 if user["last_daily"] == yesterday else 1
    reward = DAILY_COINS + streak * 5
    db.add_coins(user["tg_id"], reward)
    db.set_daily(user["tg_id"], today, streak)
    await message.answer(
        f"🎁 <b>Kunlik bonus!</b>\n\n"
        f"🪙 +{reward} tanga\n"
        f"🔥 Seriya: <b>{streak}</b> kun"
    )
