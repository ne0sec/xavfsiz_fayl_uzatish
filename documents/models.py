from django.db import models
from django.conf import settings

class Document(models.Model):
    PRIVACY_CHOICES = (
        ('simple', 'Oddiy'),
        ('protected', 'Himoyalangan'),
    )
    
    title = models.CharField(max_length=255, verbose_name="Hujjat nomi")
    description = models.TextField(blank=True, verbose_name="Tavsifi")
    file = models.FileField(upload_to='encrypted_docs/', verbose_name="Shifrlangan fayl")
    sha256_hash = models.CharField(max_length=64, verbose_name="SHA-256 Xesh")
    privacy_level = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='simple', verbose_name="Maxfiylik darajasi")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents', verbose_name="Hujjat egasi")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.get_privacy_level_display()})"