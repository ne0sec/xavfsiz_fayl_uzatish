from django.db import models
from django.conf import settings
from documents.models import Document

class DocumentShare(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Kutilmoqda'),
        ('approved', 'Tasdiqlandi'),
        ('rejected', 'Rad etildi'),
    )

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='shares', verbose_name="Hujjat")
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_shares', verbose_name="Qabul qiluvchi")
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='approved_shares', verbose_name="Tasdiqlovchi")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Holati")
    
    # Shamir ulushlari uchun maydonlar (hex formatda saqlaymiz)
    # Eslatma: Real tizimlarda ular bitta bazada saqlanmaydi, bu faqat akademik namoyish uchun!
    share_2 = models.TextField(blank=True, null=True)
    share_3 = models.TextField(blank=True, null=True)
    share_1 = models.TextField(blank=True, null=True, verbose_name="1-ulush (Baza uchun)")
    #share_2 = models.CharField(max_length=255, blank=True, null=True, verbose_name="2-ulush (Receiver uchun)")
    #share_3 = models.CharField(max_length=255, blank=True, null=True, verbose_name="3-ulush (Approver uchun)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.document.title} -> {self.receiver.username} ({self.get_status_display()})"