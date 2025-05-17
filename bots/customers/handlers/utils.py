from datetime import datetime, timedelta
import os
import re
from typing import Any
import json
import logging
from asgiref.sync import sync_to_async
import redis.asyncio as redis_async
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import types
import subprocess
import aiohttp
from post.models import PostAgent
from shop.models import Telephone
from django.core.files.base import File
import piexif
from PIL import Image
from bots.tgConfig.redis_connect import redis_client



logger = logging.getLogger(__name__)


async def get_user_profile(telegram_id: int) -> dict[str, Any] | None:
    key = f"user:{telegram_id}"
    data = await redis_client.get(key)
    return json.loads(data) if data else None


async def get_shop_by_phone(phone_number: str):
    try:
        if not phone_number.startswith("+"):
            phone_number = f"+{phone_number}"
        telephone = await sync_to_async(
            lambda: Telephone.objects.select_related("shop").get(number=phone_number)
        )()
        if telephone and hasattr(telephone, "shop"):
            shop = await sync_to_async(lambda: getattr(telephone, "shop", None))()
            return shop
        return None
    except Exception as e:
        logger.error(f"Error in get_shop_by_phone: {e}")
        return None