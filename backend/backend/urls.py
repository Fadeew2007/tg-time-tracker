from django.contrib import admin
from django.http import JsonResponse
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import StartWork, PauseWork, ResumeWork, StopWork, MyHours

def home(request):
    return JsonResponse({"message": "API is working!"})

urlpatterns = [
    path("", home, name="home"),  # Головна сторінка
    path("admin/", admin.site.urls),
    path("api/start_work/", StartWork.as_view(), name="start_work"),
    path("api/pause_work/", PauseWork.as_view(), name="pause_work"),
    path("api/resume_work/", ResumeWork.as_view(), name="resume_work"),
    path("api/stop_work/", StopWork.as_view(), name="stop_work"),
    path("api/my_hours/", MyHours.as_view(), name="my_hours"),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
