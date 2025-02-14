from collections import defaultdict
from datetime import timedelta

from django.db.models import Sum
from django.utils.timezone import now

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token

from .models import WorkSession, User

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

        report_data = defaultdict(lambda: defaultdict(list))  # Групування по днях

        for session in sessions:
            start_date = session.start_time.date()
            end_time = session.end_time if session.end_time else now()
            duration = end_time - session.start_time

            hours, minutes = divmod(duration.total_seconds() // 60, 60)  # Отримуємо години та хвилини

            report_data[session.user.username][start_date].append({
                "start": session.start_time.strftime("%H:%M"),
                "end": session.end_time.strftime("%H:%M") if session.end_time else "Ще триває",
                "hours": f"{int(hours)} год {int(minutes)} хв"
            })

        formatted_report = []
        for user, days in report_data.items():
            user_report = f"👤 **{user}**\n"
            for day, logs in days.items():
                total_duration = sum(
                    (session.end_time - session.start_time).total_seconds() if session.end_time else (now() - session.start_time).total_seconds()
                    for session in WorkSession.objects.filter(user__username=user, start_time__date=day)
                )
                total_hours, total_minutes = divmod(total_duration // 60, 60)
                day_report = f"📅 {day} (🔹 {int(total_hours)} год {int(total_minutes)} хв)"
                shifts = "\n".join([f"  🕒 {log['start']} - {log['end']} ({log['hours']})" for log in logs])
                user_report += f"{day_report}\n{shifts}\n"
            formatted_report.append(user_report)

        return Response("\n".join(formatted_report))
