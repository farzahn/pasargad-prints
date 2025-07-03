from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory


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


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'fulfillment_method', 'total_amount', 'created_at')
    list_filter = ('status', 'fulfillment_method', 'created_at')
    search_fields = ('order_number', 'user__email', 'shipping_email', 'tracking_number')
    ordering = ('-created_at',)
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
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
        ('Tracking', {
            'fields': ('tracking_number', 'shipstation_order_id', 'estimated_delivery')
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