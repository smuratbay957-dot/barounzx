# ============================================================
#  Free Skill tugmasi (kanal/guruh/private)
# ============================================================
from aiogram import F, Router
from aiogram.types import CallbackQuery

import database as db
from utils import is_subscribed

router = Router()


@router.callback_query(F.data.startswith("fs:"))
async def cb_claim_freeskill(cq: CallbackQuery):
    fs_id = int(cq.data.split(":")[1])
    uid = cq.from_user.id
    db.get_or_create_user(uid, cq.from_user.username, cq.from_user.first_name)

    if not await is_subscribed(cq.bot, uid):
        await cq.answer("❗ Avval kanal va guruhga obuna bo'ling!", show_alert=True)
        return

    fs = db.get_freeskill(fs_id)
    if not fs or not fs["active"]:
        await cq.answer("⌛ Bu e'lon tugagan.", show_alert=True)
        return

    ok = db.claim_freeskill(fs_id, uid, fs["amount"])
    if not ok:
        await cq.answer("Siz bu skillni allaqachon oldingiz! 🎁", show_alert=True)
        return

    await cq.answer(f"🎉 +{fs['amount']} skill qo'shildi!", show_alert=True)
    user = db.get_user(uid)
    try:
        await cq.bot.send_message(
            uid,
            f"🎁 <b>Free Skill olindi!</b>\n\n"
            f"💎 +{fs['amount']} skill\n"
            f"💎 Jami: <b>{user['skills']}</b> skill",
        )
    except Exception:
        pass
