from django.contrib import admin
from .models import ProductView, ProductRelationship, UserProductScore


@admin.register(ProductView)
class ProductViewAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_key', 'product', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['user__email', 'product__name', 'session_key']
    raw_id_fields = ['user', 'product']
    readonly_fields = ['viewed_at']
    date_hierarchy = 'viewed_at'


@admin.register(ProductRelationship)
class ProductRelationshipAdmin(admin.ModelAdmin):
    list_display = ['product', 'related_product', 'relationship_type', 'strength', 'created_at']
    list_filter = ['relationship_type', 'created_at']
    search_fields = ['product__name', 'related_product__name']
    raw_id_fields = ['product', 'related_product']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('product', 'related_product', 'relationship_type', 'strength')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserProductScore)
class UserProductScoreAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'score', 'views_count', 'purchased', 'wishlisted', 'last_interaction']
    list_filter = ['purchased', 'wishlisted', 'last_interaction']
    search_fields = ['user__email', 'product__name']
    raw_id_fields = ['user', 'product']
    readonly_fields = ['created_at', 'last_interaction']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'product', 'score')
        }),
        ('Interaction Data', {
            'fields': ('views_count', 'purchased', 'wishlisted')
        }),
        ('Timestamps', {
            'fields': ('last_interaction', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['update_scores']
    
    def update_scores(self, request, queryset):
        updated = 0
        for score in queryset:
            score.update_score()
            updated += 1
        self.message_user(request, f"{updated} scores updated successfully.")
    update_scores.short_description = "Update selected scores"
