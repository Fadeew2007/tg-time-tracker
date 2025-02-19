import os

# Отримуємо токен бота з середовища або використовуємо значення за замовчуванням
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7884553220:AAG4MquIKRujYaaAhtG0EuZDta6qGFqL0s")
API_URL = os.getenv("API_URL", "https://profound-wholeness-production-b760.up.railway.app/api/")

# Вивід для перевірки
print(f"API_URL: {API_URL}")  
print(f"Telegram Bot Token: {BOT_TOKEN}")  # Дебаг
