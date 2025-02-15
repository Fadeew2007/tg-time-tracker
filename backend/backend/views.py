from collections import defaultdict
from datetime import datetime, timedelta
import pytz

from django.db.models import Count, Sum
from django.utils.timezone import now

from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User, WorkSession

kyiv_tz = pytz.timezone("Europe/Kyiv")

class TelegramAuth(APIView):
    def post(self, request):
        telegram_id = request.data.get("telegram_id")
        username = request.data.get("username", f"user_{telegram_id}")

        if not telegram_id:
            return Response({"error": "Не вказано Telegram ID"}, status=400)

        user, created = User.objects.get_or_create(telegram_id=telegram_id, defaults={"username": username})
        token, _ = Token.objects.get_or_create(user=user)

        return Response({"token": token.key, "user_id": user.id, "role": user.role})

class StartWork(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        current_time = now().astimezone(kyiv_tz)

        existing_session = WorkSession.objects.filter(user=user, status="active").last()
        if existing_session:
            return Response({"error": "❌ У вас вже є активна зміна! Використовуйте /pause_work для перерви або /stop_work для завершення."}, status=400)

        session = WorkSession.objects.create(user=user, start_time=current_time, status="active")
        return Response({"message": "✅ Роботу розпочато!", "session_id": session.id})

class PauseWork(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session = WorkSession.objects.filter(user=request.user, status="active").last()

        if not session:
            return Response({"error": "❌ Ви ще не почали роботу! Використовуйте /start_work."}, status=400)

        session.pause_time = now().astimezone(kyiv_tz)
        session.status = "paused"
        session.save()
        return Response({"message": "⏸ Робота поставлена на паузу!"})

class ResumeWork(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session = WorkSession.objects.filter(user=request.user, status="paused").last()

        if not session:
            return Response({"error": "❌ Ваша зміна не була поставлена на паузу!"}, status=400)

        session.resume_time = now().astimezone(kyiv_tz)
        session.status = "active"
        session.save()
        return Response({"message": "▶️ Робота відновлена!"})

class StopWork(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session = WorkSession.objects.filter(user=request.user, status__in=["active", "paused"]).last()

        if not session:
            return Response({"error": "❌ Ви ще не почали зміну! Використовуйте /start_work."}, status=400)

        session.end_time = now().astimezone(kyiv_tz)
        session.status = "ended"
        session.save()
        return Response({"message": "✅ Робоча зміна завершена!"})

class MyHours(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, year=None, month=None):
        today = now().astimezone(kyiv_tz)

        # Визначаємо поточний або вказаний місяць і рік
        if not year or not month:
            year, month = today.year, today.month

        # Визначаємо попередній місяць
        if month == 1:
            prev_year, prev_month = year - 1, 12
        else:
            prev_year, prev_month = year, month - 1

        # Отримуємо всі сесії за поточний місяць
        sessions = WorkSession.objects.filter(
            user=request.user, 
            start_time__year=year, 
            start_time__month=month
        )

        # Перевіряємо, чи є години за попередній місяць
        has_previous = WorkSession.objects.filter(
            user=request.user, 
            start_time__year=prev_year, 
            start_time__month=prev_month
        ).exists()

        if not sessions.exists():
            return Response({
                "error": "📊 У вас ще немає робочих годин у цьому місяці.",
                "has_previous": has_previous
            })

        total_work_time = timedelta()
        daily_data = defaultdict(timedelta)

        for session in sessions:
            actual_end_time = session.end_time if session.end_time else now().astimezone(kyiv_tz)
            work_duration = actual_end_time - session.start_time
            daily_data[session.start_time.date()] += work_duration
            total_work_time += work_duration

        total_hours, total_minutes = divmod(total_work_time.total_seconds() // 60, 60)

        formatted_days = [
            f"📅 {day.strftime('%d.%m.%Y')}: {int(daily.total_seconds() // 3600)} год {int((daily.total_seconds() % 3600) // 60)} хв"
            for day, daily in sorted(daily_data.items(), reverse=True)
        ]

        return Response({
            "summary": f"📆 **{today.strftime('%B %Y')}**\n🔹 Всього відпрацьовано: {int(total_hours)} год {int(total_minutes)} хв",
            "days": formatted_days,
            "has_previous": has_previous  # Оновлена перевірка
        })

class AdminReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "admin":
            return Response({"error": "🚫 У вас немає прав для перегляду звіту."}, status=403)

        sessions = WorkSession.objects.select_related("user").all()

        report_data = defaultdict(lambda: defaultdict(list))

        for session in sessions:
            start_date = session.start_time.strftime("%d.%m.%Y")  # Формат ДД.ММ.РРРР
            end_time = session.end_time.strftime("%H:%M") if session.end_time else "Ще триває"
            duration = session.end_time - session.start_time if session.end_time else now() - session.start_time
            hours, minutes = divmod(duration.total_seconds() // 60, 60)

            full_name = f"{session.user.first_name} {session.user.last_name}".strip()
            if not full_name or full_name == "None None":
                full_name = session.user.username  # Якщо ім'я відсутнє, використовуємо username

            report_data[full_name][start_date].append({
                "start": session.start_time.strftime("%H:%M"),
                "end": end_time,
                "hours": f"{int(hours)} год {int(minutes)} хв"
            })

        formatted_report = []
        for user, days in report_data.items():
            user_report = f"👤 **{user}**\n"
            # Сортуємо дні від новіших до старіших
            sorted_days = sorted(days.keys(), reverse=True)  
            for day in sorted_days:
                logs = days[day]
                total_duration = sum(
                    (session.end_time - session.start_time).total_seconds() if session.end_time else (now() - session.start_time).total_seconds()
                    for session in WorkSession.objects.filter(user__first_name=user.split()[0], start_time__date=datetime.strptime(day, "%d.%m.%Y"))
                )
                total_hours, total_minutes = divmod(total_duration // 60, 60)
                day_report = f"📅 {day} (🔹 {int(total_hours)} год {int(total_minutes)} хв)"
                shifts = "\n".join([f"  🕒 {log['start']} - {log['end']} ({log['hours']})" for log in logs])
                user_report += f"{day_report}\n{shifts}\n"
            formatted_report.append(user_report)

        return Response("\n".join(formatted_report))

class AvailableWorkers(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "admin":
            return Response({"error": "🚫 У вас немає прав."}, status=403)

        workers = User.objects.filter(worksession__isnull=False).distinct()
        return Response([{"id": worker.id, "name": f"{worker.first_name} {worker.last_name}".strip() or worker.username} for worker in workers])

class AvailableYears(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        if request.user.role != "admin":
            return Response({"error": "🚫 У вас немає прав."}, status=403)

        years = WorkSession.objects.filter(user_id=user_id).dates("start_time", "year").distinct()
        return Response([year.year for year in years])

class AvailableMonths(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id, year):
        if request.user.role != "admin":
            return Response({"error": "🚫 У вас немає прав."}, status=403)

        months = WorkSession.objects.filter(user_id=user_id, start_time__year=year).dates("start_time", "month").distinct()
        return Response([month.month for month in months])

class MonthlyReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id, year, month):
        if request.user.role != "admin":
            return Response({"error": "🚫 У вас немає прав для перегляду звіту."}, status=403)

        sessions = WorkSession.objects.filter(user_id=user_id, start_time__year=year, start_time__month=month)

        if not sessions.exists():
            return Response({"error": "📊 Немає даних за цей місяць."})

        total_work_time = timedelta()
        daily_data = defaultdict(list)

        for session in sessions:
            day = session.start_time.astimezone(kyiv_tz).strftime("%d.%m.%Y")

            # Визначаємо фактичний кінець роботи
            actual_end_time = session.end_time.astimezone(kyiv_tz) if session.end_time else None
            if session.pause_time and not session.resume_time:
                actual_end_time = session.pause_time.astimezone(kyiv_tz)

            # Рахуємо фактичний робочий час
            actual_work_time = timedelta()
            if actual_end_time:
                actual_work_time += (actual_end_time - session.start_time.astimezone(kyiv_tz))

            # Віднімаємо час паузи, якщо працівник повернувся до роботи
            if session.pause_time and session.resume_time:
                actual_work_time -= (session.resume_time.astimezone(kyiv_tz) - session.pause_time.astimezone(kyiv_tz))

            total_work_time += actual_work_time

            hours, minutes = divmod(actual_work_time.total_seconds() // 60, 60)
            daily_data[day].append(
                f"🕒 {session.start_time.astimezone(kyiv_tz).strftime('%H:%M')} - "
                f"{actual_end_time.strftime('%H:%M') if actual_end_time else 'Ще триває'} "
                f"({int(hours)} год {int(minutes)} хв)"
            )

        total_hours, total_minutes = divmod(total_work_time.total_seconds() // 60, 60)

        report = f"📆 **{month:02d}.{year}**\n🔹 Загальна кількість: {int(total_hours)} год {int(total_minutes)} хв\n\n"
        sorted_days = sorted(daily_data.keys(), reverse=True)
        for day in sorted_days:
            report += f"📅 {day}:\n" + "\n".join(daily_data[day]) + "\n"

        return Response({"report": report})