from django.conf import settings
from django.db import models


class Notification(models.Model):
    """
    Multi-role notifications for Customer, Business Partner, Delivery Partner, and Admin (Sections 16, 43, 52).
    """
    TYPE_CHOICES = [
        ('ORDER', 'Order Update'),
        ('BUSINESS', 'Business Store Update'),
        ('DELIVERY', 'Delivery Assignment'),
        ('OFFER', 'New Offer / Promotion'),
        ('ADMIN', 'Admin Marketplace Alert'),
    ]
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    target_role = models.CharField(max_length=25, default='CUSTOMER')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='ORDER')
    title = models.CharField(max_length=160)
    message = models.TextField()
    link_url = models.CharField(max_length=250, blank=True, default='/')
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.target_role}] {self.title}"
