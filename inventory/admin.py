from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from dcwms.admin import admin_site
from .models import InventoryRecord, InventoryMovement

class InventoryMovementInline(admin.TabularInline):
    model = InventoryMovement
    extra = 0
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']

@admin.register(InventoryRecord, site=admin_site)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['farmer_link', 'warehouse_link', 'cereal_type', 'quantity_bags', 'remaining_bags', 'status', 'date_stored', 'last_movement']
    list_filter = ['status', 'cereal_type', 'date_stored', 'warehouse__county']
    search_fields = ['farmer__username', 'farmer__first_name', 'farmer__last_name', 'warehouse__name']
    readonly_fields = ['date_stored', 'last_updated']
    ordering = ['-date_stored']
    inlines = [InventoryMovementInline]
    actions = ['mark_stored', 'mark_withdrawn']

    fieldsets = (
        ('Inventory Details', {
            'fields': ('farmer', 'warehouse', 'cereal_type', 'quantity_bags', 'remaining_bags', 'status')
        }),
        ('Dates', {
            'fields': ('date_stored', 'created_at', 'updated_at'),
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

    def last_movement(self, obj):
        last_move = obj.movements.order_by('-timestamp').first()
        if last_move:
            return f"{last_move.movement_type} ({last_move.bags_moved} bags)"
        return "No movements"
    last_movement.short_description = 'Last Movement'

    def mark_stored(self, request, queryset):
        queryset.filter(status='pending').update(status='stored')
        self.message_user(request, f"Marked {queryset.filter(status='stored').count()} records as stored.")
    mark_stored.short_description = "Mark selected records as stored"

    def mark_withdrawn(self, request, queryset):
        queryset.filter(status='stored').update(status='withdrawn')
        self.message_user(request, f"Marked {queryset.filter(status='withdrawn').count()} records as withdrawn.")
    mark_withdrawn.short_description = "Mark selected records as withdrawn"

@admin.register(InventoryMovement, site=admin_site)
class MovementAdmin(admin.ModelAdmin):
    list_display = ['inventory_link', 'movement_type', 'bags_moved', 'timestamp']
    list_filter = ['movement_type', 'timestamp']
    search_fields = ['inventory__farmer__username', 'inventory__warehouse__name']
    readonly_fields = ['timestamp']

    def inventory_link(self, obj):
        url = reverse('admin:inventory_inventoryrecord_change', args=[obj.inventory.pk])
        return format_html('<a href="{}">Record #{}</a>', url, obj.inventory.pk)
    inventory_link.short_description = 'Inventory Record'
