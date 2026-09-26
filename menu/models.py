from django.db import models
from django.utils.text import slugify


class FoodCategory(models.Model):
    """
    Menu categories (e.g., Malabar Special, Goan Curries, Mangalorean Tandoor, Konkan Fry,
    Coastal Desserts, South Indian, North Indian, Chinese, Fast Food, Bakery, Cafe, Beverages, Home Food).
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    icon = models.CharField(max_length=30, default='🍛')
    image_url = models.URLField(max_length=500, blank=True)
    region = models.ForeignKey(
        'core.Region',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='food_categories'
    )
    display_order = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.icon} {self.name}"


class FoodItem(models.Model):
    """
    Multi-tenant food product managed independently by each Business Partner (Sections 7, 8, 36, 43, 91).
    Includes complete nutritional, customization, regional story, and Smart Meal Builder metadata.
    """
    VEG_CHOICES = [
        ('VEG', 'Vegetarian'),
        ('NON_VEG', 'Non-Vegetarian'),
        ('EGG', 'Contains Egg'),
    ]

    SPICE_CHOICES = [
        ('MILD', 'Mild'),
        ('MEDIUM', 'Medium'),
        ('HOT', 'Hot'),
        ('EXTREME', 'Extreme'),
    ]

    COURSE_CHOICES = [
        ('STARTER', 'Starter'),
        ('MAIN', 'Main Course'),
        ('SIDE', 'Side / Bread'),
        ('DRINK', 'Drink / Beverage'),
        ('DESSERT', 'Dessert / Sweet'),
        ('BREAKFAST', 'Breakfast / Tiffin'),
        ('SNACK', 'Snack / Fast Food'),
    ]

    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.CASCADE,
        related_name='food_items',
        db_index=True
    )
    category = models.ForeignKey(
        FoodCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='food_items'
    )
    region = models.ForeignKey(
        'core.Region',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='menu_items',
        db_index=True
    )
    name = models.CharField(max_length=160, db_index=True)
    slug = models.SlugField(max_length=190, db_index=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2, db_index=True)
    discount_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    veg_type = models.CharField(max_length=15, choices=VEG_CHOICES, default='VEG', db_index=True)
    spice_level = models.CharField(max_length=15, choices=SPICE_CHOICES, default='MEDIUM', db_index=True)
    meal_course = models.CharField(max_length=20, choices=COURSE_CHOICES, default='MAIN', db_index=True)
    preparation_time = models.PositiveIntegerField(default=20, help_text='Preparation time in minutes')
    calories = models.PositiveIntegerField(default=380)
    ingredients = models.TextField(default='Fresh local spices, herbs, cold-pressed oil, chef signature masala')
    allergens = models.CharField(max_length=180, blank=True, default='None / Check with kitchen for nut traces')
    # Regional Food Story (Section 91)
    origin_story = models.TextField(blank=True)
    preparation_style = models.CharField(max_length=255, blank=True)
    regional_significance = models.CharField(max_length=255, blank=True)
    # Inventory & Visuals
    image_url = models.URLField(max_length=500, blank=True)
    image = models.ImageField(upload_to='menu/foods/', null=True, blank=True)
    stock_quantity = models.PositiveIntegerField(default=45)
    is_available = models.BooleanField(default=True, db_index=True)
    is_bestseller = models.BooleanField(default=False)
    is_coastal_favorite = models.BooleanField(default=False)
    is_healthy = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.8)
    order_count = models.PositiveIntegerField(default=25)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_bestseller', '-rating', 'name']
        indexes = [
            models.Index(fields=['business', 'is_available']),
            models.Index(fields=['region', 'is_available']),
            models.Index(fields=['veg_type', 'price']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.business_id or 'tt'}-{self.name}")
        super().save(*args, **kwargs)

    @property
    def effective_price(self):
        if self.discount_price and 0 < self.discount_price < self.price:
            return self.discount_price
        return self.price

    def get_image(self):
        if self.image:
            return self.image.url
        return self.image_url or 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=600&auto=format&fit=crop&q=80'

    def __str__(self):
        return f"{self.name} — ₹{self.effective_price} ({self.business.name})"


class FoodCustomization(models.Model):
    """
    Dynamic size, spice level, and add-on customization options per FoodItem (Section 36, 43).
    """
    GROUP_CHOICES = [
        ('SIZE', 'Size'),
        ('ADDON', 'Add-ons'),
        ('SPICE', 'Spice Level'),
    ]
    food_item = models.ForeignKey(
        FoodItem,
        on_delete=models.CASCADE,
        related_name='customizations'
    )
    group_type = models.CharField(max_length=20, choices=GROUP_CHOICES, default='ADDON')
    option_name = models.CharField(max_length=100)
    price_delta = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['group_type', 'price_delta']

    def __str__(self):
        return f"{self.food_item.name} - {self.get_group_type_display()}: {self.option_name} (+₹{self.price_delta})"
