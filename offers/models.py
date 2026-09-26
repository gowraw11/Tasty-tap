from decimal import Decimal
from django.db import models


class Coupon(models.Model):
    """
    Platform & Business discount coupons validated in Smart Cart (Sections 13, 27, 43).
    """
    DISCOUNT_TYPES = [
        ('PERCENT', 'Percentage Discount'),
        ('FLAT', 'Flat ₹ Discount'),
        ('FREE_DELIVERY', 'Free Delivery'),
    ]
    code = models.CharField(max_length=40, unique=True, db_index=True)
    title = models.CharField(max_length=140)
    description = models.CharField(max_length=255, blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='PERCENT')
    discount_value = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('20.00'))
    min_order_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('149.00'))
    max_discount = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True, default=Decimal('100.00'))
    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='coupons'
    )
    region = models.ForeignKey(
        'core.Region',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coupons'
    )
    is_active = models.BooleanField(default=True, db_index=True)
    usage_limit = models.PositiveIntegerField(default=500)
    used_count = models.PositiveIntegerField(default=12)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} ({self.title})"


class Offer(models.Model):
    """
    Business & Regional promotional campaigns (Discounts, Combos, BOGO, Happy Hour, Festival, Lunch, Weekend)
    with Admin governance (Sections 13, 43, 90).
    """
    PROMO_TYPES = [
        ('DISCOUNT', 'Percentage Discount'),
        ('COMBO', 'Combo Offer'),
        ('BOGO', 'Buy 1 Get 1'),
        ('HAPPY_HOUR', 'Happy Hour'),
        ('FESTIVAL', 'Festival Special'),
        ('LUNCH', 'Lunch Offer'),
        ('WEEKEND', 'Weekend Offer'),
        ('FREE_DELIVERY', 'Free Delivery Offer'),
    ]
    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='offers'
    )
    region = models.ForeignKey(
        'core.Region',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='offers'
    )
    title = models.CharField(max_length=160)
    subtitle = models.CharField(max_length=240)
    promo_type = models.CharField(max_length=25, choices=PROMO_TYPES, default='DISCOUNT')
    coupon_code = models.CharField(max_length=40, blank=True)
    discount_percentage = models.PositiveIntegerField(default=20)
    min_order_value = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('199.00'))
    festival_tag = models.CharField(max_length=80, blank=True)
    badge_text = models.CharField(max_length=50, default='LIMITED OFFER')
    is_approved = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_promo_type_display()})"
