from decimal import Decimal
from django.conf import settings
from django.db import models


class UserPreference(models.Model):
    """
    Stores customer taste profile for Tasty AI Recommendations & Smart Meal Builder (Sections 20, 22, 43, 85).
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='taste_preference'
    )
    preferred_region = models.ForeignKey(
        'core.Region',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    favorite_cuisines = models.CharField(max_length=250, default='South Indian, Coastal, Mangalorean, Biryani')
    dietary_preference = models.CharField(
        max_length=20,
        choices=[('ANY', 'All Foods'), ('VEG', 'Vegetarian Only'), ('NON_VEG', 'Non-Vegetarian Preferred')],
        default='ANY'
    )
    spice_preference = models.CharField(max_length=20, default='MEDIUM')
    preferred_budget = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('200.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences: {self.user.username}"


class Recommendation(models.Model):
    """
    Persisted & scored AI food recommendations per user/region (Sections 20, 43, 85).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='recommendations'
    )
    region = models.ForeignKey(
        'core.Region',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='recommendations'
    )
    food_item = models.ForeignKey(
        'menu.FoodItem',
        on_delete=models.CASCADE,
        related_name='recommended_entries'
    )
    reason_tag = models.CharField(max_length=180, default='Because you love authentic regional specialties')
    score = models.FloatField(default=0.95)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-score', '-created_at']

    def __str__(self):
        return f"Recommend {self.food_item.name} ({self.reason_tag})"
