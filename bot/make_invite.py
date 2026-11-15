# ============================================================
#  Private guruh uchun taklif havolasi (invite link) yaratish
#  Bot guruhda admin bo'lishi va "odam taklif qilish" huquqi bo'lishi shart.
#  Ishlatish:  python3 make_invite.py
# ============================================================
import asyncio

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession

from config import BOT_TOKEN, GROUP_USERNAME, PROXY_URL


def _bot() -> Bot:
    if PROXY_URL:
        return Bot(token=BOT_TOKEN, session=AiohttpSession(proxy=PROXY_URL))
    return Bot(token=BOT_TOKEN)


async def main():
    bot = _bot()
    print(f"Guruh: {GROUP_USERNAME!r}")
    try:
        link = await bot.create_chat_invite_link(chat_id=GROUP_USERNAME, name="barounzx")
        print("\nTaklif havolasi:")
        print(f"  {link.invite_link}")
        print("\nUni .env dagi GROUP_URL ga yozing:")
        print(f"  GROUP_URL={link.invite_link}")
    except Exception as exc:  # noqa: BLE001
        print(f"XATO: {exc}")
        print("Bot guruhda admin bo'lishi va 'Invite users' huquqi bo'lishi kerak.")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
