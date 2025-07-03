from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Address


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff', 'newsletter_subscription', 'created_at')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'newsletter_subscription', 'created_at')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-created_at',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone', 'date_of_birth', 'newsletter_subscription')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('email', 'first_name', 'last_name', 'phone', 'newsletter_subscription')
        }),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'address_type', 'street_address', 'city', 'state', 'postal_code', 'is_default')
    list_filter = ('address_type', 'is_default', 'country', 'state')
    search_fields = ('user__email', 'street_address', 'city', 'postal_code')
    ordering = ('-created_at',)