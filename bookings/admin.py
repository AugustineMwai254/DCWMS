"""Bookings admin"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from dcwms.admin import admin_site
from .models import Booking

@admin.register(Booking, site=admin_site)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_ref_human', 'farmer_link', 'warehouse_link', 'cereal_type', 'quantity_bags', 'quantity_mt', 'status', 'created_at']
    list_filter = ['status', 'cereal_type', 'created_at', 'warehouse__county']
    search_fields = ['booking_reference', 'farmer__username', 'farmer__first_name', 'farmer__last_name', 'warehouse__name']
    readonly_fields = ['booking_reference', 'quantity_mt', 'created_at', 'updated_at']
    ordering = ['-created_at']
    actions = ['approve_bookings', 'reject_bookings', 'mark_completed']

    fieldsets = (
        ('Booking Details', {
            'fields': ('booking_reference', 'farmer', 'warehouse', 'cereal_type', 'quantity_bags')
        }),
        ('Status & Dates', {
            'fields': ('status', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def farmer_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.farmer.pk])
        return format_html('<a href="{}">{}</a>', url, obj.farmer.get_full_name())
    farmer_link.short_description = 'Farmer'

    def warehouse_link(self, obj):
        url = reverse('admin:warehouses_warehouse_change', args=[obj.warehouse.pk])
        return format_html('<a href="{}">{}</a>', url, obj.warehouse.name)
    warehouse_link.short_description = 'Warehouse'

    def approve_bookings(self, request, queryset):
        queryset.filter(status='pending').update(status='approved')
        self.message_user(request, f"Approved {queryset.filter(status='approved').count()} bookings.")
    approve_bookings.short_description = "Approve selected pending bookings"

    def reject_bookings(self, request, queryset):
        queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, f"Rejected {queryset.filter(status='rejected').count()} bookings.")
    reject_bookings.short_description = "Reject selected pending bookings"

    def mark_completed(self, request, queryset):
        queryset.filter(status='approved').update(status='completed')
        self.message_user(request, f"Marked {queryset.filter(status='completed').count()} bookings as completed.")
    mark_completed.short_description = "Mark selected approved bookings as completed"
