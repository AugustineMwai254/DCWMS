"""Warehouse URLs"""
from django.urls import path
from . import views

app_name = 'warehouses'

urlpatterns = [
    path('', views.warehouse_finder, name='finder'),
    path('<int:pk>/', views.warehouse_detail, name='detail'),
    path('create/', views.warehouse_create, name='create'),
    path('<int:pk>/edit/', views.warehouse_edit, name='edit'),
    path('my/', views.my_warehouses, name='my_warehouses'),
    path('<int:pk>/toggle/', views.warehouse_toggle_status, name='toggle_status'),
]
