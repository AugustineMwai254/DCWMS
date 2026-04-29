"""Admin registrations for all DCWMS models"""
# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from dcwms.admin import admin_site
from accounts.models import User, FarmerProfile, OperatorProfile

class FarmerProfileInline(admin.StackedInline):
    model = FarmerProfile
    can_delete = False
    verbose_name_plural = 'Farmer Profile'
    fk_name = 'user'

class OperatorProfileInline(admin.StackedInline):
    model = OperatorProfile
    can_delete = False
    verbose_name_plural = 'Operator Profile'
    fk_name = 'user'

@admin.register(User, site=admin_site)
class DCWMSUserAdmin(UserAdmin):
    list_display = ['username', 'get_full_name', 'email', 'role', 'county', 'phone_number', 'is_verified', 'is_active', 'created_at']
    list_filter = ['role', 'county', 'is_active', 'is_verified', 'created_at']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'national_id']
    ordering = ['-created_at']
    actions = ['verify_users', 'deactivate_users']

    fieldsets = UserAdmin.fieldsets + (
        ('DCWMS Fields', {
            'fields': ('role', 'phone_number', 'national_id', 'county', 'sub_county', 'village', 'is_verified'),
            'classes': ('collapse',)
        }),
    )

    def get_inlines(self, request, obj):
        if obj:
            if obj.is_farmer:
                return [FarmerProfileInline]
            elif obj.is_operator:
                return [OperatorProfileInline]
        return []

    def verify_users(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, f"Verified {queryset.count()} users.")
    verify_users.short_description = "Mark selected users as verified"

    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {queryset.count()} users.")
    deactivate_users.short_description = "Deactivate selected users"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('farmer_profile', 'operator_profile')

@admin.register(FarmerProfile, site=admin_site)
class FarmerProfileAdmin(admin.ModelAdmin):
    list_display = ['user_link', 'farm_size_acres', 'main_crop', 'cooperative_name', 'annual_production_bags']
    list_filter = ['main_crop', 'cooperative_name']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'cooperative_name']
    readonly_fields = ['user']

    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name())
    user_link.short_description = 'User'

@admin.register(OperatorProfile, site=admin_site)
class OperatorProfileAdmin(admin.ModelAdmin):
    list_display = ['user_link', 'company_name', 'assigned_county', 'business_license']
    list_filter = ['assigned_county']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'company_name']
    readonly_fields = ['user']

    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name())
    user_link.short_description = 'User'
