from decimal import Decimal
from django.conf import settings
from django.db import models


class DeliveryPartner(models.Model):
    """
    Delivery Partner profile & live status (Sections 17, 18, 43).
    """
    VEHICLE_CHOICES = [
        ('EV_SCOOTER', 'Electric Scooter'),
        ('BIKE', 'Motorcycle'),
        ('SCOOTER', 'Scooter'),
        ('BICYCLE', 'Bicycle'),
    ]
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delivery_partner_profile'
    )
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=25)
    vehicle_type = models.CharField(max_length=25, choices=VEHICLE_CHOICES, default='EV_SCOOTER')
    vehicle_number = models.CharField(max_length=30, default='KA-19-TT-2026')
    city = models.CharField(max_length=100, default='Mangaluru')
    current_area = models.CharField(max_length=120, default='Hampankatta')
    current_lat = models.FloatField(default=12.8714)
    current_lng = models.FloatField(default=74.8426)
    is_available = models.BooleanField(default=True, db_index=True)
    is_verified = models.BooleanField(default=True)
    total_deliveries = models.PositiveIntegerField(default=38)
    today_earnings = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('480.00'))
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('14250.00'))
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.9)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Rider: {self.full_name} ({self.city})"


class Delivery(models.Model):
    """
    Tracks individual order delivery lifecycle, coordinates, and rider earnings (Sections 17, 18, 25, 43).
    """
    STATUS_CHOICES = [
        ('WAITING_PARTNER', 'Waiting for Delivery Partner'),
        ('ASSIGNED', 'Delivery Partner Assigned'),
        ('PICKED_UP', 'Picked Up from Business'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
    ]
    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='delivery')
    partner = models.ForeignKey(
        DeliveryPartner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deliveries'
    )
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='WAITING_PARTNER', db_index=True)
    pickup_address = models.CharField(max_length=255)
    drop_address = models.CharField(max_length=255)
    distance_km = models.DecimalField(max_digits=5, decimal_places=1, default=Decimal('2.4'))
    estimated_mins = models.PositiveIntegerField(default=24)
    delivery_earning = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('40.00'))
    rider_lat = models.FloatField(default=12.9150)
    rider_lng = models.FloatField(default=74.8580)
    assigned_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Delivery for Order #{self.order.order_number} ({self.status})"
