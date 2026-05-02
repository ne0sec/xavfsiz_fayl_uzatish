import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import HttpResponse, JsonResponse

from .models import Document
from accounts.models import CustomUser
from sharing.models import DocumentShare

@login_required
def dashboard(request):
    return render(request, 'documents/dashboard.html')

@login_required
def user_directory(request):
    """Foydalanuvchilarni qidirish va fayl yuborish uchun ro'yxat oynasi"""
    query = request.GET.get('q', '')
    if query:
        users = CustomUser.objects.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query),
            is_active=True
        ).exclude(id=request.user.id)
    else:
        users = CustomUser.objects.filter(is_active=True).exclude(id=request.user.id)
        
    return render(request, 'documents/users.html', {'users': users, 'query': query})

@login_required
def inbox(request):
    # 1. Men "Qabul qiluvchi" bo'lgan hujjatlar (Menga yuborilganlar)
    received_shares = DocumentShare.objects.filter(receiver=request.user).order_by('-created_at')
    
    # 2. Men "Tasdiqlovchi" (Director/Admin/Approver) bo'lgan va tasdiq kutayotgan so'rovlar
    if request.user.role in ['approver', 'admin', 'owner']:
        pending_approvals = DocumentShare.objects.filter(approver=request.user, status='pending').order_by('-created_at')
    else:
        pending_approvals = None
        
    return render(request, 'documents/inbox.html', {
        'received_shares': received_shares,
        'pending_approvals': pending_approvals
    })

@login_required
def upload_document(request):
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        is_e2ee = request.POST.get('is_e2ee') == 'true'

        title = request.POST.get('title')
        description = request.POST.get('description')
        privacy_level = request.POST.get('privacy_level')
        receiver_id = request.POST.get('receiver')
        approver_id = request.POST.get('approver')
        uploaded_file = request.FILES.get('file')

        try:
            receiver = CustomUser.objects.get(id=receiver_id) if receiver_id else None
            approver = CustomUser.objects.get(id=approver_id) if approver_id else None
        except CustomUser.DoesNotExist:
            if is_ajax:
                return JsonResponse({"status": "error", "message": "Foydalanuvchi topilmadi."}, status=400)
            messages.error(request, "Foydalanuvchi topilmadi.")
            return redirect('upload_document')

        # SHA-256 xeshini hisoblash (faylni o'qib)
        import hashlib
        file_data = uploaded_file.read()
        sha256_hash = hashlib.sha256(file_data).hexdigest()
        # Faylni boshiga qaytarish (keyin saqlash uchun)
        from django.core.files.uploadedfile import InMemoryUploadedFile
        import io
        uploaded_file.seek(0)

        document = Document.objects.create(
            owner=request.user,
            title=title,
            description=description,
            privacy_level=privacy_level,
            file=uploaded_file,
            sha256_hash=sha256_hash,
            original_filename=request.POST.get('original_filename', '')
        )

        if privacy_level == 'protected' and is_e2ee:
            share_1 = request.POST.get('share_1')
            share_2_enc = request.POST.get('share_2_enc')
            share_3_enc = request.POST.get('share_3_enc')

            if not share_3_enc:
                if is_ajax:
                    return JsonResponse({"status": "error", "message": "share_3 bo'sh keldi!"}, status=400)

            DocumentShare.objects.create(
                document=document,
                receiver=receiver,
                approver=approver,
                share_1=share_1,
                share_2=share_2_enc,
                share_3=share_3_enc,
                status='pending'
            )

            if is_ajax:
                messages.success(request, "Hujjat E2EE orqali muvaffaqiyatli shifrlanib, serverga saqlandi!")
                return JsonResponse({"status": "success", "message": "Uploaded via E2EE"})

        elif privacy_level == 'simple':
            DocumentShare.objects.create(
                document=document,
                receiver=receiver,
                approver=approver,
                status='approved'
            )
            messages.success(request, "Hujjat muvaffaqiyatli yuklandi.")
            return redirect('inbox')

    receivers = CustomUser.objects.filter(role='receiver').exclude(public_key__isnull=True).exclude(public_key__exact='')
    approvers = CustomUser.objects.filter(role='approver').exclude(public_key__isnull=True).exclude(public_key__exact='')

    context = {
        'receivers': receivers,
        'approvers': approvers,
    }
    return render(request, 'documents/upload.html', context)

@login_required
def approve_document(request, share_id):
    try:
        share = DocumentShare.objects.get(id=share_id, approver=request.user)
        
        if request.method == 'POST':
            re_encrypted_share = request.POST.get('re_encrypted_share_3')
            if re_encrypted_share:
                share.share_3 = re_encrypted_share 
                share.status = 'approved'
                share.save()
                messages.success(request, f'"{share.document.title}" hujjati tasdiqlandi. SSS ulushingiz qabul qiluvchiga xavfsiz uzatildi.')
                return JsonResponse({"status": "success"})
            return JsonResponse({"status": "error", "message": "Ma'lumot yetib kelmadi."}, status=400)

        receiver_pub_key = share.receiver.public_key
        return render(request, 'documents/approve.html', {
            'share': share,
            'receiver_pub_key': receiver_pub_key
        })
        
    except DocumentShare.DoesNotExist:
        messages.error(request, "So'rov topilmadi yoki sizga tegishli emas.")
        return redirect('inbox')

@login_required
def reject_document(request, share_id):
    try:
        share = DocumentShare.objects.get(id=share_id, approver=request.user)
        share.status = 'rejected'
        share.save()
        messages.error(request, f'"{share.document.title}" hujjati rad etildi.')
    except DocumentShare.DoesNotExist:
        messages.error(request, "So'rov topilmadi.")
    return redirect('inbox')

@login_required
def download_document(request, share_id):
    try:
        share = DocumentShare.objects.get(id=share_id, receiver=request.user)
        doc = share.document

        if doc.privacy_level == 'protected' and share.status != 'approved':
            messages.error(request, "Hujjat hali tasdiqlanmagan! Uni ochish uchun direktorning ulushi yetishmayapti.")
            return redirect('inbox')

        return render(request, 'documents/download.html', {
            'share': share,
            'doc': doc,
            'file_url': f"/documents/proxy-file/{share_id}/"
        })

    except Exception as e:
        messages.error(request, f"Xatolik yuz berdi: {str(e)}")
        return redirect('inbox')


@login_required
def proxy_file(request, share_id):
    """Backblaze B2 yoki lokal faylni server orqali brauzerga uzatadi (CORS muammosini hal qiladi)"""
    import requests as req_lib
    try:
        share = DocumentShare.objects.get(id=share_id, receiver=request.user)
        doc = share.document

        if doc.privacy_level == 'protected' and share.status != 'approved':
            return HttpResponse("Ruxsat yo'q", status=403)

        file_url = doc.file.url

        # Agar tashqi URL (Backblaze) bo'lsa — proxy qilamiz
        if file_url.startswith('http'):
            r = req_lib.get(file_url, timeout=30)
            response = HttpResponse(r.content, content_type='application/octet-stream')
        else:
            # Lokal fayl
            response = HttpResponse(doc.file.read(), content_type='application/octet-stream')

        response['Content-Disposition'] = f'attachment; filename="{doc.original_filename or "file.enc"}"'
        response['Access-Control-Allow-Origin'] = '*'
        return response

    except Exception as e:
        return HttpResponse(f"Xatolik: {str(e)}", status=500)

@login_required
def sss_demo(request):
    """(Kriptografik demo sahifasi - eski kodingizdan)"""
    return render(request, 'documents/sss_demo.html', {})