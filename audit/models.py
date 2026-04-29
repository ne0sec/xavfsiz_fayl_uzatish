from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('login', 'Tizimga kirdi'),
        ('logout', 'Tizimdan chiqdi'),
        ('upload', 'Hujjat yukladi'),
        ('request', 'Hujjat so\'radi'),
        ('approve', 'Tasdiqladi'),
        ('reject', 'Rad etdi'),
        ('download', 'Hujjatni ochdi/yuklab oldi'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Foydalanuvchi")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="Bajarilgan amal")
    details = models.TextField(blank=True, verbose_name="Qo'shimcha ma'lumotlar")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Vaqt")

    def __str__(self):
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {self.user} | {self.get_action_display()}"