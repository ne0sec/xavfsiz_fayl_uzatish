from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CustomUserCreationForm

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # 1. Hali bazaga saqlamay turamiz
            user = form.save(commit=False)
            
            # 2. Frontend'dan kelgan E2EE kalitlarni ushlab olamiz
            public_key = request.POST.get('public_key')
            encrypted_private_key = request.POST.get('encrypted_private_key')
            
            # 3. Kalitlarni foydalanuvchi ob'ektiga biriktiramiz
            if public_key and encrypted_private_key:
                user.public_key = public_key
                user.encrypted_private_key = encrypted_private_key
            
            # 4. Endi foydalanuvchini bazaga to'liq saqlaymiz
            user.save()
            
            messages.success(request, "Muvaffaqiyatli ro'yxatdan o'tdingiz! E2EE kalitlari muvaffaqiyatli yaratildi. Tizimga kirishingiz mumkin.")
            return redirect('login')
    else:
        form = CustomUserCreationForm()
        
    return render(request, 'registration/register.html', {'form': form})