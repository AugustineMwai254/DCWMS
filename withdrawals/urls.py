"""Withdrawals URLs"""
from django.urls import path
from . import views

app_name = 'withdrawals'

urlpatterns = [
    path('', views.withdrawal_list, name='list'),
    path('schedule/<int:inventory_pk>/', views.schedule_withdrawal, name='schedule'),
    path('<int:pk>/', views.withdrawal_detail, name='detail'),
    path('<int:pk>/process/', views.process_withdrawal, name='process'),
    # AJAX endpoints for operator dashboard
    path('ajax/<int:pk>/accept/', views.accept_withdrawal_ajax, name='ajax_accept'),
    path('ajax/<int:pk>/approve/', views.approve_withdrawal_ajax, name='ajax_approve'),
    path('ajax/<int:pk>/complete/', views.complete_withdrawal_ajax, name='ajax_complete'),
    path('ajax/<int:pk>/reject/', views.reject_withdrawal_ajax, name='ajax_reject'),
]
