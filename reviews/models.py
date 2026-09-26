from django.conf import settings
from django.db import models


class Review(models.Model):
    """
    Verified customer reviews for Businesses and Food Items with photo & business reply support (Section 28, 43).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    food_item = models.ForeignKey(
        'menu.FoodItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews'
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews'
    )
    business_rating = models.PositiveSmallIntegerField(default=5)
    food_rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField()
    photo_url = models.URLField(max_length=500, blank=True)
    photo = models.ImageField(upload_to='reviews/photos/', null=True, blank=True)
    is_verified_order = models.BooleanField(default=True)
    business_reply = models.TextField(blank=True)
    replied_at = models.DateTimeField(null=True, blank=True)
    is_reported = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.user.username} for {self.business.name} ({self.business_rating}★)"
