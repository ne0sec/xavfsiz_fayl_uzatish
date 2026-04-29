from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import AuditLog
from documents.models import Document
from sharing.models import DocumentShare

# 1. Tizimga kirish va chiqishni log qilish
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    AuditLog.objects.create(user=user, action='login', details=f"IP/Agent: {request.META.get('REMOTE_ADDR')}")

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user is not None:
        AuditLog.objects.create(user=user, action='logout', details="Sessiya yakunlandi")

# 2. Yangi hujjat yuklanganda log qilish
@receiver(post_save, sender=Document)
def log_document_upload(sender, instance, created, **kwargs):
    if created:
        AuditLog.objects.create(
            user=instance.owner, 
            action='upload', 
            details=f"Hujjat yuklandi: {instance.title} (Maxfiylik: {instance.privacy_level})"
        )

# 3. Hujjat ulashish so'rovlari va tasdiqlashlarni log qilish
@receiver(post_save, sender=DocumentShare)
def log_document_share_status(sender, instance, created, **kwargs):
    if created:
        AuditLog.objects.create(
            user=instance.receiver,
            action='request',
            details=f"Hujjat so'rovi yuborildi: {instance.document.title}"
        )
    else:
        if instance.status == 'approved':
            AuditLog.objects.create(user=instance.approver, action='approve', details=f"So'rov tasdiqlandi: {instance.document.title}")
        elif instance.status == 'rejected':
            AuditLog.objects.create(user=instance.approver, action='reject', details=f"So'rov rad etildi: {instance.document.title}")