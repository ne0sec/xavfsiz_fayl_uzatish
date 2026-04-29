from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('users/', views.user_directory, name='user_directory'),
    path('upload/', views.upload_document, name='upload'),
    path('inbox/', views.inbox, name='inbox'),
    
    # Hujjat amallari uchun yangi URL lar:
    path('approve/<int:share_id>/', views.approve_document, name='approve_document'),
    path('reject/<int:share_id>/', views.reject_document, name='reject_document'),
    path('download/<int:share_id>/', views.download_document, name='download_document'),
    path('sss-demo/', views.sss_demo, name='sss_demo'),
]