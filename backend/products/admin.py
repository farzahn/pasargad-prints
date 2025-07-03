from django.contrib import admin
from django.utils.html import mark_safe
from django.utils.safestring import SafeString
from .models import Category, Product, ProductImage, ProductReview


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'image_url', 'alt_text', 'is_main', 'image_preview')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image_url:
            return mark_safe(f'<img src="{obj.image_url}" style="max-height: 100px; max-width: 100px; object-fit: cover;">')
        elif obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-height: 100px; max-width: 100px; object-fit: cover;">')
        return '-'
    image_preview.short_description = 'Preview'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'products_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    
    def products_count(self, obj):
        return obj.products.count()
    products_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'price', 'stock_quantity', 'stock_status', 'is_active', 'is_featured', 'created_at')
    list_filter = ('category', 'is_active', 'is_featured', 'material', 'created_at')
    search_fields = ('name', 'sku', 'description')
    ordering = ('-created_at',)
    inlines = [ProductImageInline]
    list_editable = ('price', 'stock_quantity', 'is_active', 'is_featured')
    list_per_page = 20
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'sku')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'stock_quantity'),
            'description': 'Update stock quantity here. Changes will be reflected immediately on the frontend.'
        }),
        ('Product Details', {
            'fields': ('weight', 'dimensions', 'material', 'print_time')
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured'),
            'description': 'Active products are visible on the site. Featured products appear on the homepage.'
        }),
    )
    
    def stock_status(self, obj):
        if obj.stock_quantity == 0:
            return mark_safe('<span style="color: red;">⚠️ Out of Stock</span>')
        elif obj.stock_quantity < 10:
            return mark_safe(f'<span style="color: orange;">⚠️ Low Stock ({obj.stock_quantity})</span>')
        else:
            return mark_safe(f'<span style="color: green;">✓ In Stock ({obj.stock_quantity})</span>')
    stock_status.short_description = 'Stock Status'
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if 'stock_quantity' in form.changed_data:
            self.message_user(request, f'Stock updated for {obj.name}: {obj.stock_quantity} units')
    
    actions = ['make_featured', 'remove_featured', 'activate_products', 'deactivate_products']
    
    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} product(s) marked as featured.')
    make_featured.short_description = 'Mark selected products as featured'
    
    def remove_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} product(s) removed from featured.')
    remove_featured.short_description = 'Remove featured status'
    
    def activate_products(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} product(s) activated.')
    activate_products.short_description = 'Activate selected products'
    
    def deactivate_products(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} product(s) deactivated.')
    deactivate_products.short_description = 'Deactivate selected products'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image_preview', 'is_main', 'alt_text', 'image_source', 'created_at')
    list_filter = ('is_main', 'created_at')
    search_fields = ('product__name', 'alt_text')
    ordering = ('-created_at',)
    
    def image_preview(self, obj):
        if obj.image_url:
            return mark_safe(f'<img src="{obj.image_url}" style="max-height: 50px; max-width: 50px; object-fit: cover;">')
        elif obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-height: 50px; max-width: 50px; object-fit: cover;">')
        return '-'
    image_preview.short_description = 'Preview'
    
    def image_source(self, obj):
        if obj.image_url:
            return 'URL'
        elif obj.image:
            return 'Upload'
        return 'None'
    image_source.short_description = 'Source'


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'is_verified_purchase', 'created_at')
    list_filter = ('rating', 'is_verified_purchase', 'created_at')
    search_fields = ('product__name', 'user__email', 'review_text')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'product', 'is_verified_purchase')