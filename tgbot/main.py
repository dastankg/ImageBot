import asyncio
import os
import logging

from dotenv import load_dotenv
load_dotenv()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from tgbot.handlers.utils import config
from tgbot.handlers.user_handlers import router as user_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting bot")

    bot = Bot(
        token=config.tg_bot.token,  # ✅ Лучше использовать из config
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    dp.include_router(user_router)

    try:
        logger.info("Bot is starting")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Critical error: {e}")
    finally:
        logger.info("Bot stopped")
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
