from django.contrib import admin
from .models import ShippingRate, ShippingLabel, TrackingEvent


@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    list_display = ['order', 'carrier', 'service_level', 'amount', 'estimated_days', 'created_at']
    list_filter = ['carrier', 'service_level', 'created_at']
    search_fields = ['order__order_number', 'carrier', 'service_level']
    readonly_fields = ['goshippo_rate_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order', 'goshippo_rate_id')
        }),
        ('Shipping Details', {
            'fields': ('carrier', 'service_level', 'amount', 'currency', 'estimated_days')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ShippingLabel)
class ShippingLabelAdmin(admin.ModelAdmin):
    list_display = ['order', 'tracking_number', 'carrier', 'service_level', 'amount', 'status', 'created_at']
    list_filter = ['carrier', 'service_level', 'status', 'created_at']
    search_fields = ['order__order_number', 'tracking_number', 'carrier']
    readonly_fields = ['goshippo_transaction_id', 'goshippo_shipment_id', 'goshippo_rate_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order', 'goshippo_transaction_id', 'goshippo_shipment_id', 'goshippo_rate_id')
        }),
        ('Label Details', {
            'fields': ('label_url', 'tracking_number', 'carrier', 'service_level', 'status')
        }),
        ('Pricing', {
            'fields': ('amount', 'currency')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(TrackingEvent)
class TrackingEventAdmin(admin.ModelAdmin):
    list_display = ['order', 'tracking_number', 'status', 'status_date', 'location', 'created_at']
    list_filter = ['status', 'status_date', 'created_at']
    search_fields = ['order__order_number', 'tracking_number', 'status_details', 'location']
    readonly_fields = ['webhook_data', 'created_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order', 'tracking_number')
        }),
        ('Event Details', {
            'fields': ('status', 'status_details', 'status_date', 'location')
        }),
        ('Webhook Data', {
            'fields': ('webhook_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )