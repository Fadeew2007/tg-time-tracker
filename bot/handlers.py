import requests

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from bot.config import API_URL

router = Router()
user_tokens = {}  # Збереження токенів користувачів у пам’яті (тимчасово)


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
        await message.answer("Привіт! Ви успішно автентифіковані.\nВикористовуй /start_work, /stop_work, /my_hours, /report для відстеження робочого часу.")
    else:
        await message.answer("❌ Помилка автентифікації.")


@router.message(Command("start_work"))
async def start_work(message: types.Message):
    telegram_id = message.from_user.id
    token = user_tokens.get(telegram_id)

    if not token:
        await message.answer("❌ Будь ласка, спершу введіть /start для автентифікації.")
        return

    response = requests.post(f"{API_URL}start_work/", headers={"Authorization": f"Token {token}"})
    if response.status_code == 200:
        await message.answer("✅ Роботу розпочато!")
    else:
        await message.answer("❌ Помилка: неможливо розпочати зміну.")


@router.message(Command("stop_work"))
async def stop_work(message: types.Message):
    telegram_id = message.from_user.id
    token = user_tokens.get(telegram_id)

    if not token:
        await message.answer("❌ Будь ласка, спершу введіть /start для автентифікації.")
        return

    response = requests.post(f"{API_URL}stop_work/", headers={"Authorization": f"Token {token}"})
    if response.status_code == 200:
        await message.answer("✅ Робоча зміна завершена!")
    else:
        await message.answer("❌ Помилка: немає активної зміни.")


@router.message(Command("my_hours"))
async def my_hours(message: types.Message):
    telegram_id = message.from_user.id
    token = user_tokens.get(telegram_id)

    if not token:
        await message.answer("❌ Будь ласка, спершу введіть /start для автентифікації.")
        return

    response = requests.get(f"{API_URL}my_hours/", headers={"Authorization": f"Token {token}"})
    if response.status_code == 200:
        data = response.json()
        text = "\n".join([f"{item['start_time']} - {item.get('end_time', 'Ще триває')}" for item in data])
        await message.answer(f"🕒 Твої години:\n{text}")
    else:
        await message.answer("❌ Помилка отримання годин.")


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
