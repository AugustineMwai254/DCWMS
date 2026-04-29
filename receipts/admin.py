from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from dcwms.admin import admin_site
from .models import Receipt

@admin.register(Receipt, site=admin_site)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ['receipt_code', 'farmer_link', 'warehouse_link', 'cereal_type', 'quantity_bags', 'issued_at', 'is_valid', 'qr_code_link']
    list_filter = ['is_valid', 'cereal_type', 'issued_at', 'warehouse__county']
    search_fields = ['receipt_code', 'farmer__username', 'farmer__first_name', 'farmer__last_name', 'warehouse__name']
    readonly_fields = ['receipt_number', 'receipt_code', 'security_hash', 'issued_at']
    ordering = ['-issued_at']
    actions = ['invalidate_receipts']

    fieldsets = (
        ('Receipt Details', {
            'fields': ('receipt_code', 'farmer', 'warehouse', 'cereal_type', 'quantity_bags')
        }),
        ('Security & Validation', {
            'fields': ('security_hash', 'is_valid', 'issued_at'),
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

    def qr_code_link(self, obj):
        url = reverse('receipts:qr_code', args=[obj.pk])
        return format_html('<a href="{}" target="_blank">View QR</a>', url)
    qr_code_link.short_description = 'QR Code'

    def invalidate_receipts(self, request, queryset):
        queryset.update(is_valid=False)
        self.message_user(request, f"Invalidated {queryset.count()} receipts.")
    invalidate_receipts.short_description = "Invalidate selected receipts"
