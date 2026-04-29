"""
DCWMS Main URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import landing_page
from .admin import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),
    path('', landing_page, name='home'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('warehouses/', include('warehouses.urls', namespace='warehouses')),
    path('bookings/', include('bookings.urls', namespace='bookings')),
    path('receipts/', include('receipts.urls', namespace='receipts')),
    path('inventory/', include('inventory.urls', namespace='inventory')),
    path('withdrawals/', include('withdrawals.urls', namespace='withdrawals')),
    path('reports/', include('reports.urls', namespace='reports')),
    path('payments/', include('payments.urls', namespace='payments')),
    path('dashboard/', include('accounts.dashboard_urls', namespace='dashboard')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
