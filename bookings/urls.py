"""Bookings URLs"""
from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('', views.booking_list, name='list'),
    path('create/<int:warehouse_pk>/', views.create_booking, name='create'),
    path('<int:pk>/', views.booking_detail, name='detail'),
    path('<int:pk>/approve/', views.approve_booking, name='approve'),
    path('<int:pk>/cancel/', views.cancel_booking, name='cancel'),
    # AJAX endpoints for dynamic dashboard
    path('ajax/quick-approve/', views.quick_approve_booking, name='quick_approve'),
    path('ajax/quick-reject/', views.quick_reject_booking, name='quick_reject'),
    path('ajax/pending-count/', views.get_pending_bookings_count, name='pending_count'),
    path('ajax/recent-bookings/', views.get_recent_bookings, name='recent_bookings'),
]
