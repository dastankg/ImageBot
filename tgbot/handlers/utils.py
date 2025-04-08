import logging
import os
from typing import Optional

import aiofiles
import aiohttp
from asgiref.sync import sync_to_async
from django.conf import settings

from post.models import Post
from shop.models import Shop
from tguser.models import TgUser
from shop.models import Telephone
logger = logging.getLogger(__name__)


@sync_to_async
def get_shop_by_phone(phone_number: str) -> Optional[Shop]:
    try:
        phone_number = str(phone_number).replace("+", "").strip()
        telephone = Telephone.objects.select_related('shop').get(number=phone_number)
        return telephone.shop
    except Telephone.DoesNotExist:
        logger.warning(f"Shop not found for phone: {phone_number}")
        return None
    except Exception as e:
        logger.error(f"Error getting shop by phone: {e}")
        return None



@sync_to_async
def save_user_profile(telegram_id: int, phone_number: str) -> TgUser:
    try:
        phone_number = str(phone_number).replace("+", "").strip()

        user_profile, created = TgUser.objects.get_or_create(
            telegram_id=telegram_id, defaults={"phone_number": phone_number}
        )
        if not created and user_profile.phone_number != phone_number:
            user_profile.phone_number = phone_number
            user_profile.save(update_fields=["phone_number"])

        return user_profile
    except Exception as e:
        logger.error(f"Error saving user profile: {e}")
        raise


@sync_to_async
def get_user_profile(telegram_id: int) -> Optional[TgUser]:
    try:
        return TgUser.objects.get(telegram_id=telegram_id)
    except TgUser.DoesNotExist:
        return None
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return None


@sync_to_async
def save_photo_to_post(shop_id: int, relative_path: str) -> Post:
    try:
        return Post.objects.create(shop_id=shop_id, image=relative_path)
    except Exception as e:
        logger.error(f"Error saving photo to post: {e}")
        raise


async def download_photo(file_url: str, filename: str) -> str:
    save_path = os.path.join(settings.MEDIA_ROOT, "photos")
    os.makedirs(save_path, exist_ok=True)
    file_path = os.path.join(save_path, filename)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as resp:
                if resp.status != 200:
                    raise ValueError(f"Failed to download file: HTTP {resp.status}")

                async with aiofiles.open(file_path, "wb") as f:
                    await f.write(await resp.read())

        logger.info(f"Photo saved: {file_path}")
        return f"photos/{filename}"
    except Exception as e:
        logger.error(f"Error downloading photo: {e}")
        raise
