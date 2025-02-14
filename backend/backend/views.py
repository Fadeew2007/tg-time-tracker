from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now
from .models import WorkSession

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
