import logging
import os
import json
from typing import Optional, Dict, Any
import aiohttp
import redis.asyncio as redis_async
from asgiref.sync import sync_to_async
from django.core.files.base import File
from post.models import PostAgent
from shop.models import Agent
from bots.agent_bot.tgConfig.tgConfig import load_config

logger = logging.getLogger(__name__)

config = load_config()

redis_client = redis_async.Redis(
    host=config.redis.redis_host,
    port=config.redis.redis_port,
    db=config.redis.redis_db,
    password=config.redis.redis_password,
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
        with open(file_path, "rb") as f:
            await sync_to_async(
                lambda: post.image.save(file_name, File(f), save=True)
            )()

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
