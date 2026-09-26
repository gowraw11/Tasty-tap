from django.conf import settings
from django.db import models


class Payment(models.Model):
    """
    Payment transaction record structured for Mock Gateway & Razorpay/Stripe integration (Section 26, 43).
    Never stores raw card numbers or CVV.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]
    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='payment')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    transaction_id = models.CharField(max_length=100, unique=True, db_index=True)
    gateway = models.CharField(max_length=40, default='TASTY_TAP_MOCK_PAY')
    payment_method = models.CharField(max_length=30, default='UPI')
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUCCESS')
    masked_instrument = models.CharField(
        max_length=80,
        blank=True,
        help_text='Safe masked reference e.g. user@okaxis or CARD-XXXX-4242 (Never stores card number/CVV)'
    )
    paid_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.transaction_id} — ₹{self.amount} ({self.status})"
