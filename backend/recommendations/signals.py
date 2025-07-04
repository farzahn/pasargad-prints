from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from wishlist.models import WishlistItem
from orders.models import OrderItem
from .models import UserProductScore
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=WishlistItem)
def update_score_on_wishlist_add(sender, instance, created, **kwargs):
    """Update user product score when item is added to wishlist."""
    if created and instance.wishlist.user:
        try:
            score, _ = UserProductScore.objects.get_or_create(
                user=instance.wishlist.user,
                product=instance.product
            )
            score.wishlisted = True
            score.update_score()
        except Exception as e:
            logger.error(f"Error updating score on wishlist add: {str(e)}")


@receiver(post_delete, sender=WishlistItem)
def update_score_on_wishlist_remove(sender, instance, **kwargs):
    """Update user product score when item is removed from wishlist."""
    if instance.wishlist.user:
        try:
            score = UserProductScore.objects.filter(
                user=instance.wishlist.user,
                product=instance.product
            ).first()
            if score:
                score.wishlisted = False
                score.update_score()
        except Exception as e:
            logger.error(f"Error updating score on wishlist remove: {str(e)}")


@receiver(post_save, sender=OrderItem)
def update_score_on_purchase(sender, instance, created, **kwargs):
    """Update user product score when item is purchased."""
    if created and instance.order.user:
        try:
            score, _ = UserProductScore.objects.get_or_create(
                user=instance.order.user,
                product=instance.product
            )
            score.purchased = True
            score.update_score()
        except Exception as e:
            logger.error(f"Error updating score on purchase: {str(e)}")