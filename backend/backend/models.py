from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import datetime, timedelta

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('worker', 'Worker'),
    ]

    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='worker')
    first_name = models.CharField(max_length=100, blank=True, null=True)  # Додаємо ім'я
    last_name = models.CharField(max_length=100, blank=True, null=True)  # Додаємо прізвище

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})" if self.first_name and self.last_name else self.username

class WorkSession(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('ended', 'Ended'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    pause_time = models.DateTimeField(null=True, blank=True)
    resume_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return f"{self.user.username} - {self.status}"

class WorkPause(models.Model):
    session = models.ForeignKey(WorkSession, on_delete=models.CASCADE, related_name="pauses")
    pause_time = models.DateTimeField()
    resume_time = models.DateTimeField(null=True, blank=True)

    def duration(self):
        """Повертає тривалість паузи"""
        if self.resume_time:
            return self.resume_time - self.pause_time
        return timedelta(0)  # Якщо пауза ще не завершена