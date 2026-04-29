"""Accounts URLs"""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/farmer/', views.register_farmer, name='register_farmer'),
    path('register/operator/', views.register_operator, name='register_operator'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
]
