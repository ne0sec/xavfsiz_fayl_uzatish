from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/documents/upload/', permanent=False)), # Endi bosh sahifa upload ga boradi
    path('accounts/', include('django.contrib.auth.urls')),
    path('documents/', include('documents.urls')), # documents URL lari ulandi
    path('accounts/', include('accounts.urls')), # Ro'yxatdan o'tish uchun bizning url
    path('accounts/', include('django.contrib.auth.urls')), # Djangoning standart login/logout
    path('audit/', include('audit.urls')),
    
]