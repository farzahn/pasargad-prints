from django.contrib import admin
from .models import Wishlist, WishlistItem


class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0
    readonly_fields = ['created_at']
    raw_id_fields = ['product']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_key', 'total_items', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'session_key']
    inlines = [WishlistItemInline]
    readonly_fields = ['created_at', 'updated_at']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'wishlist', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['wishlist__user__email', 'product__name']
    raw_id_fields = ['wishlist', 'product']
    readonly_fields = ['created_at']
