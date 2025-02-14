from collections import defaultdict
from datetime import datetime, timedelta

from django.db.models import Count, Sum
from django.utils.timezone import now

from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User, WorkSession

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
        session = WorkSession.objects.create(user=user, start_time=now(), status='active')
        return Response({"message": "Робота розпочата!", "session_id": session.id})

class PauseWork(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session = WorkSession.objects.filter(user=request.user, status='active').last()
        if session:
            session.pause_time = now()
            session.status = 'paused'
            session.save()
            return Response({"message": "Робота поставлена на паузу!"})
        return Response({"error": "Немає активної сесії."}, status=400)

class ResumeWork(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session = WorkSession.objects.filter(user=request.user, status='paused').last()
        if session:
            session.resume_time = now()
            session.status = 'active'
            session.save()
            return Response({"message": "Робота відновлена!"})
        return Response({"error": "Немає сесії на паузі."}, status=400)

class StopWork(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session = WorkSession.objects.filter(user=request.user, status='active').last()
        if session:
            session.end_time = now()
            session.status = 'ended'
            session.save()
            return Response({"message": "Робоча зміна завершена!"})
        return Response({"error": "Немає активної сесії."}, status=400)

class MyHours(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = WorkSession.objects.filter(user=request.user).values()
        return Response(list(sessions))

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

        # Формуємо структуру для відображення за днями
        daily_data = defaultdict(list)

        for session in sessions:
            day = session.start_time.strftime("%d.%m.%Y")  # Формат ДД.ММ.РРРР

            # Рахуємо реальний робочий час (віднімаючи паузи)
            actual_work_time = timedelta()
            if session.end_time:
                actual_work_time += (session.end_time - session.start_time)

            # Віднімаємо паузи, якщо вони були
            if session.pause_time and session.resume_time:
                actual_work_time -= (session.resume_time - session.pause_time)

            total_work_time += actual_work_time

            hours, minutes = divmod(actual_work_time.total_seconds() // 60, 60)
            daily_data[day].append(
                f"🕒 {session.start_time.strftime('%H:%M')} - {session.end_time.strftime('%H:%M') if session.end_time else 'Ще триває'} "
                f"({int(hours)} год {int(minutes)} хв)"
            )

        # Загальна кількість годин за місяць
        total_hours, total_minutes = divmod(total_work_time.total_seconds() // 60, 60)

        # Форматуємо звіт у вигляді тексту
        report = f"📆 **{month:02d}.{year}**\n🔹 Загальна кількість: {int(total_hours)} год {int(total_minutes)} хв\n\n"

        # Сортуємо дні від новіших до старіших
        sorted_days = sorted(daily_data.keys(), reverse=True)
        for day in sorted_days:
            report += f"📅 {day}:\n" + "\n".join(daily_data[day]) + "\n"

        return Response({"report": report})