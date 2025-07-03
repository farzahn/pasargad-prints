from django.contrib import admin
from .models import Payment, PaymentRefund, StripeWebhookEvent


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'user', 'status', 'payment_method', 'amount', 'currency', 'created_at')
    list_filter = ('status', 'payment_method', 'currency', 'created_at')
    search_fields = ('order__order_number', 'user__email', 'stripe_payment_intent_id', 'transaction_id')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('order', 'user', 'status', 'payment_method')
        }),
        ('Amount', {
            'fields': ('amount', 'currency')
        }),
        ('Stripe Details', {
            'fields': ('stripe_payment_intent_id', 'stripe_charge_id', 'stripe_customer_id'),
            'classes': ('collapse',)
        }),
        ('Transaction Details', {
            'fields': ('transaction_id', 'gateway_response'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'gateway_response')


@admin.register(PaymentRefund)
class PaymentRefundAdmin(admin.ModelAdmin):
    list_display = ('id', 'payment', 'amount', 'status', 'reason', 'created_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('payment__order__order_number', 'payment__user__email', 'stripe_refund_id', 'reason')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Refund Information', {
            'fields': ('payment', 'amount', 'reason', 'status')
        }),
        ('Stripe Details', {
            'fields': ('stripe_refund_id',),
            'classes': ('collapse',)
        }),
        ('Transaction Details', {
            'fields': ('transaction_id', 'gateway_response'),
            'classes': ('collapse',)
        }),
        ('Administrative', {
            'fields': ('created_by', 'created_at', 'updated_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'gateway_response')


@admin.register(StripeWebhookEvent)
class StripeWebhookEventAdmin(admin.ModelAdmin):
    list_display = ('stripe_event_id', 'event_type', 'processed', 'created_at', 'processed_at')
    list_filter = ('event_type', 'processed', 'created_at')
    search_fields = ('stripe_event_id', 'event_type', 'error_message')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Event Information', {
            'fields': ('stripe_event_id', 'event_type', 'processed')
        }),
        ('Event Data', {
            'fields': ('data',),
            'classes': ('collapse',)
        }),
        ('Processing', {
            'fields': ('error_message', 'created_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('stripe_event_id', 'event_type', 'data', 'created_at', 'processed_at')