import logging
from datetime import datetime

import requests
import pytz

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, FSInputFile

from bot.config import API_URL

router = Router()
user_tokens = {}

logging.basicConfig(
    filename="button_logs.txt",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S"
)

kyiv_tz = pytz.timezone("Europe/Kyiv")

def log_button_press(user_id, username, button_text):
    log_entry = f"{datetime.now(kyiv_tz).strftime('%d-%m-%Y %H:%M:%S')} | User ID: {user_id} | Username: {username} | Button: {button_text}"
    logging.info(log_entry)
    print(log_entry)

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

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="▶️ Почати роботу")],
                [KeyboardButton(text="📊 Мої години")],
                [KeyboardButton(text="📋 Звіт")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "🍰 Вітаємо в DESSEE!\n\n"
            "📌 Команди:\n"
            "▶️ Почати роботу – розпочати зміну\n"
            "⏸ Пауза – піти на перерву\n"
            "▶️ Відновити – продовжити роботу після перерви\n"
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
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="▶️ Почати роботу")],
                [KeyboardButton(text="📊 Мої години")],
                [KeyboardButton(text="📋 Звіт")]
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
    telegram_id = message.from_user.id
    token = user_tokens.get(telegram_id)

    if not token:
        await message.answer("❌ Будь ласка, спершу введіть /start для автентифікації.")
        return

    response = requests.get(f"{API_URL}active_session/", headers={"Authorization": f"Token {token}"})
    data = response.json()

    if response.status_code == 200 and data.get("active", False):
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="⏸ Пауза"), KeyboardButton(text="🛑 Завершити")],
                [KeyboardButton(text="📊 Мої години")],
                [KeyboardButton(text="📋 Звіт")]
            ],
            resize_keyboard=True
        )
    else:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="▶️ Почати роботу")],
                [KeyboardButton(text="📊 Мої години")],
                [KeyboardButton(text="📋 Звіт")]
            ],
            resize_keyboard=True
        )

    await message.answer("🔙 Повернення в головне меню:", reply_markup=keyboard)

@router.message(ReportState.choosing_worker)
async def handle_worker_choice(message: types.Message, state: FSMContext):
    # Якщо натиснуто кнопку повернення ("⬅️ Назад" або "все")
    if message.text in ["В головне меню"]:
        await state.clear()  # Очищення/скидання стану
        telegram_id = message.from_user.id
        token = user_tokens.get(telegram_id)
        if not token:
            await message.answer("❌ Будь ласка, спершу введіть /start для автентифікації.")
            return

        response = requests.get(f"{API_URL}active_session/", headers={"Authorization": f"Token {token}"})
        data = response.json()
        if response.status_code == 200 and data.get("active", False):
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="⏸ Пауза"), KeyboardButton(text="🛑 Завершити")],
                    [KeyboardButton(text="📊 Мої години")],
                    [KeyboardButton(text="📋 Звіт")]
                ],
                resize_keyboard=True
            )
        else:
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="▶️ Почати роботу")],
                    [KeyboardButton(text="📊 Мої години")],
                    [KeyboardButton(text="📋 Звіт")]
                ],
                resize_keyboard=True
            )
        await message.answer("🔙 Повернення в головне меню:", reply_markup=keyboard)
        return

    # Якщо натиснуто кнопку з ім'ям працівника, отримуємо дані стану
    data = await state.get_data()
    worker = next((w for w in data.get("workers", []) if w["name"] == message.text), None)
    if not worker:
        await message.answer("❌ Невірний вибір, спробуйте ще раз.")
        return

    # Якщо працівника знайдено – переходимо до вибору року
    telegram_id = message.from_user.id
    token = user_tokens.get(telegram_id)
    response = requests.get(f"{API_URL}admin/years/{worker['id']}/", headers={"Authorization": f"Token {token}"})
    if response.status_code == 200 and response.json():
        years = response.json()
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=str(year))] for year in years],
            resize_keyboard=True,
        )
        await state.set_state(ReportState.choosing_year)
        await state.update_data(worker=worker)
        await message.answer("📅 Оберіть рік:", reply_markup=keyboard)
    else:
        await message.answer("❌ Немає даних за жоден рік.")

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
            keyboard=[[KeyboardButton(text=worker["name"])] for worker in workers] + [[KeyboardButton(text="В головне меню")]],
            resize_keyboard=True,
        )
        await state.set_state(ReportState.choosing_worker)
        await state.update_data(workers=workers)
        await message.answer("👤 Оберіть працівника:", reply_markup=keyboard)
    else:
        try:
            data = response.json()
            error = data.get("error", "❌ Немає доступних працівників.")
        except Exception:
            error = "❌ Немає доступних працівників."
        await message.answer(error)

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
            resize_keyboard=True
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
            resize_keyboard=True
        )
        await state.set_state(ReportState.choosing_month)
        await state.update_data(year=year)
        await message.answer("📅 Оберіть місяць:", reply_markup=keyboard)
    else:
        await message.answer("❌ Немає даних за жоден місяць.")


@router.message(ReportState.choosing_month)
async def show_report(message: types.Message, state: FSMContext):
    data = await state.get_data()
    worker = data.get("worker")
    year = data.get("year")
    month = message.text  # Місяць береться з повідомлення

    if not worker or not year or not month:
        await message.answer("❌ Сталася помилка. Спробуйте ще раз.")
        return

    telegram_id = message.from_user.id
    token = user_tokens.get(telegram_id)

    response = requests.get(f"{API_URL}admin/report/{worker['id']}/{year}/{month}/", headers={"Authorization": f"Token {token}"})

    temp_data = {"year": year, "month": month}

    await state.clear()

    await state.update_data(temp_data)

    if response.status_code == 200:
        report = response.json().get("report", "❌ Дані відсутні.")

        # Додаємо кнопку для завантаження Excel
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📥 Завантажити Excel")],  # Ось нова кнопка
                [KeyboardButton(text="⬅️ Назад")]
            ],
            resize_keyboard=True
        )

        await message.answer(report, reply_markup=keyboard)
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

@router.message(F.text == "📥 Завантажити Excel")
async def download_excel_report(message: types.Message, state: FSMContext):
    data = await state.get_data()
    year, month = data.get("year"), data.get("month")

    print(f"DEBUG: Year={year}, Month={month}")

    if not year or not month:
        await message.answer("❌ Спершу оберіть рік і місяць для звіту.")
        return

    telegram_id = message.from_user.id
    token = user_tokens.get(telegram_id)

    if not token:
        await message.answer("❌ Будь ласка, спершу введіть /start для автентифікації.")
        return

    file_url = f"{API_URL}admin/export_excel/{year}/{month}/"
    headers = {"Authorization": f"Token {token}"}

    print(f"DEBUG: Запит до {file_url} з headers={headers}")  # Лог запиту

    response = requests.get(file_url, headers=headers)

    print(f"DEBUG: Статус код = {response.status_code}")

    if response.status_code == 200:
        file_path = f"звіт_годин_за_{month}_{year}.xlsx"

        with open(file_path, "wb") as file:
            file.write(response.content)

        print(f"DEBUG: Файл збережено як {file_path}")

        import os
        if os.path.exists(file_path):
            print(f"DEBUG: Файл {file_path} існує, пробуємо відправити")
        else:
            print(f"ERROR: Файл {file_path} не знайдено!")
            await message.answer("❌ Помилка: Файл не знайдено після завантаження.")
            return

        # Відправляємо файл в Telegram через FSInputFile
        try:
            document = FSInputFile(file_path)  # Ось тут ми правильно передаємо файл
            await message.answer_document(document)
            print("DEBUG: Файл успішно надіслано у Telegram")
        except Exception as e:
            print(f"ERROR: Не вдалося відправити файл. Помилка: {e}")
            await message.answer(f"❌ Помилка відправлення файлу: {e}")
    else:
        await message.answer("❌ Не вдалося отримати файл.")