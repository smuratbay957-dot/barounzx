# ============================================================
#  Barounzx Telegram bot - kirish nuqtasi
#  Ishga tushirish:  python main.py
# ============================================================
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import database as db
from config import BOT_TOKEN
from handlers import account, admin, common, freeskill, shop, stars


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    db.init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # Router tartibi muhim: admin/freeskill avval, umumiy keyin
    dp.include_router(admin.router)
    dp.include_router(freeskill.router)
    dp.include_router(stars.router)
    dp.include_router(shop.router)
    dp.include_router(account.router)
    dp.include_router(common.router)

    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Barounzx bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi.")
