from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Role-based profile for the 4 core roles:
    1. CUSTOMER
    2. BUSINESS_PARTNER
    3. DELIVERY_PARTNER
    4. ADMIN
    Plus Region & Delivery Location separation (Section 94) and Tasty Points wallet (Section 27).
    """
    ROLE_CHOICES = [
        ('CUSTOMER', 'Customer'),
        ('BUSINESS_PARTNER', 'Business Partner'),
        ('DELIVERY_PARTNER', 'Delivery Partner'),
        ('ADMIN', 'Admin'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(max_length=25, choices=ROLE_CHOICES, default='CUSTOMER', db_index=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar_url = models.URLField(max_length=500, blank=True)
    selected_region = models.ForeignKey(
        'core.Region',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users_exploring'
    )
    has_chosen_region = models.BooleanField(default=False)
    # Delivery location is intentionally independent of Explore Region (Section 94)
    delivery_location_label = models.CharField(max_length=60, default='Home')
    delivery_city = models.CharField(max_length=100, default='Mangaluru')
    delivery_area = models.CharField(max_length=120, default='MG Road')
    delivery_state = models.CharField(max_length=100, default='Karnataka')
    delivery_lat = models.FloatField(default=12.9141)
    delivery_lng = models.FloatField(default=74.8560)
    # Wallet & Rewards
    tasty_points = models.PositiveIntegerField(default=120)
    dark_mode = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


class Address(models.Model):
    """
    Customer saved addresses (Home, Work, Current Location, Other) with coordinates (Section 24, 43).
    """
    LABEL_CHOICES = [
        ('Home', 'Home'),
        ('Work', 'Work'),
        ('Current Location', 'Current Location'),
        ('Other', 'Other'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='addresses'
    )
    label = models.CharField(max_length=30, choices=LABEL_CHOICES, default='Home')
    recipient_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address_line = models.CharField(max_length=255)
    area = models.CharField(max_length=120)
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100, default='Karnataka')
    pincode = models.CharField(max_length=12, default='575001')
    latitude = models.FloatField(default=12.9141)
    longitude = models.FloatField(default=74.8560)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.label}: {self.area}, {self.city}"


class PointsTransaction(models.Model):
    """
    Tracks Tasty Points history: earned on orders & redeemed on checkout (Section 27).
    """
    TX_TYPES = [
        ('EARNED', 'Earned from Order'),
        ('REDEEMED', 'Redeemed on Checkout'),
        ('BONUS', 'Welcome / Promo Bonus'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='points_history'
    )
    points = models.IntegerField()
    transaction_type = models.CharField(max_length=20, choices=TX_TYPES, default='EARNED')
    description = models.CharField(max_length=220)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.points} pts ({self.transaction_type})"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_user_profile(sender, instance, created, **kwargs):
    if created:
        role = 'ADMIN' if instance.is_superuser else 'CUSTOMER'
        UserProfile.objects.get_or_create(user=instance, defaults={'role': role})
