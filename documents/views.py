import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import HttpResponse
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .models import Document
from .crypto import encrypt_file_data, calculate_sha256
from .sss import make_shares, recover_secret
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
        # Qidiruv username, ism yoki familiya bo'yicha amalga oshadi
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
def upload_document(request):
    receivers = CustomUser.objects.filter(is_active=True).exclude(id=request.user.id)
    approvers = CustomUser.objects.filter(role__in=['approver', 'admin', 'owner']).exclude(id=request.user.id)
    
    # Qidiruv sahifasidan kelgan qabul qiluvchi ID sini tutib olamiz
    selected_receiver_id = request.GET.get('receiver', '')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        privacy_level = request.POST.get('privacy_level')
        receiver_id = request.POST.get('receiver')
        approver_id = request.POST.get('approver')
        uploaded_file = request.FILES.get('file')

        # Endi approver_id faqat "protected" bo'lganda shart bo'ladi
        if uploaded_file and receiver_id:
            
            # Xavfsizlik tekshiruvi: Himoyalangan fayl bo'lsa-yu, tasdiqlovchi tanlanmagan bo'lsa
            if privacy_level == 'protected' and not approver_id:
                messages.error(request, "Himoyalangan fayl uchun tasdiqlovchi tanlash shart!")
                return redirect('upload')

            file_data = uploaded_file.read()
            sha256_hash = calculate_sha256(file_data)
            key, nonce, ciphertext = encrypt_file_data(file_data)
            
            doc = Document.objects.create(
                title=title,
                description=description,
                privacy_level=privacy_level,
                sha256_hash=sha256_hash,
                owner=request.user
            )
            
            encrypted_content = nonce + ciphertext
            file_name = f"enc_{uploaded_file.name}"
            doc.file.save(file_name, ContentFile(encrypted_content))
            doc.save()

            receiver_user = CustomUser.objects.get(id=receiver_id)

            # MANTIQIY YECHIM:
            if privacy_level == 'protected':
                approver_user = CustomUser.objects.get(id=approver_id)
                status = 'pending'
                shares = make_shares(key, minimum=2, shares_count=3)
                share_1 = json.dumps(shares[0])
                share_2 = json.dumps(shares[1])
                share_3 = json.dumps(shares[2])
            else:
                # Oddiy fayl bo'lsa, DB xato bermasligi uchun yuboruvchining o'zini approver qilib belgilaymiz
                approver_user = request.user 
                status = 'approved'
                share_1 = key.hex()
                share_2 = ""
                share_3 = ""

            DocumentShare.objects.create(
                document=doc,
                receiver=receiver_user,
                approver=approver_user,
                share_1=share_1,
                share_2=share_2,
                share_3=share_3,
                status=status
            )
            
            messages.success(request, f'"{title}" muvaffaqiyatli saqlandi va uzatildi!')
            return redirect('upload')
            
    return render(request, 'documents/upload.html', {
        'receivers': receivers, 
        'approvers': approvers,
        'selected_receiver_id': selected_receiver_id # Shablon uchun uzatamiz
    })


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
def approve_document(request, share_id):
    """Tasdiqlovchi (Director) hujjatni tasdiqlaydi"""
    try:
        share = DocumentShare.objects.get(id=share_id, approver=request.user)
        share.status = 'approved'
        share.save()
        messages.success(request, f'"{share.document.title}" hujjatini ochishga ruxsat berdingiz (Sizning SSS ulushingiz taqdim etildi).')
    except DocumentShare.DoesNotExist:
        messages.error(request, "So'rov topilmadi yoki sizga tegishli emas.")
    return redirect('inbox')


@login_required
def reject_document(request, share_id):
    """Tasdiqlovchi (Director) hujjatni rad etadi"""
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
    """Qabul qiluvchi ulushlarni birlashtirib, AES kalitini tiklaydi va hujjatni deshifr qiladi"""
    try:
        share = DocumentShare.objects.get(id=share_id, receiver=request.user)
        doc = share.document

        if doc.privacy_level == 'protected' and share.status != 'approved':
            messages.error(request, "Hujjat hali tasdiqlanmagan! Uni ochish uchun direktorning ulushi yetishmayapti.")
            return redirect('inbox')

        # 1. AES kalitini tiklash
        if doc.privacy_level == 'protected':
            # Shamir algoritmi bo'yicha 2 ta ulushni olamiz
            share2 = tuple(json.loads(share.share_2)) # Receiver ulushi
            share3 = tuple(json.loads(share.share_3)) # Approver ulushi
            key = recover_secret([share2, share3])
        else:
            # Oddiy fayllar uchun
            key = bytes.fromhex(share.share_1)

        # 2. Shifrlangan faylni xotiraga o'qish
        with doc.file.open('rb') as f:
            file_data = f.read()

        # 3. Nonce va Ciphertext ni ajratish
        nonce = file_data[:12]
        ciphertext = file_data[12:]

        # 4. AES-256-GCM yordamida deshifr qilish
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        # ==========================================
        # 5. BUTUNLIKNI TEKSHIRISH (Integrity Check)
        # ==========================================
        decrypted_hash = calculate_sha256(plaintext)
        
        # 6. Foydalanuvchiga yuklab berish uchun HTTP Response tayyorlash
        response = HttpResponse(plaintext, content_type='application/octet-stream')
        original_name = doc.file.name.split('/')[-1].replace('enc_', '')
        response['Content-Disposition'] = f'attachment; filename="{original_name}"'

        # JS ushlashi uchun maxsus Cookie o'rnatamiz (10 soniya yashaydi)
        if decrypted_hash == doc.sha256_hash:
            response.set_cookie('hash_status', 'valid', max_age=10)
        else:
            response.set_cookie('hash_status', 'invalid', max_age=10)
        # ==========================================
        
        return response
        
    except Exception as e:
        messages.error(request, f"Deshifrlashda xatolik yuz berdi (Fayl buzilgan yoki kalit noto'g'ri): {str(e)}")
        return redirect('inbox')
    

@login_required
def sss_demo(request):
    result_key = None
    error_msg = None
    
    if request.method == 'POST':
        share1_input = request.POST.get('share1', '').strip()
        share2_input = request.POST.get('share2', '').strip()
        
        # 1 ta ulush bilan urinib ko'rish holati
        if share1_input and not share2_input:
            error_msg = "Kriptografik xatolik: Kalitni tiklash uchun 1 ta ulush yetarli emas! Tizim Shamir algoritmi bo'yicha kamida 2 ta ulush talab qiladi (t=2)."
        elif share2_input and not share1_input:
            error_msg = "Kriptografik xatolik: Kalitni tiklash uchun 1 ta ulush yetarli emas!"
        elif share1_input and share2_input:
            try:
                # JSON formatidagi matnni tuple'ga o'tkazamiz
                s1 = tuple(json.loads(share1_input))
                s2 = tuple(json.loads(share2_input))
                
                # Lagrange interpolyatsiyasi orqali kalitni tiklash
                recovered_bytes = recover_secret([s1, s2])
                result_key = recovered_bytes.hex()
            except Exception as e:
                error_msg = f"Ulushlar formati noto'g'ri kiritildi: {str(e)}"
        else:
            error_msg = "Iltimos, tekshirish uchun kamida bitta ulushni kiriting."
            
    return render(request, 'documents/sss_demo.html', {
        'result_key': result_key,
        'error_msg': error_msg
    })