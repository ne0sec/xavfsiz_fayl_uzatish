from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # Foydalanuvchi faqat shu maydonlarni to'ldiradi, 
        # rol esa modeldagi default='receiver' bo'lib o'zi saqlanadi.
        fields = ('username', 'first_name', 'last_name')