from decimal import Decimal
from django.conf import settings
from django.db import models


class Order(models.Model):
    """
    Complete multi-vendor customer order connected to Business & Delivery Partner (Sections 16, 17, 25, 30, 43, 53).
    """
    STATUS_CHOICES = [
        ('CONFIRMED', 'Confirmed'),
        ('ACCEPTED', 'Accepted'),
        ('PREPARING', 'Preparing'),
        ('READY', 'Ready for Pickup'),
        ('ASSIGNED', 'Delivery Partner Assigned'),
        ('PICKED_UP', 'Picked Up'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]

    PAYMENT_METHODS = [
        ('UPI', 'UPI (GPay / PhonePe / Paytm)'),
        ('CARD', 'Credit / Debit Card'),
        ('NET_BANKING', 'Net Banking'),
        ('COD', 'Cash on Delivery'),
    ]

    PAYMENT_STATUSES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]

    order_number = models.CharField(max_length=25, unique=True, db_index=True)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.CASCADE,
        related_name='orders'
    )
    region = models.ForeignKey(
        'core.Region',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    # Delivery destination
    customer_name = models.CharField(max_length=120)
    customer_phone = models.CharField(max_length=25)
    delivery_address = models.CharField(max_length=255)
    delivery_area = models.CharField(max_length=120, default='MG Road')
    delivery_city = models.CharField(max_length=100, default='Mangaluru')
    delivery_lat = models.FloatField(default=12.9180)
    delivery_lng = models.FloatField(default=74.8610)
    # Financials
    subtotal = models.DecimalField(max_digits=9, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    points_redeemed = models.PositiveIntegerField(default=0)
    points_discount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    delivery_fee = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=9, decimal_places=2, default=Decimal('0.00'))
    coupon_code = models.CharField(max_length=40, blank=True)
    # Status & Payment
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='CONFIRMED', db_index=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='UPI')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUSES, default='PAID')
    estimated_delivery_mins = models.PositiveIntegerField(default=28)
    points_earned = models.PositiveIntegerField(default=10)
    special_instructions = models.TextField(blank=True)
    # Timestamps
    accepted_at = models.DateTimeField(null=True, blank=True)
    prepared_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['business', 'status']),
            models.Index(fields=['customer', '-created_at']),
        ]

    def get_timeline_steps(self):
        """
        Returns animated status tracker steps for Order Tracking (Sections 17, 25).
        """
        sequence = [
            ('CONFIRMED', 'Confirmed', '✓'),
            ('ACCEPTED', 'Accepted', '👍'),
            ('PREPARING', 'Preparing', '🔥'),
            ('READY', 'Ready', '🥡'),
            ('OUT_FOR_DELIVERY', 'Out for Delivery', '🚴'),
            ('DELIVERED', 'Delivered', '🏠'),
        ]
        order_rank = {
            'CONFIRMED': 0,
            'ACCEPTED': 1,
            'PREPARING': 2,
            'READY': 3,
            'ASSIGNED': 3,
            'PICKED_UP': 4,
            'OUT_FOR_DELIVERY': 4,
            'DELIVERED': 5,
            'REJECTED': -1,
            'CANCELLED': -1,
        }
        current_idx = order_rank.get(self.status, 0)
        steps = []
        for idx, (code, label, icon) in enumerate(sequence):
            steps.append({
                'code': code,
                'label': label,
                'icon': icon,
                'completed': idx <= current_idx,
                'active': idx == current_idx,
            })
        return steps

    def __str__(self):
        return f"Order #{self.order_number} ({self.get_status_display()})"


class OrderItem(models.Model):
    """
    Immutable snapshot of each ordered item & customization (Section 43).
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    food_item = models.ForeignKey(
        'menu.FoodItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items'
    )
    food_name = models.CharField(max_length=160)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    addon_price = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('0.00'))
    quantity = models.PositiveIntegerField(default=1)
    customization_details = models.CharField(max_length=255, blank=True)
    line_total = models.DecimalField(max_digits=9, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.food_name} ×{self.quantity} ({self.order.order_number})"
