from django.contrib import admin
from django.utils.timezone import localtime
from datetime import timedelta, datetime
import pytz
from .models import User, WorkSession, WorkPause

# Налаштовуємо київський часовий пояс
kyiv_tz = pytz.timezone('Europe/Kiev')

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'username', 'telegram_id', 'role', 'is_active', 'is_staff')
    search_fields = ('first_name', 'last_name', 'telegram_id')
    list_filter = ('role', 'is_active')
    fields = ('first_name', 'last_name', 'username', 'telegram_id', 'role', 'is_active', 'is_staff')


def calculate_actual_work_time(session):
    """
    Обчислює фактичний робочий час сесії з урахуванням перерв.
    Якщо пауза незавершена, а сесія завершена, час від початку такої паузи не враховується.
    """
    session_start = session.start_time.astimezone(kyiv_tz)
    actual_end_time = session.end_time.astimezone(kyiv_tz) if session.end_time else None

    work_intervals = []
    current_start = session_start

    # Використовуємо related_name 'pauses'
    pauses = session.pauses.all().order_by("pause_time")
    for pause in pauses:
        pause_start = pause.pause_time.astimezone(kyiv_tz)
        if pause.resume_time:
            pause_end = pause.resume_time.astimezone(kyiv_tz)
        elif actual_end_time:
            # Якщо сесія завершена, незавершену паузу вважаємо нульовою (resume_time = session.end_time)
            pause_end = actual_end_time
        else:
            # Якщо сесія триває, незавершена пауза розглядається як завершена в момент її початку
            pause_end = pause_start

        if pause_start > current_start:
            work_intervals.append(pause_start - current_start)
        current_start = pause_end

    if actual_end_time and actual_end_time > current_start:
        work_intervals.append(actual_end_time - current_start)
    elif not actual_end_time:
        # Якщо сесія триває, рахувати до поточного моменту
        work_intervals.append(datetime.now(kyiv_tz) - current_start)

    return sum(work_intervals, timedelta())


class WorkPauseInline(admin.TabularInline):
    model = WorkPause
    extra = 0  # Не створюємо нових записів автоматично


@admin.register(WorkSession)
class WorkSessionAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'formatted_start_time',
        'formatted_end_time',
        'calculated_work_time',
        'status'
    )
    list_filter = ('status',)
    search_fields = ('user__username', 'user__telegram_id')
    inlines = [WorkPauseInline]
    readonly_fields = ('calculated_work_time',)

    def formatted_start_time(self, obj):
        """Форматуємо дату початку у формат ДД.ММ.РРРР ГГ:ХХ"""
        return localtime(obj.start_time).strftime("%d.%m.%Y %H:%M")
    formatted_start_time.short_description = "Початок роботи"

    def formatted_end_time(self, obj):
        """
        Форматуємо дату завершення у формат ДД.ММ.РРРР ГГ:ХХ.
        Якщо сесія завершена, але є незавершена пауза, повертаємо час останнього початку незавершеної паузи.
        """
        if not obj.end_time:
            return "Ще триває"
        unfinished_pause = obj.pauses.filter(resume_time__isnull=True).order_by('-pause_time').first()
        if unfinished_pause:
            return localtime(unfinished_pause.pause_time).strftime("%d.%m.%Y %H:%M")
        return localtime(obj.end_time).strftime("%d.%m.%Y %H:%M")
    formatted_end_time.short_description = "Кінець роботи"

    def calculated_work_time(self, obj):
        """Обчислює фактичний робочий час сесії з урахуванням перерв"""
        work_time = calculate_actual_work_time(obj)
        total_seconds = int(work_time.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours} год {minutes} хв {seconds} сек"
    calculated_work_time.short_description = "Фактичний робочий час"
