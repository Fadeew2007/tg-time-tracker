from django.contrib import admin
from django.utils.timezone import localtime
from .models import User, WorkSession

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'username', 'telegram_id', 'role', 'is_active', 'is_staff')  # Тепер відображаємо імена
    search_fields = ('first_name', 'last_name', 'telegram_id')  # Додаємо пошук за іменем
    list_filter = ('role', 'is_active')  # Фільтри за роллю
    fields = ('first_name', 'last_name', 'username', 'telegram_id', 'role', 'is_active', 'is_staff')  # Поля, які можна змінювати

@admin.register(WorkSession)
class WorkSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'formatted_start_time', 'formatted_end_time', 'status')  # Форматовані дати
    list_filter = ('status',)
    search_fields = ('user__username', 'user__telegram_id')  # Додано пошук за Telegram ID

    def formatted_start_time(self, obj):
        """Форматуємо дату початку у формат ДД.ММ.РРРР ГГ:ХХ"""
        return localtime(obj.start_time).strftime("%d.%m.%Y %H:%M")
    formatted_start_time.short_description = "Початок роботи"

    def formatted_end_time(self, obj):
        """Форматуємо дату завершення у формат ДД.ММ.РРРР ГГ:ХХ"""
        return localtime(obj.end_time).strftime("%d.%m.%Y %H:%M") if obj.end_time else "Ще триває"
    formatted_end_time.short_description = "Кінець роботи"