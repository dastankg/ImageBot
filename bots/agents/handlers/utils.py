from datetime import datetime, timedelta
import os
import re
from typing import Any
import json
import logging
from asgiref.sync import sync_to_async
import redis.asyncio as redis_async
from bots.agents.tgConfig.tgConfig import load_config
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import types
import subprocess
import aiohttp
from post.models import PostAgent
from shop.models import Agent
from django.core.files.base import File
import piexif
from PIL import Image

config = load_config()

redis_client = redis_async.Redis(
    host=config.redis.redis_host,
    port=config.redis.redis_port,
    db=config.redis.redis_db,
    password=config.redis.redis_password,
)


logger = logging.getLogger(__name__)

async def get_user_profile(telegram_id: int) -> dict[str, Any] | None:
    key = f"user:{telegram_id}"
    data = await redis_client.get(key)
    return json.loads(data) if data else None

async def get_agent_by_phone(phone_number: str):
    try:
        if not phone_number.startswith("+"):
            phone_number = f"+{phone_number}"

        agent = await sync_to_async(
            lambda: Agent.objects.filter(agent_number=phone_number).first()
        )()
        return agent
    except Exception as e:
        logger.error(f"Error in get_agent_by_phone: {e}")
        return None

async def save_user_profile(telegram_id: int, phone_number: str) -> bool:
    try:
        key = f"user:{telegram_id}"
        user_data = {"phone_number": phone_number}
        await redis_client.set(key, json.dumps(user_data))
        return True
    except Exception as e:
        logger.error(f"Error saving user profile to Redis: {e}")
        return False


async def schedule(message: Message):
    user = await get_user_profile(message.from_user.id)
    phone_number = user["phone_number"]
    if not phone_number.startswith("+"):
            phone_number = f"+{phone_number}"

    agent_phone = phone_number

    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    current_day = weekdays[datetime.now().weekday()]

    agent = await sync_to_async(
        lambda: Agent.objects.filter(agent_number=agent_phone).first()
    )()
    if not agent:
        await message.answer(f"Не удалось найти агента по номеру телефона: {agent_phone}")
        return


    stores_attr = f"{current_day}_stores"
    stores = await sync_to_async(
        lambda: list(getattr(agent, stores_attr).all())
    )()

    if not stores:
        await message.answer(f"На сегодня ({current_day.capitalize()}) у вас нет назначенных магазинов.")
        return

    builder = ReplyKeyboardBuilder()

    for store in stores:
        builder.add(types.KeyboardButton(text=store.name))

    builder.adjust(2)

    await message.answer(
        f"Ваши магазины на сегодня ({current_day.capitalize()}):\n\nВыберите магазин:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

async def download_photo(file_url: str, filename: str):
    try:
        os.makedirs("media/posts", exist_ok=True)

        save_path = f"media/posts/{filename}"
        relative_path = f"posts/{filename}"

        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to download file: {response.status}")

                with open(save_path, "wb") as f:
                    f.write(await response.read())
        file_extension = os.path.splitext(filename.lower())[1]
        image_extensions = [".jpg", ".jpeg", ".png", ".heic", ".tiff", ".bmp"]
        if any(file_extension == ext for ext in image_extensions):
            is_valid = await check_photo_creation_time(save_path)
            if not is_valid:
                if os.path.exists(save_path):
                    os.remove(save_path)
                raise Exception(
                    "Фото не содержит необходимые метаданные или было сделано более 3 минут назад."
                )

        return relative_path
    except Exception as e:
        logger.error(f"Error in download_photo: {e}")
        raise


async def save_photo_to_post(
    agent_id, shop_name, relative_path, latitude=None, longitude=None
):
    try:
        agent = await sync_to_async(lambda: Agent.objects.get(id=agent_id))()

        post = PostAgent(
            agent=agent, shop=shop_name, latitude=latitude, longitude=longitude
        )
        await sync_to_async(post.save)()

        file_path = f"media/{relative_path}"
        file_name = os.path.basename(file_path)

        file_extension = os.path.splitext(file_name.lower())[1]
        image_extensions = [".jpg", ".jpeg", ".png", ".heic", ".tiff", ".bmp"]
        with open(file_path, "rb") as f:
            file_content = File(f)
            if any(file_extension == ext for ext in image_extensions):
                await sync_to_async(
                    lambda: post.image.save(file_name, file_content, save=True)
                )()
            else:
                await sync_to_async(
                    lambda: post.document.save(file_name, file_content, save=True)
                )()

        if os.path.exists(file_path):
            os.remove(file_path)

        if latitude and longitude and not post.address:
            try:
                address = await get_address_from_coordinates(latitude, longitude)
                if address:
                    post.address = address
                    await sync_to_async(post.save)()
            except Exception as e:
                logger.error(f"Error getting address from coordinates: {e}")

        return post.id
    except Exception as e:
        logger.error(f"Error in save_photo_to_post: {e}")
        raise


async def get_address_from_coordinates(latitude, longitude):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={
                    "lat": latitude,
                    "lon": longitude,
                    "format": "json",
                },
                headers={"User-Agent": "DjangoApp"},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("display_name")
        return None
    except Exception as e:
        logger.error(f"Error in get_address_from_coordinates: {e}")
        return None


async def get_shop_by_phone(phone_number: str):
    logger.warning("get_shop_by_phone is deprecated, use get_agent_by_phone instead")
    return await get_agent_by_phone(phone_number)


async def check_photo_creation_time(file_path):
    try:
        file_extension = os.path.splitext(file_path.lower())[1]

        if file_extension == ".heic":
            metadata = get_heic_metadata(file_path)
            if not metadata:
                logger.warning(f"Метаданные отсутствуют в HEIC файле: {file_path}")
                return False

            date_time_str = None
            for field in ["DateTimeOriginal", "CreateDate"]:
                if field in metadata and metadata[field]:
                    date_time_str = metadata[field]
                    break

            if not date_time_str:
                logger.warning(
                    f"Данные о времени создания отсутствуют в HEIC: {file_path}"
                )
                return False

            match = re.match(
                r"(\d{4}):(\d{2}):(\d{2}) (\d{2}):(\d{2}):(\d{2})", date_time_str
            )
            if not match:
                logger.warning(f"Неизвестный формат даты в HEIC: {date_time_str}")
                return False

            year, month, day, hour, minute, second = map(int, match.groups())
            photo_time = datetime(year, month, day, hour, minute, second)

            current_time = datetime.now()
            time_diff = current_time - photo_time

            return time_diff <= timedelta(minutes=3)

        else:
            try:
                img = Image.open(file_path)

                if not hasattr(img, "_getexif") or not img._getexif():
                    logger.warning(
                        f"EXIF данные отсутствуют в изображении: {file_path}"
                    )
                    return False

                exif_dict = piexif.load(img.info["exif"])

                if "0th" in exif_dict and piexif.ImageIFD.DateTime in exif_dict["0th"]:
                    date_time_str = exif_dict["0th"][piexif.ImageIFD.DateTime].decode(
                        "utf-8"
                    )
                    photo_time = datetime.strptime(date_time_str, "%Y:%m:%d %H:%M:%S")

                    current_time = datetime.now()
                    time_diff = current_time - photo_time

                    return time_diff <= timedelta(minutes=3)
                else:
                    logger.warning(
                        f"Данные о времени создания отсутствуют в EXIF: {file_path}"
                    )
                    return False

            except Exception as e:
                logger.warning(f"Ошибка при чтении EXIF данных: {e}")
                return False

    except Exception as e:
        logger.error(f"Ошибка при проверке времени создания файла: {e}")
        return False


async def get_heic_metadata(file_path):
    try:
        try:
            subprocess.run(["exiftool", "-ver"], capture_output=True, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error(
                "ExifTool не установлен. Установите с помощью 'sudo dnf install perl-Image-ExifTool'"
            )
            return None

        result = subprocess.run(
            ["exiftool", "-json", "-DateTimeOriginal", "-CreateDate", file_path],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logger.error(f"Ошибка при выполнении exiftool: {result.stderr}")
            return None

        metadata = json.loads(result.stdout)
        if not metadata or len(metadata) == 0:
            return None

        return metadata[0]
    except Exception as e:
        logger.error(f"Ошибка при чтении метаданных HEIC: {e}")
        return None