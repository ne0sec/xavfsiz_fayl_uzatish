from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # Topshiriqdagi 4 ta rolni belgilab olamiz
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('owner', 'Hujjat Egasi'),
        ('receiver', 'Qabul Qiluvchi'),
        ('approver', 'Tasdiqlovchi'),
    )
    
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='receiver',
        verbose_name="Foydalanuvchi roli"
    )

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"