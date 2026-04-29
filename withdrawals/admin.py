from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from dcwms.admin import admin_site
from .models import Withdrawal

@admin.register(Withdrawal, site=admin_site)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ['withdrawal_ref_short', 'farmer_link', 'warehouse_link', 'bags_to_withdraw', 'mt_to_withdraw', 'scheduled_date', 'status', 'created_at']
    list_filter = ['status', 'scheduled_date', 'warehouse__county']
    search_fields = ['withdrawal_reference', 'farmer__username', 'farmer__first_name', 'farmer__last_name', 'warehouse__name']
    readonly_fields = ['withdrawal_reference', 'mt_to_withdraw', 'created_at', 'updated_at']
    ordering = ['-created_at']
    actions = ['approve_withdrawals', 'reject_withdrawals', 'mark_completed']

    fieldsets = (
        ('Withdrawal Details', {
            'fields': ('withdrawal_reference', 'farmer', 'warehouse', 'bags_to_withdraw', 'scheduled_date')
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

    def approve_withdrawals(self, request, queryset):
        queryset.filter(status='pending').update(status='approved')
        self.message_user(request, f"Approved {queryset.filter(status='approved').count()} withdrawals.")
    approve_withdrawals.short_description = "Approve selected pending withdrawals"

    def reject_withdrawals(self, request, queryset):
        queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, f"Rejected {queryset.filter(status='rejected').count()} withdrawals.")
    reject_withdrawals.short_description = "Reject selected pending withdrawals"

    def mark_completed(self, request, queryset):
        queryset.filter(status='approved').update(status='completed')
        self.message_user(request, f"Marked {queryset.filter(status='completed').count()} withdrawals as completed.")
    mark_completed.short_description = "Mark selected approved withdrawals as completed"
