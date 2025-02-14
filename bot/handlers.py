from aiogram import Router, types, F
from aiogram.filters import Command
import requests
from bot.config import API_URL

router = Router()
user_tokens = {}  # Збереження токенів користувачів у пам’яті (тимчасово)

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
        await message.answer("Помилка автентифікації.")

@router.message(Command("start_work"))
async def start_work(message: types.Message):
    telegram_id = message.from_user.id
    token = user_tokens.get(telegram_id)

    if not token:
        await message.answer("Будь ласка, спершу введіть /start для автентифікації.")
        return

    response = requests.post(f"{API_URL}start_work/", headers={"Authorization": f"Token {token}"})
    if response.status_code == 200:
        await message.answer("Роботу розпочато!")
    else:
        await message.answer("Помилка: неможливо розпочати зміну.")

@router.message(Command("stop_work"))
async def stop_work(message: types.Message):
    telegram_id = message.from_user.id
    token = user_tokens.get(telegram_id)

    if not token:
        await message.answer("Будь ласка, спершу введіть /start для автентифікації.")
        return

    response = requests.post(f"{API_URL}stop_work/", headers={"Authorization": f"Token {token}"})
    if response.status_code == 200:
        await message.answer("Робоча зміна завершена!")
    else:
        await message.answer("Помилка: немає активної зміни.")

@router.message(Command("my_hours"))
async def my_hours(message: types.Message):
    telegram_id = message.from_user.id
    token = user_tokens.get(telegram_id)

    if not token:
        await message.answer("Будь ласка, спершу введіть /start для автентифікації.")
        return

    response = requests.get(f"{API_URL}my_hours/", headers={"Authorization": f"Token {token}"})
    if response.status_code == 200:
        data = response.json()
        text = "\n".join([f"{item['start_time']} - {item.get('end_time', 'Ще триває')}" for item in data])
        await message.answer(f"Твої години:\n{text}")
    else:
        await message.answer("Помилка отримання годин.")

@router.message(Command("report"))
async def admin_report(message: types.Message):
    telegram_id = message.from_user.id
    token = user_tokens.get(telegram_id)

    if not token:
        await message.answer("Будь ласка, спершу введіть /start для автентифікації.")
        return

    response = requests.get(f"{API_URL}admin/report/", headers={"Authorization": f"Token {token}"})
    
    if response.status_code == 200:
        data = response.json()
        if not data:
            await message.answer("📊 Немає даних про робочі години.")
            return

        # Надсилаємо текст частинами, щоб уникнути ліміту Telegram
        for chunk in [data[i:i+4096] for i in range(0, len(data), 4096)]:
            await message.answer(chunk)
    
    elif response.status_code == 403:
        await message.answer("🚫 У вас немає прав для перегляду цього звіту.")
    else:
        await message.answer("❌ Помилка отримання звіту.")
