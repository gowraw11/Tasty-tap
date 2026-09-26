from decimal import Decimal
from django.db import models


class BusinessAnalytics(models.Model):
    """
    Daily & aggregated performance analytics for each Business Partner (Sections 6, 14, 15, 43).
    """
    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.CASCADE,
        related_name='analytics_records'
    )
    date = models.DateField(db_index=True)
    daily_orders = models.PositiveIntegerField(default=0)
    daily_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    new_customers = models.PositiveIntegerField(default=0)
    returning_customers = models.PositiveIntegerField(default=0)
    average_order_value = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    top_product_name = models.CharField(max_length=150, blank=True)
    peak_hour = models.CharField(max_length=40, default='1:00 PM - 2:30 PM')
    store_views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        unique_together = ('business', 'date')

    def __str__(self):
        return f"{self.business.name} Analytics ({self.date}): ₹{self.daily_revenue}"
