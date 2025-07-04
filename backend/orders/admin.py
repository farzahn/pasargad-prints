from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory, TrackingStatus


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'quantity', 'unit_price', 'total_price')
    readonly_fields = ('unit_price', 'total_price')


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    fields = ('status', 'notes', 'created_at', 'created_by')
    readonly_fields = ('created_at', 'created_by')


class TrackingStatusInline(admin.TabularInline):
    model = TrackingStatus
    extra = 0
    fields = ('tracking_number', 'carrier', 'status', 'status_details', 'status_date', 'location_city', 'location_state')
    readonly_fields = ('goshippo_object_created', 'goshippo_object_updated', 'created_at', 'updated_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'fulfillment_method', 'carrier', 'total_amount', 'created_at')
    list_filter = ('status', 'fulfillment_method', 'carrier', 'created_at')
    search_fields = ('order_number', 'user__email', 'shipping_email', 'tracking_number', 'shippo_transaction_id')
    ordering = ('-created_at',)
    inlines = [OrderItemInline, OrderStatusHistoryInline, TrackingStatusInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'fulfillment_method')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'tax_amount', 'shipping_cost', 'total_amount')
        }),
        ('Shipping Information', {
            'fields': ('shipping_name', 'shipping_email', 'shipping_phone', 
                      'shipping_address', 'shipping_city', 'shipping_state', 
                      'shipping_postal_code', 'shipping_country')
        }),
        ('Billing Information', {
            'fields': ('billing_name', 'billing_email', 'billing_address', 
                      'billing_city', 'billing_state', 'billing_postal_code', 
                      'billing_country'),
            'classes': ('collapse',)
        }),
        ('Tracking & Shipping', {
            'fields': ('tracking_number', 'carrier', 'service_level', 'estimated_delivery')
        }),
        ('Goshippo Integration', {
            'fields': ('goshippo_order_id', 'goshippo_transaction_id', 'goshippo_object_id', 
                      'goshippo_rate_id', 'goshippo_tracking_url', 'goshippo_label_url'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'shipped_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('order_number', 'created_at', 'updated_at')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'unit_price', 'total_price')
    list_filter = ('order__status', 'order__created_at')
    search_fields = ('order__order_number', 'product__name', 'product_name')
    ordering = ('-order__created_at',)


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'created_at', 'created_by')
    list_filter = ('status', 'created_at')
    search_fields = ('order__order_number', 'notes')
    ordering = ('-created_at',)


@admin.register(TrackingStatus)
class TrackingStatusAdmin(admin.ModelAdmin):
    list_display = ('order', 'tracking_number', 'carrier', 'status', 'status_date', 'location_city', 'location_state')
    list_filter = ('status', 'carrier', 'status_date', 'created_at')
    search_fields = ('order__order_number', 'tracking_number', 'status_details', 'goshippo_tracking_id')
    ordering = ('-status_date', '-created_at')
    readonly_fields = ('goshippo_object_created', 'goshippo_object_updated', 'created_at', 'updated_at')