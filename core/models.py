from django.db import models
from django.utils.text import slugify


class Region(models.Model):
    """
    Represents an Indian state or culinary region in Tasty Tap Regions (Sections 69-100).
    Allows completely data-driven regional transformation without hardcoded templates.
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(max_length=110, unique=True, db_index=True)
    code = models.CharField(max_length=20, unique=True)
    emoji_flag = models.CharField(max_length=16, default='🇮🇳')
    greeting = models.CharField(max_length=180, default='Welcome to Tasty Tap 👋')
    subheading = models.CharField(max_length=280, default='Discover authentic regional flavors near you.')
    tagline = models.CharField(max_length=200, default='Flavors of the Region')
    short_description = models.TextField(blank=True)
    default_city = models.CharField(max_length=100, default='Bengaluru')
    latitude = models.FloatField(default=12.9716)
    longitude = models.FloatField(default=77.5946)
    card_image_url = models.URLField(max_length=500, blank=True)
    illustration_svg = models.CharField(max_length=80, default='coastal_palm')
    popular_dishes_preview = models.CharField(
        max_length=400,
        help_text='Comma-separated popular dishes shown on region cards'
    )
    specialties_sections = models.JSONField(
        default=list,
        blank=True,
        help_text='List of regional spotlight titles e.g. ["Mangaluru Specials", "Mysuru Specials"]'
    )
    is_active = models.BooleanField(default=True, db_index=True)
    display_order = models.PositiveIntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['slug', 'is_active']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_popular_dishes_list(self):
        return [d.strip() for d in self.popular_dishes_preview.split(',') if d.strip()]

    def __str__(self):
        return f"{self.emoji_flag} {self.name}"


class RegionTheme(models.Model):
    """
    Data-driven visual & cultural theme configuration per Region (Section 72 & 89).
    """
    region = models.OneToOneField(Region, on_delete=models.CASCADE, related_name='theme')
    primary_color = models.CharField(max_length=30, default='#B8532A')
    secondary_color = models.CharField(max_length=30, default='#1B5E68')
    accent_color = models.CharField(max_length=30, default='#E69F38')
    background = models.CharField(max_length=120, default='#FDF8F2')
    hero_gradient = models.CharField(
        max_length=250,
        default='linear-gradient(135deg, #9E421B 0%, #C86D3B 52%, #8A3916 100%)'
    )
    wave_color = models.CharField(max_length=30, default='#1A5F72')
    hero_image = models.URLField(max_length=500, blank=True)
    hero_secondary_image = models.URLField(max_length=500, blank=True)
    hero_tertiary_image = models.URLField(max_length=500, blank=True)
    logo_variant = models.CharField(max_length=100, default='Tasty Tap Coastal')
    font_style = models.CharField(max_length=100, default="'Playfair Display', Georgia, serif")
    animation_style = models.CharField(
        max_length=60,
        default='coastal_wave',
        help_text='E.g. coastal_wave, coconut_breeze, temple_glow, royal_marigold, spice_burst'
    )
    food_categories = models.JSONField(default=list, blank=True)
    popular_foods = models.JSONField(default=list, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Theme: {self.region.name}"


class RegionalCuisine(models.Model):
    """
    Specific sub-cuisines inside a Region (e.g., Udupi, Mangalorean, Malabar, Chettinad).
    """
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='cuisines')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120)
    icon = models.CharField(max_length=30, default='🍛')
    description = models.TextField(blank=True)
    is_signature = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('region', 'slug')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.region.slug}-{self.name}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.region.name})"


class RegionalCategory(models.Model):
    """
    Dynamically generated categories per Region (Section 83).
    """
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='regional_categories')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120)
    icon = models.CharField(max_length=30, default='🍲')
    illustration_url = models.URLField(max_length=500, blank=True)
    badge_label = models.CharField(max_length=60, blank=True)
    display_order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.region.slug}-{self.name}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.region.name} - {self.name}"


class RegionalFood(models.Model):
    """
    Iconic regional dishes & food stories (Sections 80, 91).
    """
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='regional_foods')
    cuisine = models.ForeignKey(RegionalCuisine, on_delete=models.SET_NULL, null=True, blank=True, related_name='foods')
    name = models.CharField(max_length=140, db_index=True)
    slug = models.SlugField(max_length=160)
    description = models.TextField()
    typical_price = models.DecimalField(max_digits=8, decimal_places=2, default=65.00)
    veg_type = models.CharField(max_length=20, choices=[('VEG', 'Vegetarian'), ('NON_VEG', 'Non-Vegetarian')], default='VEG')
    spice_level = models.CharField(max_length=20, default='MEDIUM')
    popular_in_cities = models.CharField(max_length=200, blank=True)
    origin_story = models.TextField(blank=True)
    preparation_style = models.TextField(blank=True)
    regional_significance = models.TextField(blank=True)
    image_url = models.URLField(max_length=500, blank=True)
    is_iconic = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.region.slug}-{self.name}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.region.name})"


class RegionalBusiness(models.Model):
    """
    Maps regional showcase metadata to local businesses (Section 80 & 81).
    """
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='regional_businesses')
    linked_business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='regional_spotlights'
    )
    business_name = models.CharField(max_length=150)
    city = models.CharField(max_length=100)
    specialty = models.CharField(max_length=200)
    spotlight_tag = models.CharField(
        max_length=60,
        default='Local Favorite',
        help_text='Famous Hotels, Local Favorites, Historic Food Places, Trending Cafes, Hidden Gems'
    )
    is_demo_business = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.business_name} ({self.region.name})"


class RegionalOffer(models.Model):
    """
    Regional & Festival Specials (Sections 80, 90).
    """
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='regional_offers')
    business = models.ForeignKey('businesses.Business', on_delete=models.CASCADE, null=True, blank=True)
    festival_name = models.CharField(
        max_length=100,
        blank=True,
        help_text='E.g. Onam Sadhya, Pongal Harvest, Ugadi Special, Mysuru Dasara, Ganesh Chaturthi, Diwali'
    )
    title = models.CharField(max_length=160)
    subtitle = models.CharField(max_length=250)
    coupon_code = models.CharField(max_length=40, default='REGIONAL20')
    discount_percentage = models.PositiveIntegerField(default=20)
    is_approved = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.region.name})"


class PlatformSetting(models.Model):
    """
    Admin-configurable platform rules (points, joining fees, allowed promo types, etc.).
    """
    key = models.CharField(max_length=80, unique=True)
    value = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key} = {self.value}"
