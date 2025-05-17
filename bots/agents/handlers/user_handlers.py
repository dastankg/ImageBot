import os
import uuid

from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import ContentType, Message
import logging
from aiogram import F, Router, Bot

from bots.agents.fsm.fsm import UserState
from bots.agents.handlers.utils import get_user_profile, get_agent_by_phone, save_user_profile, schedule, download_photo, save_photo_to_post
from bots.agents.keyboards.keyboard import get_contact_keyboard, get_main_keyboard, get_location_keyboard, \
    get_back_keyboard, get_photo_keyboard

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
@router.message(F.text == "❓ Помощь")
async def cmd_help(message: Message):
    await message.answer(
        "📋 <b>Инструкция по использованию бота:</b>\n\n"
        "1. Отправьте свой контакт для авторизации\n"
        "2. После успешной авторизации нажмите на кнопку «Загрузить фото»\n"
        "3. Введите название магазина для фотографии\n"
        "4. Отправьте геолокацию для привязки к фотографии\n"
        "5. Загрузите фотографию магазина\n\n"
        "Если у вас возникли проблемы, обратитесь к администратору."
    )


@router.message(Command("profile"))
@router.message(F.text == "👤 Мой профиль")
async def cmd_profile(message: Message, state: FSMContext):
    user = await get_user_profile(message.from_user.id)
    if not user:
        await message.answer(
            "Вы еще не авторизованы. Пожалуйста, поделитесь своим контактом для авторизации.",
            reply_markup=get_contact_keyboard(),
        )
        await state.set_state(UserState.unauthorized)
        return

    agent = await get_agent_by_phone(user["phone_number"])
    if agent:
        await message.answer(
            f"📊 <b>Ваш профиль:</b>\n\n"
            f"👤 Агент: {agent.agent_name}\n"
            f"📱 Телефон: {agent.agent_number}",
            reply_markup=get_main_keyboard(),
        )
    else:
        await message.answer(
            f"📱 Телефон: {user['phone_number']}\n\n"
            f"❗ Этот номер не найден в системе агентов."
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

        agent = await get_agent_by_phone(phone_number)

        if agent:
            await message.answer(
                f"✅ Успешная авторизация!\n\n"
                f"Вы зарегистрированы как агент '{agent.agent_name}'.\n"
                f"Теперь вы можете загружать фотографии магазинов с геолокацией.",
                reply_markup=get_main_keyboard(),
            )
        else:
            await message.answer(
                "❌ Ваш номер не найден в нашей системе.\n"
                "Обратитесь к администратору для регистрации вас как агента."
            )
    except Exception as e:
        logger.error(f"Error in handle_contact: {e}")
        await message.answer(
            "Произошла ошибка при проверке вашего номера. Пожалуйста, попробуйте позже."
        )


@router.message(F.text == "📷 Загрузить фото")
async def handle_upload_photo(message: Message, state: FSMContext):
    user = await get_user_profile(message.from_user.id)
    if not user:
        await message.answer(
            "Для загрузки фото необходимо авторизоваться. Пожалуйста, поделитесь контактом.",
            reply_markup=get_contact_keyboard(),
        )
        await state.set_state(UserState.unauthorized)
        return

    await state.set_state(UserState.waiting_for_shopName)
    await schedule(message)


@router.message(UserState.waiting_for_shopName)
async def handle_shop_name(message: Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.set_state(UserState.authorized)
        await message.answer(
            "Возвращаемся в главное меню.",
            reply_markup=get_main_keyboard(),
        )
        return

    shop_name = message.text

    if not shop_name or len(shop_name) > 100:
        await message.answer(
            "Название магазина должно быть не пустым и не более 100 символов.\n"
            "Пожалуйста, введите корректное название:",
            reply_markup=get_back_keyboard(),
        )
        return

    await state.update_data(shop_name=shop_name)
    await state.set_state(UserState.waiting_for_location)

    await message.answer(
        f"Название магазина '{shop_name}' сохранено.\n"
        f"Теперь отправьте геолокацию магазина.",
        reply_markup=get_location_keyboard(),
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

    state_data = await state.get_data()
    shop_name = state_data.get("shop_name")

    if not shop_name:
        await message.answer(
            "Сначала введите название магазина.",
            reply_markup=get_main_keyboard(),
        )
        await state.set_state(UserState.waiting_for_shopName)
        return

    await state.update_data(
        location={
            "latitude": message.location.latitude,
            "longitude": message.location.longitude,
        }
    )
    await state.set_state(UserState.waiting_for_photo)

    await message.answer(
        f"📍 Геолокация для магазина '{shop_name}' получена!\n\nТеперь отправьте фотографию магазина.",
        reply_markup=get_photo_keyboard(),
    )

@router.message(F.content_type == ContentType.DOCUMENT)
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
        shop_name = state_data.get("shop_name")

        if not shop_name:
            logger.info(f"Нет названия магазина для user_id={telegram_id}")
            await message.answer("Сначала введите название магазина.")
            await state.set_state(UserState.waiting_for_shopName)
            return

        if not location:
            logger.info(f"Нет геолокации для user_id={telegram_id}")
            await message.answer("Сначала отправьте геолокацию.")
            await state.set_state(UserState.waiting_for_location)
            return

        agent = await get_agent_by_phone(user_profile["phone_number"])
        if not agent:
            logger.warning(f"Агент не найден: phone={user_profile['phone_number']}")
            await message.answer("Вы не зарегистрированы как агент.")
            return

        document = message.document
        file_id = document.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        file_name = (
                document.file_name or f"{uuid.uuid4().hex}{os.path.splitext(file_path)[1]}"
        )

        logger.info(
            f"Загрузка фото от {telegram_id}: file_id={file_id}, path={file_path}"
        )

        file_url = (
            f"https://api.telegram.org/file/bot{os.getenv('BOT_TOKEN2')}/{file_path}"
        )

        status_message = await message.answer("⏳ Загрузка фотографии...")

        try:
            relative_path = await download_photo(file_url, file_name)
            await save_photo_to_post(
                agent.id,
                shop_name,
                relative_path,
                latitude=location["latitude"],
                longitude=location["longitude"],
            )

            logger.info(f"Фото сохранено: {file_name} для магазина {shop_name}")

            await state.update_data(location=None, shop_name=None)
            await state.set_state(UserState.authorized)

            await bot.edit_message_text(
                f"✅ Фото успешно сохранено для магазина '{shop_name}'.",
                chat_id=status_message.chat.id,
                message_id=status_message.message_id,
            )

            await message.answer("Что дальше?", reply_markup=get_main_keyboard())


        except Exception as e:
            error_message = str(e)
            logger.exception(
                f"Ошибка при сохранении файла от {telegram_id}: {error_message}"
            )
            if "более 3 минут назад" in error_message:
                await bot.edit_message_text(
                    "❌ Фото сделано более 3 минут назад. Пожалуйста, сделайте свежее фото.",
                    chat_id=status_message.chat.id,
                    message_id=status_message.message_id,
                )
            elif (
                    "EXIF данные отсутствуют" in error_message
                    or "метаданные отсутствуют" in error_message.lower()
            ):

                await bot.edit_message_text(
                    "❌ Фото не содержит необходимые метаданные (EXIF). Пожалуйста, сделайте фото через камеру телефона.",
                    chat_id=status_message.chat.id,
                    message_id=status_message.message_id,
                )
            else:
                await bot.edit_message_text(
                    "❌ Ошибка при сохранении файла.",
                    chat_id=status_message.chat.id,
                    message_id=status_message.message_id,
                )

    except Exception:
        logger.exception(f"Ошибка в handle_photo от {telegram_id}")
        await message.answer("❗ Неизвестная ошибка.")

@router.message(F.text == "🔙 Назад")
async def back_command(message: Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state in [
        UserState.waiting_for_location,
        UserState.waiting_for_photo,
        UserState.waiting_for_shopName,
    ]:
        await state.set_state(UserState.authorized)
        await state.update_data(location=None, shop_name=None)

    await message.answer(
        "Возвращаемся в главное меню.",
        reply_markup=get_main_keyboard(),
    )


@router.message()
async def unknown_message(message: Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state == UserState.waiting_for_shopName:
        await handle_shop_name(message, state)
        return

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
            "Воспользуйтесь кнопками меню.",
            reply_markup=get_main_keyboard(),
        )
