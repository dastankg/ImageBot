from datetime import datetime

from asgiref.sync import sync_to_async

from shop.models import Telephone, Report
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)


async def send_monthly_notification(bot):

    message = f"🔔 Сегодня первое число месяца\nВы получили оплату за прошлый месяц?"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да", callback_data="payment_yes")],
            [InlineKeyboardButton(text="❌ Нет", callback_data="payment_no")],
        ]
    )

    owner_telephones = await sync_to_async(
        lambda: list(Telephone.objects.filter(is_owner=True))
    )()

    for telephone in owner_telephones:
        try:
            if telephone.chat_id:
                await bot.send_message(
                    chat_id=telephone.chat_id, text=message, reply_markup=keyboard
                )
                logger.info(f"Опрос отправлен {telephone.number}")
        except Exception as e:
            logger.error(f"Ошибка при отправке опроса {telephone.number}: {e}")


def setup_scheduler(bot):
    scheduler = AsyncIOScheduler(timezone=pytz.timezone("Asia/Bishkek"))

    scheduler.add_job(
        send_monthly_notification,
        CronTrigger(day="25", hour="20", minute="45"),
        kwargs={"bot": bot},
    )

    logger.info("Планировщик настроен для отправки ежемесячных уведомлений")
    return scheduler
