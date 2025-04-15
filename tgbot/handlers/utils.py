import json
import logging
import os
from typing import Any, Dict, Optional
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import aiohttp
import redis.asyncio as redis_async
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile

from config import settings
from post.models import Post
from shop.models import Shop, Telephone
from tgbot.tgConfig.tgConfig import load_config

logger = logging.getLogger(__name__)

config = load_config()

redis_client = redis_async.Redis(
    host=config.redis.redis_host, port=config.redis.redis_port, db=config.redis.redis_db
)


async def get_user_profile(telegram_id: int) -> Optional[Dict[str, Any]]:
    key = f"user:{telegram_id}"
    data = await redis_client.get(key)
    return json.loads(data) if data else None


async def save_user_profile(telegram_id: int, phone_number: str) -> bool:
    try:
        key = f"user:{telegram_id}"
        user_data = {"phone_number": phone_number}
        await redis_client.set(key, json.dumps(user_data))
        return True
    except Exception as e:
        logger.error(f"Error saving user profile to Redis: {e}")
        return False


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


async def download_file(file_url: str, filename: str):
    try:
        posts_dir = os.path.join(settings.MEDIA_ROOT, "posts")
        os.makedirs(posts_dir, exist_ok=True)

        save_path = os.path.join(posts_dir, filename)
        relative_path = f"posts/{filename}"

        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to download file: {response.status}")

                with open(save_path, "wb") as f:
                    f.write(await response.read())

        return save_path, relative_path
    except Exception as e:
        logger.error(f"Error in download_file: {e}")
        raise


def extract_creation_time(file_path):
    try:
        with Image.open(file_path) as img:
            exif_data = img._getexif()
            if not exif_data:
                logger.warning(f"No EXIF data found in the image: {file_path}")
                return None

            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == "DateTimeOriginal":
                    try:
                        return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                    except ValueError:
                        logger.warning(f"Invalid date format in EXIF: {value}")
                        return None

            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == "DateTime":
                    try:
                        return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                    except ValueError:
                        logger.warning(f"Invalid date format in EXIF: {value}")
                        return None

            logger.warning(f"No creation time found in EXIF data: {file_path}")
            return None
    except Exception as e:
        logger.error(f"Error extracting creation time from image: {e}")
        return None


async def save_photo_to_post(shop_id, relative_path, full_path, latitude=None, longitude=None):
    try:
        creation_time = extract_creation_time(full_path)

        shop = await sync_to_async(lambda: Shop.objects.get(id=shop_id))()

        post = Post(
            shop=shop,
            latitude=latitude,
            longitude=longitude,
            creation_time=creation_time
        )

        return post.id
    except Exception as e:
        logger.error(f"Error in save_photo_to_post: {e}")
        raise