from django.db import models


class Restaurant(models.Model):
    """
    Extended kitchen & operational metadata for dining/restaurant businesses (Section 43).
    """
    business = models.OneToOneField(
        'businesses.Business',
        on_delete=models.CASCADE,
        related_name='restaurant_info'
    )
    chef_special_note = models.CharField(max_length=220, blank=True)
    kitchen_prep_capacity = models.PositiveIntegerField(default=15)
    seating_available = models.BooleanField(default=True)
    takeaway_available = models.BooleanField(default=True)
    packaging_charge = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    hygiene_score = models.DecimalField(max_digits=3, decimal_places=1, default=4.9)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Restaurant Info: {self.business.name}"
