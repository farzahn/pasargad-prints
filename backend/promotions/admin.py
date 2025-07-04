from django.contrib import admin
from .models import PromotionCode, PromotionCodeUsage, Campaign


class PromotionCodeUsageInline(admin.TabularInline):
    model = PromotionCodeUsage
    extra = 0
    readonly_fields = ['user', 'order', 'discount_amount', 'used_at']
    can_delete = False


@admin.register(PromotionCode)
class PromotionCodeAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'description', 'discount_type', 'discount_value',
        'usage_type', 'is_active', 'valid_from', 'valid_until', 'usage_count'
    ]
    list_filter = ['discount_type', 'usage_type', 'is_active', 'created_at']
    search_fields = ['code', 'description']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    inlines = [PromotionCodeUsageInline]
    filter_horizontal = ['applicable_products', 'applicable_categories']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'description', 'is_active')
        }),
        ('Discount Settings', {
            'fields': ('discount_type', 'discount_value', 'minimum_order_amount')
        }),
        ('Usage Settings', {
            'fields': ('usage_type', 'usage_limit', 'usage_limit_per_user')
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Applicability', {
            'fields': (
                'applicable_to_all', 'applicable_products', 'applicable_categories'
            )
        }),
        ('Restrictions', {
            'fields': ('first_order_only', 'logged_in_only')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def usage_count(self, obj):
        return obj.uses.count()
    usage_count.short_description = 'Times Used'
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PromotionCodeUsage)
class PromotionCodeUsageAdmin(admin.ModelAdmin):
    list_display = ['promotion_code', 'user', 'order', 'discount_amount', 'used_at']
    list_filter = ['used_at', 'promotion_code']
    search_fields = ['promotion_code__code', 'user__email', 'order__order_number']
    readonly_fields = ['promotion_code', 'user', 'order', 'discount_amount', 'used_at']
    date_hierarchy = 'used_at'
    
    def has_add_permission(self, request):
        return False  # Prevent manual creation
    
    def has_delete_permission(self, request, obj=None):
        return False  # Prevent deletion


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_active', 'promotion_count', 'is_running']
    list_filter = ['is_active', 'start_date', 'end_date']
    search_fields = ['name', 'description']
    filter_horizontal = ['promotion_codes']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Campaign Period', {
            'fields': ('start_date', 'end_date')
        }),
        ('Promotion Codes', {
            'fields': ('promotion_codes',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def promotion_count(self, obj):
        return obj.promotion_codes.count()
    promotion_count.short_description = 'Promotions'
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
