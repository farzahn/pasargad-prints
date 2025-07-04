from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    PageView, UserBehavior, ProductView, CartAbandonment,
    Conversion, ABTestExperiment, ABTestParticipant, Report
)


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ['page_url', 'user', 'session_id', 'device_type', 'browser', 'timestamp']
    list_filter = ['device_type', 'browser', 'timestamp', 'country']
    search_fields = ['page_url', 'user__username', 'user__email', 'session_id']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(UserBehavior)
class UserBehaviorAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'event_name', 'user', 'session_id', 'page_url', 'timestamp']
    list_filter = ['event_type', 'timestamp']
    search_fields = ['event_name', 'user__username', 'user__email', 'session_id', 'page_url']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(ProductView)
class ProductViewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'session_id', 'view_duration', 'source', 'timestamp']
    list_filter = ['source', 'timestamp']
    search_fields = ['product__name', 'user__username', 'user__email', 'session_id']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'product')


@admin.register(CartAbandonment)
class CartAbandonmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'cart_value', 'abandoned_at', 'recovered', 'email_sent', 'recovery_link']
    list_filter = ['recovered', 'email_sent', 'abandoned_at']
    search_fields = ['user__username', 'user__email', 'session_id']
    readonly_fields = ['abandoned_at', 'recovered_at']
    date_hierarchy = 'abandoned_at'
    actions = ['send_recovery_email', 'mark_as_recovered']
    
    def recovery_link(self, obj):
        if obj.recovery_order:
            url = reverse('admin:orders_order_change', args=[obj.recovery_order.id])
            return format_html('<a href="{}">Order #{}</a>', url, obj.recovery_order.order_number)
        return '-'
    recovery_link.short_description = 'Recovery Order'
    
    def send_recovery_email(self, request, queryset):
        count = 0
        for abandonment in queryset.filter(email_sent=False, user__isnull=False):
            # Implement email sending logic here
            abandonment.email_sent = True
            abandonment.save()
            count += 1
        self.message_user(request, f'Recovery emails sent to {count} customers.')
    send_recovery_email.short_description = 'Send recovery emails'
    
    def mark_as_recovered(self, request, queryset):
        count = queryset.filter(recovered=False).update(recovered=True)
        self.message_user(request, f'Marked {count} cart abandonments as recovered.')
    mark_as_recovered.short_description = 'Mark as recovered'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'recovery_order')


@admin.register(Conversion)
class ConversionAdmin(admin.ModelAdmin):
    list_display = ['order', 'user', 'conversion_value', 'source', 'medium', 'campaign', 'timestamp']
    list_filter = ['source', 'medium', 'campaign', 'timestamp']
    search_fields = ['order__order_number', 'user__username', 'user__email', 'session_id']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'order')


@admin.register(ABTestExperiment)
class ABTestExperimentAdmin(admin.ModelAdmin):
    list_display = ['name', 'feature', 'is_active', 'start_date', 'end_date', 'traffic_percentage', 'participant_count']
    list_filter = ['is_active', 'feature', 'start_date']
    search_fields = ['name', 'feature', 'description']
    readonly_fields = ['created_at', 'updated_at', 'participant_count']
    date_hierarchy = 'start_date'
    actions = ['activate_experiments', 'deactivate_experiments']
    
    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = 'Participants'
    
    def activate_experiments(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'Activated {count} experiments.')
    activate_experiments.short_description = 'Activate selected experiments'
    
    def deactivate_experiments(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'Deactivated {count} experiments.')
    deactivate_experiments.short_description = 'Deactivate selected experiments'


class ABTestParticipantInline(admin.TabularInline):
    model = ABTestParticipant
    extra = 0
    readonly_fields = ['enrolled_at']
    fields = ['user', 'session_id', 'variant', 'converted', 'conversion_value', 'enrolled_at']


@admin.register(ABTestParticipant)
class ABTestParticipantAdmin(admin.ModelAdmin):
    list_display = ['experiment', 'user', 'variant', 'converted', 'conversion_value', 'enrolled_at']
    list_filter = ['experiment', 'variant', 'converted', 'enrolled_at']
    search_fields = ['experiment__name', 'user__username', 'user__email', 'session_id']
    readonly_fields = ['enrolled_at']
    date_hierarchy = 'enrolled_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('experiment', 'user')


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'generated_by', 'generated_at', 'download_link']
    list_filter = ['report_type', 'generated_at']
    search_fields = ['name', 'generated_by__username']
    readonly_fields = ['generated_at', 'download_link']
    date_hierarchy = 'generated_at'
    
    def download_link(self, obj):
        if obj.file_path:
            return format_html('<a href="{}" target="_blank">Download PDF</a>', obj.file_path.url)
        return '-'
    download_link.short_description = 'Download'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('generated_by')


# Add the ABTestParticipantInline to ABTestExperimentAdmin
ABTestExperimentAdmin.inlines = [ABTestParticipantInline]
