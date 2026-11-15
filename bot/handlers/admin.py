# ============================================================
#  Admin handlerlari: /freeskill, /items, /broadcast, /give, /stats
# ============================================================
import asyncio

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

import database as db
import keyboards as kb
import texts
from config import CHANNEL_USERNAME, GROUP_USERNAME
from utils import is_admin

router = Router()


async def _broadcast(bot, text, markup=None):
    sent = 0
    for user in db.all_users():
        try:
            await bot.send_message(user["tg_id"], text, reply_markup=markup)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            continue
    return sent


# ---------------- /freeskill ----------------
async def _do_freeskill(message: Message, arg: str):
    arg = (arg or "").strip()
    if not arg.isdigit() or int(arg) <= 0:
        await message.answer("Foydalanish: <code>/freeskill 5</code>")
        return
    amount = int(arg)
    fs_id = db.create_freeskill(amount)

    try:
        sent = await message.bot.send_message(
            CHANNEL_USERNAME, texts.freeskill_card(amount), reply_markup=kb.freeskill_kb(fs_id)
        )
        db.set_freeskill_message(fs_id, sent.message_id)
    except Exception as exc:  # noqa: BLE001
        await message.answer(
            f"❌ Kanalga yuborilmadi. Bot kanalda admin bo'lishi kerak.\n<code>{exc}</code>"
        )
        return

    try:
        await message.bot.send_message(
            GROUP_USERNAME, texts.freeskill_announce(amount), reply_markup=kb.freeskill_kb(fs_id)
        )
    except Exception:
        pass

    count = await _broadcast(message.bot, texts.freeskill_announce(amount), kb.freeskill_kb(fs_id))
    await message.answer(f"✅ Free Skill e'lon qilindi: +{amount} skill\n👥 {count} foydalanuvchiga xabar.")


@router.message(Command("freeskill"))
async def cmd_freeskill(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    await _do_freeskill(message, parts[1] if len(parts) > 1 else "")


@router.channel_post(Command("freeskill"))
async def channel_freeskill(message: Message):
    # Kanalga faqat adminlar yoza oladi
    parts = message.text.split(maxsplit=1)
    await _do_freeskill(message, parts[1] if len(parts) > 1 else "")


# ---------------- /items ----------------
async def _do_items(message: Message, arg: str):
    arg = (arg or "").strip()
    parts = [p.strip() for p in arg.split(",")]
    if len(parts) != 5:
        await message.answer(
            "Foydalanish: <code>/items &lt;nomi&gt;, &lt;narx&gt;, &lt;rarity&gt;, &lt;soni&gt;, &lt;skill&gt;</code>\n"
            "Masalan: <code>/items Ninza qilish, 1200, epic, 10, 2</code>"
        )
        return
    name, price_s, rarity, stock_s, skill_s = parts
    try:
        price, stock, skill_value = int(price_s), int(stock_s), int(skill_s)
    except ValueError:
        await message.answer("❌ narx, soni va skill butun son bo'lishi kerak.")
        return
    if price < 0 or stock < 0 or skill_value < 0 or not name:
        await message.answer("❌ Qiymatlar noto'g'ri.")
        return

    item_id = db.create_item(name, price, rarity, stock, skill_value)
    item = db.get_item(item_id)

    try:
        sent = await message.bot.send_message(
            GROUP_USERNAME, texts.item_card(item), reply_markup=kb.item_kb(item_id, stock)
        )
        db.set_item_message(item_id, sent.message_id)
    except Exception as exc:  # noqa: BLE001
        await message.answer(
            f"❌ Guruhga yuborilmadi. Bot guruhda admin bo'lishi kerak.\n<code>{exc}</code>"
        )
        return

    await message.answer(f"✅ Item yaratildi: <b>{name}</b> (#{item_id}, {stock} ta).")


@router.message(Command("items"))
async def cmd_items(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    await _do_items(message, parts[1] if len(parts) > 1 else "")


@router.channel_post(Command("items"))
async def channel_items(message: Message):
    parts = message.text.split(maxsplit=1)
    await _do_items(message, parts[1] if len(parts) > 1 else "")


# ---------------- /broadcast ----------------
@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("Foydalanish: <code>/broadcast Xabar matni</code>")
        return
    count = await _broadcast(message.bot, parts[1].strip())
    await message.answer(f"✅ {count} foydalanuvchiga yuborildi.")


# ---------------- /give ----------------
@router.message(Command("give"))
async def cmd_give(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 4:
        await message.answer("Foydalanish: <code>/give &lt;tg_id&gt; &lt;tanga&gt; &lt;skill&gt;</code>")
        return
    try:
        target = int(parts[1])
        coins = int(parts[2])
        skills = int(parts[3])
    except ValueError:
        await message.answer("❌ Sonlar noto'g'ri.")
        return
    user = db.get_user(target)
    if not user:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return
    if coins:
        db.add_coins(target, coins)
    if skills:
        db.add_skills(target, skills)
    await message.answer(f"✅ {target} ga: +{coins} tanga, +{skills} skill.")
    try:
        await message.bot.send_message(target, f"🎁 Admin sizga: +{coins} tanga, +{skills} skill berdi!")
    except Exception:
        pass


# ---------------- /stats ----------------
@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    s = db.stats()
    await message.answer(
        "📊 <b>Statistika</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👥 Foydalanuvchilar: <b>{s['users']}</b>\n"
        f"📦 Faol itemlar: <b>{s['items']}</b>\n"
        f"🛒 Xaridlar: <b>{s['purchases']}</b>\n"
        f"⭐ Yulduzlar: <b>{s['stars']}</b>\n"
        "━━━━━━━━━━━━━━━━━━"
    )
