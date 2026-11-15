# ============================================================
#  Obuna tekshiruvini diagnostika qilish
#  Ishlatish:
#    python3 -u check_sub.py            # admin id bilan
#    python3 -u check_sub.py 123456789  # aniq user_id bilan
# ============================================================
import asyncio
import sys

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession

from config import ADMIN_ID, BOT_TOKEN, CHANNEL_USERNAME, GROUP_USERNAME, PROXY_URL

TIMEOUT = 30


def _bot() -> Bot:
    if PROXY_URL:
        return Bot(token=BOT_TOKEN, session=AiohttpSession(proxy=PROXY_URL))
    return Bot(token=BOT_TOKEN)


def _user_id() -> int:
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        return int(sys.argv[1])
    return ADMIN_ID


async def check(bot: Bot, label: str, chat, user_id: int):
    print(f"\n=== {label}: {chat!r} ===", flush=True)
    try:
        info = await asyncio.wait_for(bot.get_chat(chat), TIMEOUT)
        print(
            f"  chat: id={info.id} type={info.type} title={info.title!r} username={info.username!r}",
            flush=True,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"  get_chat XATO: {type(exc).__name__}: {exc}", flush=True)
    try:
        m = await asyncio.wait_for(bot.get_chat_member(chat_id=chat, user_id=user_id), TIMEOUT)
        print(f"  get_chat_member: status={m.status}", flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"  get_chat_member XATO: {type(exc).__name__}: {exc}", flush=True)


async def main():
    user_id = _user_id()
    print(f"PROXY_URL={PROXY_URL!r}", flush=True)
    print(f"KANAL={CHANNEL_USERNAME!r}  GURUH={GROUP_USERNAME!r}", flush=True)
    print(f"Tekshirilayotgan user_id: {user_id}", flush=True)
    bot = _bot()
    print("Bot obyekti yaratildi, get_me kutilmoqda...", flush=True)
    try:
        me = await asyncio.wait_for(bot.get_me(), TIMEOUT)
        print(f"Bot: @{me.username} (id={me.id})", flush=True)
        await check(bot, "KANAL", CHANNEL_USERNAME, user_id)
        await check(bot, "GURUH", GROUP_USERNAME, user_id)
    except Exception as exc:  # noqa: BLE001
        print(f"get_me XATO: {type(exc).__name__}: {exc}", flush=True)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
