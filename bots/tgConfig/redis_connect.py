import redis.asyncio as redis_async
from bots.tgConfig.tgConfig import load_config


config = load_config(bot_number=2)

redis_client = redis_async.Redis(
    host=config.redis.redis_host,
    port=config.redis.redis_port,
    db=config.redis.redis_db,
    password=config.redis.redis_password,
)