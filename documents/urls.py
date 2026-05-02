from django.urls import path
from . import views

urlpatterns = [
    # Asosiy sahifalar
    path('dashboard/', views.dashboard, name='dashboard'),
    path('users/', views.user_directory, name='user_directory'),
    
    # Hujjat amallari
    path('upload/', views.upload_document, name='upload'),
    path('inbox/', views.inbox, name='inbox'),
    
    # E2EE amallari (Aynan shu yerda approve va download bog'lanadi)
    path('approve/<int:share_id>/', views.approve_document, name='approve_document'),
    path('reject/<int:share_id>/', views.reject_document, name='reject_document'),
    path('download/<int:share_id>/', views.download_document, name='download_document'),
    path('proxy-file/<int:share_id>/', views.proxy_file, name='proxy_file'),
    
    # Kriptografiya demosi (agar kerak bo'lsa)
    path('sss-demo/', views.sss_demo, name='sss_demo'),
]