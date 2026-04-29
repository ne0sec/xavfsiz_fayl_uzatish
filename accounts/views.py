from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CustomUserCreationForm

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Muvaffaqiyatli ro'yxatdan o'tdingiz! Tizimga kirishingiz mumkin. Rollar admin tomonidan tasdiqlanadi.")
            return redirect('login')
    else:
        form = CustomUserCreationForm()
        
    return render(request, 'registration/register.html', {'form': form})