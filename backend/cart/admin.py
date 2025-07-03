from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ('product', 'quantity', 'total_price')
    readonly_fields = ('total_price',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('cart_owner', 'total_items', 'total_price', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__email', 'session_key')
    ordering = ('-updated_at',)
    inlines = [CartItemInline]
    
    def cart_owner(self, obj):
        if obj.user:
            return f"User: {obj.user.email}"
        return f"Guest: {obj.session_key[:8]}..."
    cart_owner.short_description = 'Owner'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'total_price', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('cart__user__email', 'product__name')
    ordering = ('-created_at',)