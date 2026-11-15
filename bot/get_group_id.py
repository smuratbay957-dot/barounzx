# ============================================================
#  Private guruh/kanalning raqamli chat_id sini aniqlash
#  Ishlatish:
#    1) Botni to'xtating (Ctrl+C)
#    2) Botni private guruhga qo'shing / guruhda xabar yozing
#    3) python3 get_group_id.py
# ============================================================
import asyncio

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession

from config import BOT_TOKEN, PROXY_URL


def _make_bot() -> Bot:
    if PROXY_URL:
        return Bot(token=BOT_TOKEN, session=AiohttpSession(proxy=PROXY_URL))
    return Bot(token=BOT_TOKEN)


async def main():
    bot = _make_bot()
    print("Guruhga botni qo'shing yoki guruhda xabar yozing (30 soniya kutilmoqda)...")
    seen = {}
    offset = None
    try:
        for _ in range(6):
            updates = await bot.get_updates(offset=offset, timeout=5)
            for u in updates:
                offset = u.update_id + 1
                obj = u.message or u.channel_post or u.edited_message or u.my_chat_member
                chat = getattr(obj, "chat", None)
                if chat is not None:
                    seen[chat.id] = f"{chat.type} | {chat.title or chat.username or ''}"
            if seen:
                break
    finally:
        await bot.session.close()

    if not seen:
        print("Hech narsa topilmadi. Botni to'xtatganingizga ishonch hosil qiling va qayta urinib ko'ring.")
        return

    print("\nTopilgan chatlar:")
    for chat_id, info in seen.items():
        print(f"  {chat_id}  ->  {info}")
    print("\nPrivate guruh uchun '-100...' bilan boshlanadigan id ni .env dagi GROUP_USERNAME ga yozing.")


if __name__ == "__main__":
    asyncio.run(main())
