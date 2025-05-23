from dataclasses import dataclass
from environs import Env


@dataclass
class TgBot:
    token: str


@dataclass
class RedisConfig:
    redis_host: str
    redis_port: int
    redis_db: int
    redis_password: str


@dataclass
class Config:
    tg_bot: TgBot
    redis: RedisConfig


def load_config(path: str | None = None, bot_number=1) -> Config:
    env = Env()
    env.read_env(path)
    return Config(
        tg_bot=TgBot(
            token=env(f"BOT_TOKEN{bot_number}"),
        ),
        redis=RedisConfig(
            redis_host=env("REDIS_HOST", "redis"),
            redis_port=env.int("REDIS_PORT", 6379),
            redis_db=env.int("REDIS_DB", 1),
            redis_password=env("REDIS_PASSWORD", ""),
        ),
    )
