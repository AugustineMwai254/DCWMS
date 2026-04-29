"""Receipts URLs"""
from django.urls import path
from . import views

app_name = 'receipts'

urlpatterns = [
    path('', views.receipt_list, name='list'),
    path('<int:pk>/', views.receipt_detail, name='detail'),
    path('<int:pk>/print/', views.receipt_print, name='print'),
    path('<int:pk>/qr/', views.receipt_qr_code, name='qr_code'),
    path('verify/', views.verify_receipt, name='verify'),
]
