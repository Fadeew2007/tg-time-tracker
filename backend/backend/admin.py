from django.contrib import admin
from .models import User, WorkSession

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'username', 'telegram_id', 'role', 'is_active', 'is_staff')  # Тепер відображаємо імена
    search_fields = ('first_name', 'last_name', 'telegram_id')  # Додаємо пошук за іменем
    list_filter = ('role', 'is_active')  # Фільтри за роллю
    fields = ('first_name', 'last_name', 'username', 'telegram_id', 'role', 'is_active', 'is_staff')  # Поля, які можна змінювати

@admin.register(WorkSession)
class WorkSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'start_time', 'end_time', 'status')
    list_filter = ('status',)
    search_fields = ('user__username',)