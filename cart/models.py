from decimal import Decimal
from django.conf import settings
from django.db import models


class Cart(models.Model):
    """
    Smart Multi-Vendor Cart enforcing single-business checkout per order (Sections 9, 37, 43).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='carts'
    )
    session_key = models.CharField(max_length=100, blank=True, db_index=True)
    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='active_carts'
    )
    applied_coupon = models.ForeignKey(
        'offers.Coupon',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='carts'
    )
    redeem_points = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_subtotal(self):
        total = Decimal('0.00')
        for item in self.items.select_related('food_item').all():
            total += item.get_line_total()
        return total.quantize(Decimal('0.01'))

    def get_discount(self):
        subtotal = self.get_subtotal()
        if not self.applied_coupon or subtotal <= 0:
            return Decimal('0.00')
        coupon = self.applied_coupon
        if not coupon.is_active or subtotal < coupon.min_order_amount:
            return Decimal('0.00')
        if coupon.business_id and self.business_id and coupon.business_id != self.business_id:
            return Decimal('0.00')
        if coupon.discount_type == 'PERCENT':
            disc = (subtotal * coupon.discount_value) / Decimal('100.00')
            if coupon.max_discount and disc > coupon.max_discount:
                disc = coupon.max_discount
            return min(disc, subtotal).quantize(Decimal('0.01'))
        elif coupon.discount_type == 'FLAT':
            return min(coupon.discount_value, subtotal).quantize(Decimal('0.01'))
        return Decimal('0.00')

    def get_delivery_fee(self):
        subtotal = self.get_subtotal()
        if subtotal <= 0:
            return Decimal('0.00')
        if self.applied_coupon and self.applied_coupon.is_active and self.applied_coupon.discount_type == 'FREE_DELIVERY':
            if subtotal >= self.applied_coupon.min_order_amount:
                return Decimal('0.00')
        threshold = self.business.free_delivery_threshold if self.business else Decimal('199.00')
        base_fee = self.business.delivery_fee if self.business else Decimal('25.00')
        if threshold > 0 and subtotal >= threshold:
            return Decimal('0.00')
        return base_fee.quantize(Decimal('0.01'))

    def get_free_delivery_progress(self):
        """
        Calculates progress bar data for Smart Cart (Section 37: "₹80 more for free delivery").
        """
        subtotal = self.get_subtotal()
        threshold = self.business.free_delivery_threshold if self.business else Decimal('199.00')
        if threshold <= 0:
            return {'unlocked': True, 'remaining': Decimal('0.00'), 'percent': 100, 'threshold': threshold}
        if subtotal >= threshold:
            return {'unlocked': True, 'remaining': Decimal('0.00'), 'percent': 100, 'threshold': threshold}
        remaining = (threshold - subtotal).quantize(Decimal('0.01'))
        percent = int(min(100, round((float(subtotal) / float(threshold)) * 100)))
        return {'unlocked': False, 'remaining': remaining, 'percent': percent, 'threshold': threshold}

    def get_tax(self):
        taxable = max(Decimal('0.00'), self.get_subtotal() - self.get_discount())
        return (taxable * Decimal('0.05')).quantize(Decimal('0.01'))

    def get_points_discount(self):
        if not self.redeem_points:
            return Decimal('0.00')
        subtotal_after_disc = max(Decimal('0.00'), self.get_subtotal() - self.get_discount())
        max_redeemable = min(Decimal(str(self.redeem_points)), subtotal_after_disc * Decimal('0.50'))
        return max_redeemable.quantize(Decimal('0.01'))

    def get_total(self):
        subtotal = self.get_subtotal()
        if subtotal <= 0:
            return Decimal('0.00')
        total = subtotal - self.get_discount() - self.get_points_discount() + self.get_tax() + self.get_delivery_fee()
        return max(Decimal('0.00'), total).quantize(Decimal('0.01'))

    def get_item_count(self):
        return sum(i.quantity for i in self.items.all())

    def __str__(self):
        owner_label = self.user.username if self.user else f"Session({self.session_key[:8]})"
        return f"Cart({owner_label})"


class CartItem(models.Model):
    """
    Individual line item in the Smart Cart with food customizations (Section 36, 37, 43).
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    food_item = models.ForeignKey('menu.FoodItem', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    selected_size = models.CharField(max_length=60, default='Regular')
    selected_spice = models.CharField(max_length=60, default='Medium')
    selected_addons = models.CharField(max_length=255, blank=True)
    addon_unit_price = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('0.00'))
    special_instructions = models.CharField(max_length=220, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_unit_price(self):
        return (self.food_item.effective_price + self.addon_unit_price).quantize(Decimal('0.01'))

    def get_line_total(self):
        return (self.get_unit_price() * self.quantity).quantize(Decimal('0.01'))

    def get_customization_display(self):
        parts = []
        if self.selected_size and self.selected_size != 'Regular':
            parts.append(f"Size: {self.selected_size}")
        if self.selected_spice:
            parts.append(f"Spice: {self.selected_spice}")
        if self.selected_addons:
            parts.append(f"Add-ons: {self.selected_addons}")
        return " • ".join(parts)

    def __str__(self):
        return f"{self.food_item.name} x {self.quantity}"


class Wishlist(models.Model):
    """
    Customer saved favorite foods and favorite businesses (Section 29, 43).
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist'
    )
    food_items = models.ManyToManyField('menu.FoodItem', blank=True, related_name='wishlisted_by')
    businesses = models.ManyToManyField('businesses.Business', blank=True, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wishlist: {self.user.username}"
