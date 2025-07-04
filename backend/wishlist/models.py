from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product

User = get_user_model()


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'session_key']

    def __str__(self):
        if self.user:
            return f"Wishlist for {self.user.email}"
        return f"Guest Wishlist {self.session_key}"

    @property
    def total_items(self):
        return self.items.count()


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['wishlist', 'product']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} in {self.wishlist}"
