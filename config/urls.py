from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/documents/upload/', permanent=False)),
    path('accounts/', include('django.contrib.auth.urls')),
    path('documents/', include('documents.urls')),
    path('accounts/', include('accounts.urls')),
    path('audit/', include('audit.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)