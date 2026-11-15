# ============================================================
#  Telegram Stars orqali tanga olish (1 Star = STARS_TO_COINS tanga)
# ============================================================
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

import database as db
import keyboards as kb
from config import STARS_TO_COINS

router = Router()


@router.message(Command("star"))
async def cmd_star(message: Message):
    db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer(
        "⭐ <b>Stars orqali tanga olish</b>\n\n"
        f"Kurs: <b>1 Star = {STARS_TO_COINS} tanga</b>\n"
        "Paketni tanlang 👇",
        reply_markup=kb.stars_kb(),
    )


@router.callback_query(F.data == "menu:stars")
async def cb_stars_menu(cq: CallbackQuery):
    await cq.answer()
    text = (
        "⭐ <b>Stars orqali tanga olish</b>\n\n"
        f"Kurs: <b>1 Star = {STARS_TO_COINS} tanga</b>\n"
        "Paketni tanlang 👇"
    )
    try:
        await cq.message.edit_text(text, reply_markup=kb.stars_kb())
    except Exception:
        await cq.message.answer(text, reply_markup=kb.stars_kb())


@router.callback_query(F.data.startswith("stars:"))
async def cb_buy_stars(cq: CallbackQuery):
    stars = int(cq.data.split(":")[1])
    coins = stars * STARS_TO_COINS
    await cq.answer()
    await cq.bot.send_invoice(
        chat_id=cq.from_user.id,
        title=f"{stars} Stars",
        description=f"{coins} tanga sotib olish",
        payload=f"coins:{stars}",
        currency="XTR",
        prices=[LabeledPrice(label="Stars", amount=stars)],
    )


@router.pre_checkout_query()
async def on_pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def on_paid(message: Message):
    payment = message.successful_payment
    stars = payment.total_amount
    coins = stars * STARS_TO_COINS
    uid = message.from_user.id
    db.get_or_create_user(uid, message.from_user.username, message.from_user.first_name)
    db.add_coins(uid, coins)
    db.add_payment(uid, stars, coins, payment.invoice_payload)
    user = db.get_user(uid)
    await message.answer(
        "✅ <b>To'lov muvaffaqiyatli!</b>\n\n"
        f"⭐ {stars} Stars → 🪙 +{coins} tanga\n"
        f"🪙 Jami: <b>{user['coins']}</b> tanga"
    )
