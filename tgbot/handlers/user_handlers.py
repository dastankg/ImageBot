import logging
import os
import uuid

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import ContentType, Message

from tgbot.FSM.fsm import UserState
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


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    logger.info(f"/start от {message.from_user.id} ({message.from_user.full_name})")
    await message.answer(
        "👋 Привет! Я бот для загрузки фотографий магазинов.\n\n"
        "Для начала работы, пожалуйста, поделитесь своим контактом, "
        "чтобы я мог проверить ваш номер телефона в системе.",
        reply_markup=get_contact_keyboard(),
    )
    await state.set_state(UserState.unauthorized)


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
async def cmd_profile(message: Message, state: FSMContext):
    user = await get_user_profile(message.from_user.id)
    if not user:
        await message.answer(
            "Вы еще не авторизованы. Пожалуйста, поделитесь своим контактом для авторизации.",
            reply_markup=get_contact_keyboard(),
        )
        await state.set_state(UserState.unauthorized)
        return

    shop = await get_shop_by_phone(user["phone_number"])
    if shop:
        await message.answer(
            f"📊 <b>Ваш профиль:</b>\n\n"
            f"🏪 Магазин: {shop.shop_name}\n"
            f"👤 Владелец: {shop.owner_name}\n"
            f"📍 Адрес: {shop.address}\n"
            f"📱 Телефон: {user['phone_number']}",
            reply_markup=get_main_keyboard(),
        )
    else:
        await message.answer(
            f"📱 Телефон: {user['phone_number']}\n\n"
            f"❗ Этот номер не найден в системе магазинов."
        )


@router.message(F.content_type == ContentType.CONTACT)
async def handle_contact(message: Message, state: FSMContext):
    contact = message.contact
    phone_number = contact.phone_number
    telegram_id = message.from_user.id
    logger.info(f"Контакт от {telegram_id}: {phone_number}")
    if contact.user_id != telegram_id:
        await message.answer("Пожалуйста, отправьте свой собственный контакт.")
        return

    try:
        await save_user_profile(telegram_id, phone_number)

        await state.update_data(phone=phone_number)
        await state.set_state(UserState.authorized)

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
async def handle_location(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    user = await get_user_profile(telegram_id)

    if not user:
        await message.answer(
            "Для начала работы необходимо авторизоваться. "
            "Пожалуйста, поделитесь своим контактом.",
            reply_markup=get_contact_keyboard(),
        )
        await state.set_state(UserState.unauthorized)
        return

    # Save location to state
    await state.update_data(
        location={
            "latitude": message.location.latitude,
            "longitude": message.location.longitude,
        }
    )
    await state.set_state(UserState.waiting_for_photo)

    await message.answer(
        "📍 Геолокация получена!\n\nТеперь отправьте фотографию магазина.",
        reply_markup=get_photo_keyboard(),
    )


@router.message(F.content_type == ContentType.PHOTO)
async def handle_photo(message: Message, bot: Bot, state: FSMContext):
    telegram_id = message.from_user.id
    logger.info(f"Получено фото от user_id={telegram_id}")

    try:
        user_profile = await get_user_profile(telegram_id)
        if not user_profile:
            logger.warning(f"Неизвестный пользователь: {telegram_id}")
            await message.answer("Авторизуйтесь.")
            await state.set_state(UserState.unauthorized)
            return

        state_data = await state.get_data()
        location = state_data.get("location")

        if not location:
            logger.info(f"Нет геолокации для user_id={telegram_id}")
            await message.answer("Сначала отправьте геолокацию.")
            await state.set_state(UserState.waiting_for_location)
            return

        shop = await get_shop_by_phone(user_profile["phone_number"])
        if not shop:
            logger.warning(f"Магазин не найден: phone={user_profile['phone_number']}")
            await message.answer("Ваш магазин не зарегистрирован.")
            return

        photo = message.photo[-1]
        file_id = photo.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path

        logger.info(
            f"Загрузка фото от {telegram_id}: file_id={file_id}, path={file_path}"
        )

        file_url = (
            f"https://api.telegram.org/file/bot{os.getenv('BOT_TOKEN')}/{file_path}"
        )
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

            logger.info(f"Фото сохранено: {filename} для магазина {shop.shop_name}")

            await state.update_data(location=None)
            await state.set_state(UserState.authorized)

            await bot.edit_message_text(
                f"✅ Фото успешно сохранено и связано с магазином '{shop.shop_name}'.",
                chat_id=status_message.chat.id,
                message_id=status_message.message_id,
            )

            await message.answer("Что дальше?", reply_markup=get_main_keyboard())

        except Exception as e:
            logger.exception(f"Ошибка при сохранении фото от {telegram_id}")
            await bot.edit_message_text(
                "❌ Ошибка при сохранении фото.",
                chat_id=status_message.chat.id,
                message_id=status_message.message_id,
            )

    except Exception as e:
        logger.exception(f"Ошибка в handle_photo от {telegram_id}")
        await message.answer("❗ Неизвестная ошибка.")


@router.message(F.text == "📷 Загрузить фото")
async def upload_photo_command(message: Message, state: FSMContext):
    telegram_id = message.from_user.id

    user_profile = await get_user_profile(telegram_id)
    if not user_profile:
        await message.answer(
            "Для загрузки фотографий необходимо авторизоваться. "
            "Пожалуйста, поделитесь своим контактом.",
            reply_markup=get_contact_keyboard(),
        )
        await state.set_state(UserState.unauthorized)
        return

    await state.set_state(UserState.waiting_for_location)
    await message.answer(
        "Сначала отправьте геолокацию магазина.",
        reply_markup=get_location_keyboard(),
    )


@router.message(F.text == "👤 Мой профиль")
async def profile_command(message: Message, state: FSMContext):
    await cmd_profile(message, state)


@router.message(F.text == "❓ Помощь")
async def help_command(message: Message):
    await cmd_help(message)


@router.message(F.text == "🔙 Назад")
async def back_command(message: Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state in [UserState.waiting_for_location, UserState.waiting_for_photo]:
        await state.set_state(UserState.authorized)

    await message.answer(
        "Возвращаемся в главное меню.",
        reply_markup=get_main_keyboard(),
    )


@router.message()
async def unknown_message(message: Message, state: FSMContext):
    user = await get_user_profile(message.from_user.id)
    if not user:
        await message.answer(
            "Для начала работы, пожалуйста, поделитесь своим контактом.",
            reply_markup=get_contact_keyboard(),
        )
        await state.set_state(UserState.unauthorized)
    else:
        await message.answer(
            "Я понимаю только фотографии и специальные команды. "
            "Отправьте фото или воспользуйтесь кнопками меню.",
            reply_markup=get_main_keyboard(),
        )
