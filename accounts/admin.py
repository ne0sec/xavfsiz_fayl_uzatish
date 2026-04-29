from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    # 1. Ro'yxatda (sen tashlagan rasmdagi jadvalda) ko'rinadigan ustunlar
    list_display = UserAdmin.list_display + ('role',)
    
    # 2. Foydalanuvchi profiliga kirganda (tahrirlashda) ko'rinadigan maydonlar
    fieldsets = UserAdmin.fieldsets + (
        ('Rol va Huquqlar', {'fields': ('role',)}),
    )

admin.site.register(CustomUser, CustomUserAdmin)