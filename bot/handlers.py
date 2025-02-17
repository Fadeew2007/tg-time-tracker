import logging
from datetime import datetime

import requests
import pytz

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from bot.config import API_URL

# Ініціалізація роутера
router = Router()
user_tokens = {}

# Налаштування логування
logging.basicConfig(
    filename="button_logs.txt",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S"
)

# Часовий пояс Києва
kyiv_tz = pytz.timezone("Europe/Kyiv")

def log_button_press(user_id, username, button_text):
    """Функція запису натискань кнопок у лог"""
    log_entry = f"{datetime.now(kyiv_tz).strftime('%d-%m-%Y %H:%M:%S')} | User ID: {user_id} | Username: {username} | Button: {button_text}"
    logging.info(log_entry)
    print(log_entry)  # Вивід у консоль для зручності

class ReportState(StatesGroup):
    choosing_worker = State()
    choosing_year = State()
    choosing_month = State()


@router.message(Command("start"))
async def start(message: types.Message):
    telegram_id = message.from_user.id
    username = message.from_user.username or f"user_{telegram_id}"

    response = requests.post(f"{API_URL}auth/", json={"telegram_id": telegram_id, "username": username})

    if response.status_code == 200:
        data = response.json()
        user_tokens[telegram_id] = data["token"]

        # Створюємо клавіатуру з кнопками
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="▶️ Почати роботу"), KeyboardButton(text="📊 Мої години"), KeyboardButton(text="📋 Звіт")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "🍰 Вітаємо в DESSEE!\n\n"
            "📌 Команди:\n"
            "▶️ Почати роботу – розпочати зміну\n"
            "⏸ Пауза – поставити роботу на паузу\n"
            "▶️ Відновити – продовжити роботу після паузи\n"
            "🛑 Завершити – завершити зміну\n\n"
            "📊 Мої години – переглянути свої робочі години\n\n"
            "📋 Звіт – для адмінів\n\n"
            "⚡ Використовуйте кнопки нижче для швидкого доступу!",
            reply_markup=keyboard
        )
    else:
        await message.answer("❌ Помилка автентифікації.")


@router.message(Command("start_work"))
async def start_work(message: types.Message):
    telegram_id = message.from_user.id
    token = user_tokens.get(telegram_id)

    log_button_press(telegram_id, message.from_user.username, "▶️ Почати роботу")

    if not token:
        await message.answer("❌ Будь ласка, спершу введіть /start для автентифікації.")
        return

    response = requests.post(f"{API_URL}start_work/", headers={"Authorization": f"Token {token}"})
    data = response.json()

    if response.status_code == 200:
        # Оновлюємо клавіатуру після старту роботи
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="⏸ Пауза"), KeyboardButton(text="🛑 Завершити")],
                [KeyboardButton(text="📊 Мої години"), KeyboardButton(text="📋 Звіт")]
            ],
            resize_keyboard=True
        )

        await message.answer("✅ Роботу розпочато! Гарного дня!🌞", reply_markup=keyboard)
    else:
        await message.answer(data.get("error", "❌ Помилка: неможливо розпочати зміну."))

@router.message(Command("pause_work"))
async def pause_work(message: types.Message):
    telegram_id = message.from_user.id
    token = user_tokens.get(telegram_id)

    log_button_press(telegram_id, message.from_user.username, "⏸ Пауза")

    if not token:
        await message.answer("❌ Будь ласка, спершу введіть /start для автентифікації.")
        return

    response = requests.post(f"{API_URL}pause_work/", headers={"Authorization": f"Token {token}"})
    data = response.json()

    if response.status_code == 200:
        # Оновлюємо клавіатуру після паузи роботи
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="▶️ Відновити"), KeyboardButton(text="🛑 Завершити")],
                [KeyboardButton(text="📊 Мої години"), KeyboardButton(text="📋 Звіт")]
            ],
            resize_keyboard=True
        )

        await message.answer("⏸ Робота поставлена на паузу!", reply_markup=keyboard)
    else:
        await message.answer(data.get("error", "❌ Помилка: немає активної сесії."))

@router.message(Command("resume_work"))
async def resume_work(message: types.Message):
    telegram_id = message.from_user.id
    token = user_tokens.get(telegram_id)

    log_button_press(telegram_id, message.from_user.username, "▶️ Відновити")

    if not token:
        await message.answer("❌ Будь ласка, спершу введіть /start для автентифікації.")
        return

    response = requests.post(f"{API_URL}resume_work/", headers={"Authorization": f"Token {token}"})
    data = response.json()

    if response.status_code == 200:
        # Оновлюємо клавіатуру після відновлення роботи
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="⏸ Пауза"), KeyboardButton(text="🛑 Завершити")],
                [KeyboardButton(text="📊 Мої години"), KeyboardButton(text="📋 Звіт")]
            ],
            resize_keyboard=True
        )

        await message.answer("▶️ Робота відновлена!", reply_markup=keyboard)
    else:
        await message.answer(data.get("error", "❌ Помилка: немає сесії на паузі."))

@router.message(Command("stop_work"))
async def stop_work(message: types.Message):
    telegram_id = message.from_user.id
    token = user_tokens.get(telegram_id)

    log_button_press(telegram_id, message.from_user.username, "🛑 Завершити")

    if not token:
        await message.answer("❌ Будь ласка, спершу введіть /start для автентифікації.")
        return

    response = requests.post(f"{API_URL}stop_work/", headers={"Authorization": f"Token {token}"})
    data = response.json()

    if response.status_code == 200:
        # Оновлюємо клавіатуру після завершення роботи
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="▶️ Почати роботу")],
                [KeyboardButton(text="📊 Мої години"), KeyboardButton(text="📋 Звіт")]
            ],
            resize_keyboard=True
        )

        await message.answer("✅ Робоча зміна завершена! Дякуємо за роботу!", reply_markup=keyboard)
    else:
        await message.answer(data.get("error", "❌ Помилка: немає активної зміни."))


@router.message(Command("my_hours"))
async def my_hours(message: types.Message):
    telegram_id = message.from_user.id
    token = user_tokens.get(telegram_id)

    if not token:
        await message.answer("❌ Будь ласка, спершу введіть /start для автентифікації.")
        return

    response = requests.get(f"{API_URL}my_hours/", headers={"Authorization": f"Token {token}"})
    data = response.json()

    if response.status_code == 200:
        if "error" in data:
            await message.answer(data["error"])
            return

        summary = data["summary"]
        days_list = "\n".join(data["days"])

        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⏪ Попередній місяць")]],
            resize_keyboard=True
        )

        await message.answer(f"{summary}\n\n{days_list}", reply_markup=keyboard)
    else:
        await message.answer("❌ Помилка отримання годин.")@router.message(Command("my_hours"))
async def my_hours(message: types.Message):
    """Отримує години поточного місяця та виводить кнопку '⬅️ Назад'"""
    telegram_id = message.from_user.id
    token = user_tokens.get(telegram_id)

    if not token:
        await message.answer("❌ Будь ласка, спершу введіть /start для автентифікації.")
        return

    response = requests.get(f"{API_URL}my_hours/", headers={"Authorization": f"Token {token}"})
    data = response.json()

    if response.status_code == 200:
        if "error" in data:
            await message.answer(data["error"])
            return

        summary = data["summary"]
        days_list = "\n".join(data["days"])

        # Додаємо кнопку "⬅️ Назад"
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="⬅️ Назад")]
            ],
            resize_keyboard=True
        )

        await message.answer(f"{summary}\n\n{days_list}", reply_markup=keyboard)
    else:
        await message.answer("❌ Помилка отримання годин.")

@router.message(F.text == "⬅️ Назад")
async def go_back(message: types.Message):
    """Перевіряє, чи є активна сесія, і повертає відповідні кнопки"""
    telegram_id = message.from_user.id
    token = user_tokens.get(telegram_id)

    if not token:
        await message.answer("❌ Будь ласка, спершу введіть /start для автентифікації.")
        return

    # Отримуємо статус активної сесії
    response = requests.get(f"{API_URL}active_session/", headers={"Authorization": f"Token {token}"})
    data = response.json()

    if response.status_code == 200 and data.get("active", False):
        # Якщо сесія активна, показуємо кнопки для паузи або завершення
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="⏸ Пауза"), KeyboardButton(text="🛑 Завершити")],
                [KeyboardButton(text="📋 Звіт")],
                [KeyboardButton(text="📊 Мої години")]
            ],
            resize_keyboard=True
        )
    else:
        # Якщо сесія неактивна, показуємо кнопку початку роботи
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="▶️ Почати роботу")],
                [KeyboardButton(text="📋 Звіт")],
                [KeyboardButton(text="📊 Мої години")]
            ],
            resize_keyboard=True
        )

    await message.answer("🔙 Повернення в головне меню:", reply_markup=keyboard)


@router.message(Command("report"))
async def start_report(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    token = user_tokens.get(telegram_id)

    if not token:
        await message.answer("❌ Будь ласка, спершу введіть /start для автентифікації.")
        return

    response = requests.get(f"{API_URL}admin/workers/", headers={"Authorization": f"Token {token}"})
    if response.status_code == 200 and response.json():
        workers = response.json()
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=worker["name"])] for worker in workers],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await state.set_state(ReportState.choosing_worker)
        await state.update_data(workers=workers)
        await message.answer("👤 Оберіть працівника:", reply_markup=keyboard)
    else:
        await message.answer("❌ Немає доступних працівників.")


@router.message(ReportState.choosing_worker)
async def choose_year(message: types.Message, state: FSMContext):
    data = await state.get_data()
    worker = next((w for w in data["workers"] if w["name"] == message.text), None)

    if not worker:
        await message.answer("❌ Невірний вибір, спробуйте ще раз.")
        return

    telegram_id = message.from_user.id
    token = user_tokens.get(telegram_id)

    response = requests.get(f"{API_URL}admin/years/{worker['id']}/", headers={"Authorization": f"Token {token}"})
    if response.status_code == 200 and response.json():
        years = response.json()
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=str(year))] for year in years],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await state.set_state(ReportState.choosing_year)
        await state.update_data(worker=worker)
        await message.answer("📅 Оберіть рік:", reply_markup=keyboard)
    else:
        await message.answer("❌ Немає даних за жоден рік.")


@router.message(ReportState.choosing_year)
async def choose_month(message: types.Message, state: FSMContext):
    data = await state.get_data()
    worker, year = data["worker"], message.text

    telegram_id = message.from_user.id
    token = user_tokens.get(telegram_id)

    response = requests.get(f"{API_URL}admin/months/{worker['id']}/{year}/", headers={"Authorization": f"Token {token}"})
    if response.status_code == 200 and response.json():
        months = response.json()
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=str(month))] for month in months],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await state.set_state(ReportState.choosing_month)
        await state.update_data(year=year)
        await message.answer("📅 Оберіть місяць:", reply_markup=keyboard)
    else:
        await message.answer("❌ Немає даних за жоден місяць.")


@router.message(ReportState.choosing_month)
async def show_report(message: types.Message, state: FSMContext):
    data = await state.get_data()
    worker, year, month = data["worker"], data["year"], message.text

    telegram_id = message.from_user.id
    token = user_tokens.get(telegram_id)

    response = requests.get(f"{API_URL}admin/report/{worker['id']}/{year}/{month}/", headers={"Authorization": f"Token {token}"})
    
    await state.clear()

    if response.status_code == 200:
        report = response.json().get("report", "❌ Дані відсутні.")
        await message.answer(report)
    else:
        await message.answer("❌ Помилка отримання звіту.")

@router.message(F.text == "▶️ Почати роботу")
async def button_start_work(message: types.Message):
    await start_work(message)

@router.message(F.text == "⏸ Пауза")
async def button_pause_work(message: types.Message):
    await pause_work(message)

@router.message(F.text == "▶️ Відновити")
async def button_resume_work(message: types.Message):
    await resume_work(message)

@router.message(F.text == "🛑 Завершити")
async def button_stop_work(message: types.Message):
    await stop_work(message)

@router.message(F.text == "📊 Мої години")
async def button_my_hours(message: types.Message):
    await my_hours(message)

@router.message(F.text == "📋 Звіт")
async def button_report(message: types.Message, state: FSMContext):
    await start_report(message, state)