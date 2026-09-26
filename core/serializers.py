from rest_framework import serializers
from core.models import Region, RegionTheme, RegionalCategory, RegionalFood, RegionalOffer
from businesses.models import Business, BusinessCategory, BusinessProfile
from menu.models import FoodCategory, FoodItem, FoodCustomization
from orders.models import Order, OrderItem
from payments.models import Payment
from reviews.models import Review
from offers.models import Coupon, Offer
from recommendations.models import Recommendation
from delivery.models import Delivery, DeliveryPartner
from notifications.models import Notification


class RegionThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegionTheme
        fields = [
            'primary_color', 'secondary_color', 'accent_color', 'background',
            'hero_gradient', 'wave_color', 'hero_image', 'hero_secondary_image',
            'logo_variant', 'font_style', 'animation_style', 'food_categories',
            'popular_foods', 'description'
        ]


class RegionSerializer(serializers.ModelSerializer):
    theme = RegionThemeSerializer(read_only=True)
    popular_dishes = serializers.SerializerMethodField()

    class Meta:
        model = Region
        fields = [
            'id', 'name', 'slug', 'code', 'emoji_flag', 'greeting',
            'subheading', 'tagline', 'short_description', 'default_city',
            'latitude', 'longitude', 'card_image_url', 'illustration_svg',
            'popular_dishes_preview', 'popular_dishes', 'specialties_sections', 'theme'
        ]

    def get_popular_dishes(self, obj):
        return obj.get_popular_dishes_list()


class BusinessSerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source='region.name', default='All India', read_only=True)
    business_type_display = serializers.CharField(source='get_business_type_display', read_only=True)
    badges = serializers.SerializerMethodField()
    cover_image = serializers.SerializerMethodField()
    logo_image = serializers.SerializerMethodField()
    marker_emoji = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = [
            'id', 'name', 'slug', 'owner_name', 'business_type', 'business_type_display',
            'region', 'region_name', 'address', 'area', 'city', 'state', 'pincode',
            'latitude', 'longitude', 'distance_km', 'cuisine', 'estimated_delivery_time',
            'delivery_fee', 'free_delivery_threshold', 'price_range', 'dietary_type',
            'status', 'joining_cost_inr', 'is_open_now', 'is_featured', 'is_hidden_gem',
            'is_local_favorite', 'rating', 'total_reviews', 'badges', 'cover_image',
            'logo_image', 'marker_emoji'
        ]

    def get_badges(self, obj):
        return obj.get_badges()

    def get_cover_image(self, obj):
        prof = getattr(obj, 'profile', None)
        return prof.get_cover() if prof else ''

    def get_logo_image(self, obj):
        prof = getattr(obj, 'profile', None)
        return prof.get_logo() if prof else ''

    def get_marker_emoji(self, obj):
        return obj.get_map_marker_emoji()


class FoodCustomizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodCustomization
        fields = ['id', 'group_type', 'option_name', 'price_delta', 'is_default']


class FoodCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodCategory
        fields = ['id', 'name', 'slug', 'icon', 'image_url', 'region', 'display_order']


class FoodItemSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='business.name', read_only=True)
    business_slug = serializers.CharField(source='business.slug', read_only=True)
    category_name = serializers.CharField(source='category.name', default='Specialty', read_only=True)
    region_name = serializers.CharField(source='region.name', default='All India', read_only=True)
    effective_price = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    image_resolved = serializers.SerializerMethodField()
    customizations = FoodCustomizationSerializer(many=True, read_only=True)

    class Meta:
        model = FoodItem
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'discount_price', 'effective_price',
            'veg_type', 'spice_level', 'meal_course', 'preparation_time', 'calories',
            'ingredients', 'allergens', 'origin_story', 'preparation_style',
            'regional_significance', 'image_resolved', 'stock_quantity', 'is_available',
            'is_bestseller', 'is_coastal_favorite', 'is_healthy', 'rating',
            'business', 'business_name', 'business_slug', 'category', 'category_name',
            'region', 'region_name', 'customizations'
        ]

    def get_image_resolved(self, obj):
        return obj.get_image()


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'food_item', 'food_name', 'unit_price', 'addon_price', 'quantity', 'customization_details', 'line_total']


class OrderSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='business.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    timeline = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer_name', 'business', 'business_name',
            'delivery_address', 'delivery_area', 'delivery_city', 'subtotal',
            'discount_amount', 'points_discount', 'tax_amount', 'delivery_fee',
            'total_amount', 'status', 'status_display', 'payment_method',
            'payment_status', 'estimated_delivery_mins', 'points_earned',
            'created_at', 'items', 'timeline'
        ]

    def get_timeline(self, obj):
        return obj.get_timeline_steps()


class PaymentSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'order_number', 'transaction_id', 'gateway', 'payment_method', 'amount', 'status', 'masked_instrument', 'paid_at']


class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)
    food_name = serializers.CharField(source='food_item.name', default='', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'username', 'business', 'business_name', 'food_item', 'food_name',
            'business_rating', 'food_rating', 'comment', 'photo_url',
            'is_verified_order', 'business_reply', 'created_at'
        ]


class OfferSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='business.name', default='Tasty Tap Platform', read_only=True)
    region_name = serializers.CharField(source='region.name', default='All India', read_only=True)

    class Meta:
        model = Offer
        fields = [
            'id', 'title', 'subtitle', 'promo_type', 'coupon_code',
            'discount_percentage', 'min_order_value', 'festival_tag',
            'badge_text', 'business_name', 'region_name', 'is_active'
        ]


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['id', 'code', 'title', 'description', 'discount_type', 'discount_value', 'min_order_amount', 'max_discount', 'is_active']


class DeliverySerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    business_name = serializers.CharField(source='order.business.name', read_only=True)
    partner_name = serializers.CharField(source='partner.full_name', default='Assigning Partner...', read_only=True)

    class Meta:
        model = Delivery
        fields = [
            'id', 'order_number', 'business_name', 'partner_name', 'status',
            'pickup_address', 'drop_address', 'distance_km', 'estimated_mins',
            'delivery_earning', 'rider_lat', 'rider_lng'
        ]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'target_role', 'notification_type', 'title', 'message', 'link_url', 'is_read', 'created_at']
