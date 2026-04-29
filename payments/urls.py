from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('initiate/<int:booking_id>/', views.initiate_payment, name='initiate'),
    path('status/<str:payment_id>/', views.payment_status, name='status'),
    path('check-manual/<str:payment_id>/', views.manual_check_payment, name='check_manual'),
    path('check-status/<str:payment_id>/', views.check_payment_status, name='check_status'),
    path('history/', views.payment_history, name='history'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
]