import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from backend.models import WorkSession, WorkPause, User
from django.utils.timezone import localtime

user = User.objects.get(username="nonamelviv")
session = WorkSession.objects.filter(user=user).last()

if not session:
    print("У користувача немає жодної сесії.")
else:
    print(f"\nОстання сесія користувача {user.username}:")
    print(f"Початок: {localtime(session.start_time).strftime('%d.%m.%Y %H:%M')}")

    pauses = WorkPause.objects.filter(session=session).order_by("pause_time")

    if pauses.exists():
        for i, pause in enumerate(pauses, 1):
            pause_start = localtime(pause.pause_time).strftime('%H:%M')
            pause_end = localtime(pause.resume_time).strftime('%H:%M') if pause.resume_time else "Не завершено"
            print(f"⏸ Пауза {i}: {pause_start} → {pause_end}")
    else:
        print("Жодної паузи не було.")

    if session.end_time:
        print(f"Завершення: {localtime(session.end_time).strftime('%d.%m.%Y %H:%M')}")
    else:
        print("Сесія ще триває.")