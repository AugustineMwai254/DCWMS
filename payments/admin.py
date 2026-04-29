from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from dcwms.admin import admin_site
from .models import Payment


@admin.register(Payment, site=admin_site)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_ref', 'farmer_link', 'booking_link', 'amount_kes', 'payment_method', 'status', 'initiated_at']
    list_filter = ['status', 'payment_method', 'initiated_at']
    search_fields = ['payment_id', 'farmer__username', 'farmer__first_name', 'farmer__last_name', 'booking__booking_reference']
    readonly_fields = ['payment_id', 'mpesa_receipt_number', 'mpesa_transaction_id', 'callback_data', 'initiated_at', 'completed_at']
    ordering = ['-initiated_at']

    fieldsets = (
        ('Payment Details', {
            'fields': ('payment_id', 'booking', 'farmer', 'amount_kes', 'payment_method', 'status')
        }),
        ('MPesa Details', {
            'fields': ('mpesa_receipt_number', 'mpesa_transaction_id', 'mpesa_phone_number'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('initiated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Callback Data', {
            'fields': ('callback_data', 'error_message'),
            'classes': ('collapse',)
        }),
    )

    def farmer_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.farmer.pk])
        return format_html('<a href="{}">{}</a>', url, obj.farmer.get_full_name())
    farmer_link.short_description = 'Farmer'

    def booking_link(self, obj):
        url = reverse('admin:bookings_booking_change', args=[obj.booking.pk])
        return format_html('<a href="{}">{}</a>', url, obj.booking.booking_ref_human)
    booking_link.short_description = 'Booking'