from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class ProductView(models.Model):
    """Track product views for recommendation engine."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='recommendation_product_views')
    session_key = models.CharField(max_length=40, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='views')
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['user', 'product']),
            models.Index(fields=['session_key', 'product']),
            models.Index(fields=['viewed_at']),
        ]

    def __str__(self):
        viewer = self.user.email if self.user else f"Session {self.session_key}"
        return f"{viewer} viewed {self.product.name}"


class ProductRelationship(models.Model):
    """Define relationships between products for recommendations."""
    RELATIONSHIP_TYPES = [
        ('similar', 'Similar Product'),
        ('complementary', 'Complementary Product'),
        ('bundle', 'Bundle Suggestion'),
        ('upgrade', 'Upgrade Option'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='relationships')
    related_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='related_to')
    relationship_type = models.CharField(max_length=20, choices=RELATIONSHIP_TYPES)
    strength = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(10.0)],
        help_text="Strength of relationship (0.1-10.0)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['product', 'related_product', 'relationship_type']
        ordering = ['-strength', 'relationship_type']

    def __str__(self):
        return f"{self.product.name} -> {self.related_product.name} ({self.relationship_type})"


class UserProductScore(models.Model):
    """Store user preference scores for products."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Recommendation score (0-100)"
    )
    views_count = models.PositiveIntegerField(default=0)
    purchased = models.BooleanField(default=False)
    wishlisted = models.BooleanField(default=False)
    last_interaction = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'product']
        ordering = ['-score', '-last_interaction']
        indexes = [
            models.Index(fields=['user', 'score']),
            models.Index(fields=['last_interaction']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.product.name}: {self.score}"

    def update_score(self):
        """Update recommendation score based on user interactions."""
        # Base score from views
        self.score = min(self.views_count * 10, 30)
        
        # Bonus for wishlist
        if self.wishlisted:
            self.score += 20
        
        # Bonus for purchase
        if self.purchased:
            self.score += 50
        
        # Ensure score is within bounds
        self.score = min(self.score, 100)
        self.save()
