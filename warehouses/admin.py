"""Warehouses admin"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from dcwms.admin import admin_site
from .models import Warehouse, WarehouseImage

class WarehouseImageInline(admin.TabularInline):
    model = WarehouseImage
    extra = 0
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.image.url)
        return "No image"
    image_preview.short_description = 'Preview'

@admin.register(Warehouse, site=admin_site)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'operator_link', 'county', 'sub_county', 'total_capacity_mt', 'available_capacity_mt', 'utilization_percent_display', 'certification_status', 'is_active']
    list_filter = ['county', 'certification_status', 'storage_type', 'is_active', 'has_pest_control', 'has_security']
    search_fields = ['name', 'county', 'sub_county', 'operator__username', 'operator__first_name', 'operator__last_name']
    readonly_fields = ['registration_number', 'created_at', 'updated_at', 'utilization_percent']
    ordering = ['-created_at']
    actions = ['activate_warehouses', 'deactivate_warehouses', 'certify_warehouses']
    inlines = [WarehouseImageInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('operator', 'name', 'registration_number', 'county', 'sub_county', 'village', 'physical_address')
        }),
        ('Capacity & Storage', {
            'fields': ('total_capacity_mt', 'available_capacity_mt', 'storage_type'),
            'classes': ('collapse',)
        }),
        ('Certification', {
            'fields': ('certification_status', 'certification_expiry'),
            'classes': ('collapse',)
        }),
        ('Features', {
            'fields': ('has_pest_control', 'has_moisture_control', 'has_security', 'has_fumigation', 'accepts_wrs'),
            'classes': ('collapse',)
        }),
        ('Location', {
            'fields': ('latitude', 'longitude'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def operator_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.operator.pk])
        return format_html('<a href="{}">{}</a>', url, obj.operator.get_full_name())
    operator_link.short_description = 'Operator'

    def utilization_percent_display(self, obj):
        percent = obj.utilization_percent
        color = 'green' if percent < 60 else 'orange' if percent < 85 else 'red'
        return format_html('<span style="color: {};">{}%</span>', color, percent)
    utilization_percent_display.short_description = 'Utilization'

    def activate_warehouses(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"Activated {queryset.count()} warehouses.")
    activate_warehouses.short_description = "Activate selected warehouses"

    def deactivate_warehouses(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {queryset.count()} warehouses.")
    deactivate_warehouses.short_description = "Deactivate selected warehouses"

    def certify_warehouses(self, request, queryset):
        queryset.filter(certification_status__in=['pending', 'none']).update(certification_status='wrsc')
        self.message_user(request, f"Certified {queryset.filter(certification_status='wrsc').count()} warehouses.")
    certify_warehouses.short_description = "Mark selected warehouses as WRSC certified"

@admin.register(WarehouseImage, site=admin_site)
class WarehouseImageAdmin(admin.ModelAdmin):
    list_display = ['warehouse_link', 'image_preview', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['warehouse__name']

    def warehouse_link(self, obj):
        url = reverse('admin:warehouses_warehouse_change', args=[obj.warehouse.pk])
        return format_html('<a href="{}">{}</a>', url, obj.warehouse.name)
    warehouse_link.short_description = 'Warehouse'

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.image.url)
        return "No image"
    image_preview.short_description = 'Preview'
