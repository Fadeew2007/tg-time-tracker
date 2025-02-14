from django.contrib import admin
from .models import User, WorkSession

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'telegram_id', 'role', 'is_active', 'is_staff')  # Поля для списку
    search_fields = ('username', 'telegram_id')  # Додає пошук по username і Telegram ID
    list_filter = ('role', 'is_active')  # Фільтри за роллю та активністю
    fields = ('username', 'telegram_id', 'role', 'is_active', 'is_staff')  # Поля, які можна змінювати

@admin.register(WorkSession)
class WorkSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'start_time', 'end_time', 'status')
    list_filter = ('status',)
    search_fields = ('user__username',)