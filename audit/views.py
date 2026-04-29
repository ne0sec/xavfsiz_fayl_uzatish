from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import AuditLog

@login_required
def audit_log_view(request):
    # Faqat admin roli borlar yoki superuserlar ko'ra oladi
    if request.user.role != 'admin' and not request.user.is_superuser:
        messages.error(request, "Xatolik: Sizda Audit jurnalini ko'rish uchun huquq yo'q!")
        return redirect('dashboard')
        
    # Barcha loglarni eng yangisi birinchi turadigan qilib olamiz
    logs = AuditLog.objects.all().order_by('-timestamp')
    
    return render(request, 'audit/audit_log.html', {'logs': logs})