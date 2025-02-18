import logging
import asyncio
from aiogram import Bot, Dispatcher
from bot.config import BOT_TOKEN
from bot.handlers import router

logging.basicConfig(level=logging.INFO)
logging.info("Bot is starting...")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(router)

async def main():
    logging.info("Bot started polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
