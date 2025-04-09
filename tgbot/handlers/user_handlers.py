import logging
import os
import uuid

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import ContentType, Message

from tgbot.handlers.utils import (
    download_photo,
    get_shop_by_phone,
    get_user_profile,
    save_photo_to_post,
    save_user_profile,
)
from tgbot.keyboard.keyboards import (
    get_contact_keyboard,
    get_location_keyboard,
    get_main_keyboard,
    get_photo_keyboard,
)

router = Router()
logger = logging.getLogger(__name__)

user_states = {}


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я бот для загрузки фотографий магазинов.\n\n"
        "Для начала работы, пожалуйста, поделитесь своим контактом, "
        "чтобы я мог проверить ваш номер телефона в системе.",
        reply_markup=get_contact_keyboard(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📋 <b>Инструкция по использованию бота:</b>\n\n"
        "1. Отправьте свой контакт для авторизации\n"
        "2. После успешной авторизации нажмите на кнопку «Загрузить фото»\n"
        "3. Отправьте геолокацию для привязки к фотографии\n"
        "4. Загрузите фотографию магазина\n\n"
        "Если у вас возникли проблемы, обратитесь к администратору."
    )


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    user = await get_user_profile(message.from_user.id)
    if not user:
        await message.answer(
            "Вы еще не авторизованы. Пожалуйста, поделитесь своим контактом для авторизации.",
            reply_markup=get_contact_keyboard(),
        )
        return

    shop = await get_shop_by_phone(user["phone_number"])
    if shop:
        await message.answer(
            f"📊 <b>Ваш профиль:</b>\n\n"
            f"🏪 Магазин: {shop.shop_name}\n"
            f"👤 Владелец: {shop.owner_name}\n"
            f"📍 Адрес: {shop.address}\n"
            f"📱 Телефон: {user.phone_number}",
            reply_markup=get_main_keyboard(),
        )
    else:
        await message.answer(
            f"📱 Телефон: {user.phone_number}\n\n"
            f"❗ Этот номер не найден в системе магазинов."
        )


@router.message(F.content_type == ContentType.CONTACT)
async def handle_contact(message: Message):
    contact = message.contact
    phone_number = contact.phone_number
    telegram_id = message.from_user.id

    if contact.user_id != telegram_id:
        await message.answer("Пожалуйста, отправьте свой собственный контакт.")
        return

    try:
        await save_user_profile(telegram_id, phone_number)

        user_states[telegram_id] = {"phone": phone_number}

        shop = await get_shop_by_phone(phone_number)

        if shop:
            await message.answer(
                f"✅ Успешная авторизация!\n\n"
                f"Вы зарегистрированы как магазин '{shop.shop_name}'.\n"
                f"Теперь вы можете загружать фотографии с геолокацией.",
                reply_markup=get_main_keyboard(),
            )
        else:
            await message.answer(
                "❌ Ваш номер не найден в нашей системе.\n"
                "Обратитесь к администратору для регистрации вашего магазина."
            )
    except Exception as e:
        logger.error(f"Error in handle_contact: {e}")
        await message.answer(
            "Произошла ошибка при проверке вашего номера. Пожалуйста, попробуйте позже."
        )


@router.message(F.content_type == ContentType.LOCATION)
async def handle_location(message: Message):
    telegram_id = message.from_user.id

    if telegram_id not in user_states:
        await message.answer(
            "Для начала работы необходимо авторизоваться. "
            "Пожалуйста, поделитесь своим контактом.",
            reply_markup=get_contact_keyboard(),
        )
        return

    user_states[telegram_id]["location"] = {
        "latitude": message.location.latitude,
        "longitude": message.location.longitude,
    }

    await message.answer(
        "📍 Геолокация получена!\n\nТеперь отправьте фотографию магазина.",
        reply_markup=get_photo_keyboard(),
    )


@router.message(F.content_type == ContentType.PHOTO)
async def handle_photo(message: Message, bot: Bot):
    telegram_id = message.from_user.id

    try:
        user_profile = await get_user_profile(telegram_id)
        if not user_profile:
            await message.answer(
                "Для загрузки фотографий необходимо авторизоваться. "
                "Пожалуйста, поделитесь своим контактом.",
                reply_markup=get_contact_keyboard(),
            )
            return

        user_state = user_states.get(telegram_id, {})
        location = user_state.get("location")

        if not location:
            await message.answer(
                "Сначала необходимо отправить геолокацию.",
                reply_markup=get_location_keyboard(),
            )
            return

        shop = await get_shop_by_phone(user_profile["phone_number"])
        if not shop:
            await message.answer(
                "К сожалению, ваш номер телефона не найден в системе магазинов. "
                "Обратитесь к администратору."
            )
            return

        photo = message.photo[-1]
        file_id = photo.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path

        bot_token = os.getenv("TG_TOKEN")
        if not bot_token:
            await message.answer(
                "Ошибка конфигурации сервера. Обратитесь к администратору."
            )
            logger.error("TG_TOKEN not found in environment variables!")
            return

        file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        filename = f"{uuid.uuid4().hex}.jpg"

        status_message = await message.answer("⏳ Загрузка фотографии...")

        try:
            relative_path = await download_photo(file_url, filename)
            await save_photo_to_post(
                shop.id,
                relative_path,
                latitude=location["latitude"],
                longitude=location["longitude"],
            )

            if "location" in user_states[telegram_id]:
                del user_states[telegram_id]["location"]

            await bot.edit_message_text(
                f"✅ Фото успешно сохранено и связано с магазином '{shop.shop_name}'.",
                chat_id=status_message.chat.id,
                message_id=status_message.message_id,
            )

            await message.answer(
                "Что бы вы хотели сделать дальше?", reply_markup=get_main_keyboard()
            )

        except Exception as e:
            logger.error(f"Error saving photo: {e}")
            await bot.edit_message_text(
                "❌ Произошла ошибка при сохранении фотографии. Пожалуйста, попробуйте позже.",
                chat_id=status_message.chat.id,
                message_id=status_message.message_id,
            )

    except Exception as e:
        logger.error(f"Uncaught error in handle_photo: {e}")
        await message.answer(
            "Произошла неизвестная ошибка. Пожалуйста, попробуйте позже."
        )


@router.message(F.text == "📷 Загрузить фото")
async def upload_photo_command(message: Message):
    telegram_id = message.from_user.id

    user_profile = await get_user_profile(telegram_id)
    if not user_profile:
        await message.answer(
            "Для загрузки фотографий необходимо авторизоваться. "
            "Пожалуйста, поделитесь своим контактом.",
            reply_markup=get_contact_keyboard(),
        )
        return

    await message.answer(
        "Сначала отправьте геолокацию магазина.",
        reply_markup=get_location_keyboard(),
    )


@router.message(F.text == "👤 Мой профиль")
async def profile_command(message: Message):
    await cmd_profile(message)


@router.message(F.text == "❓ Помощь")
async def help_command(message: Message):
    await cmd_help(message)


@router.message(F.text == "🔙 Назад")
async def back_command(message: Message):
    await message.answer(
        "Возвращаемся в главное меню.",
        reply_markup=get_main_keyboard(),
    )


@router.message()
async def unknown_message(message: Message):
    user = await get_user_profile(message.from_user.id)
    if not user:
        await message.answer(
            "Для начала работы, пожалуйста, поделитесь своим контактом.",
            reply_markup=get_contact_keyboard(),
        )
    else:
        await message.answer(
            "Я понимаю только фотографии и специальные команды. "
            "Отправьте фото или воспользуйтесь кнопками меню.",
            reply_markup=get_main_keyboard(),
        )
