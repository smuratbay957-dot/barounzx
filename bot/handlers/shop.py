# ============================================================
#  Do'kon: ro'yxat, sotib olish
# ============================================================
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import database as db
import keyboards as kb
import texts
from utils import is_subscribed

router = Router()


def _shop_text_and_kb():
    items = db.list_items()
    if not items:
        return "🛒 Hozircha itemlar yo'q. Admin tez orada qo'shadi.", kb.back_menu_kb()
    lines = ["🛒 <b>Do'kon</b>", "━━━━━━━━━━━━━━━━━━"]
    rows = []
    for it in items:
        emoji = texts.rarity_emoji(it["rarity"])
        lines.append(f"{emoji} <b>{it['name']}</b> — {it['price']} 🪙 | +{it['skill_value']} SP | {it['stock']} ta")
        rows.append([InlineKeyboardButton(
            text=f"🛒 {it['name']} ({it['price']}🪙)",
            callback_data=f"buy:{it['id']}",
        )])
    rows.append([InlineKeyboardButton(text="⬅️ Menyu", callback_data="menu:home")])
    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("shop"))
async def cmd_shop(message: Message):
    db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    text, markup = _shop_text_and_kb()
    await message.answer(text, reply_markup=markup)


@router.callback_query(F.data == "menu:shop")
async def cb_shop(cq: CallbackQuery):
    await cq.answer()
    text, markup = _shop_text_and_kb()
    try:
        await cq.message.edit_text(text, reply_markup=markup)
    except Exception:
        await cq.message.answer(text, reply_markup=markup)


@router.callback_query(F.data.startswith("buy:"))
async def cb_buy(cq: CallbackQuery):
    item_id = int(cq.data.split(":")[1])
    uid = cq.from_user.id
    db.get_or_create_user(uid, cq.from_user.username, cq.from_user.first_name)

    if not await is_subscribed(cq.bot, uid):
        await cq.answer("❗ Avval kanal va guruhga obuna bo'ling!", show_alert=True)
        return

    item = db.get_item(item_id)
    if not item or not item["active"]:
        await cq.answer("❌ Bu item mavjud emas.", show_alert=True)
        return
    if item["stock"] <= 0:
        await cq.answer("🚫 Item tugadi.", show_alert=True)
        return

    res = db.buy_item(uid, item_id, 1)
    if res is None:
        await cq.answer("🚫 Item tugadi.", show_alert=True)
        return
    if isinstance(res, dict) and res.get("error") == "no_money":
        await cq.answer(
            f"🪙 Tanga yetarli emas!\nKerak: {res['need']}, sizda: {res['have']}",
            show_alert=True,
        )
        return

    await cq.answer(f"✅ +{res['gained']} SP!", show_alert=False)

    fresh = db.get_item(item_id)
    try:
        await cq.message.edit_text(texts.item_card(fresh), reply_markup=kb.item_kb(item_id, fresh["stock"]))
    except Exception:
        pass

    try:
        await cq.bot.send_message(uid, texts.buy_success(fresh, res["gained"], res["stock"]))
    except Exception:
        pass
