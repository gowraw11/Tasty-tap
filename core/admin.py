from django.contrib import admin
from core.models import (
    Region, RegionTheme, RegionalCuisine, RegionalCategory,
    RegionalFood, RegionalBusiness, RegionalOffer, PlatformSetting
)
from accounts.models import UserProfile, Address, PointsTransaction
from businesses.models import BusinessCategory, Business, BusinessProfile, BusinessVerification
from restaurants.models import Restaurant
from menu.models import FoodCategory, FoodItem, FoodCustomization
from cart.models import Cart, CartItem, Wishlist
from orders.models import Order, OrderItem
from payments.models import Payment
from delivery.models import DeliveryPartner, Delivery
from reviews.models import Review
from offers.models import Coupon, Offer
from recommendations.models import UserPreference, Recommendation
from notifications.models import Notification
from analytics.models import BusinessAnalytics


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'emoji_flag', 'default_city', 'is_active', 'display_order')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner_name', 'business_type', 'region', 'city', 'status', 'rating', 'joining_cost_inr')
    list_filter = ('status', 'business_type', 'region', 'dietary_type')
    search_fields = ('name', 'owner_name', 'city', 'cuisine')


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'region', 'category', 'price', 'discount_price', 'veg_type', 'is_available')
    list_filter = ('veg_type', 'spice_level', 'meal_course', 'is_available', 'region')
    search_fields = ('name', 'description', 'business__name')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_name', 'business', 'total_amount', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'payment_status')
    search_fields = ('order_number', 'customer_name', 'business__name')


admin.site.register(RegionTheme)
admin.site.register(RegionalCuisine)
admin.site.register(RegionalCategory)
admin.site.register(RegionalFood)
admin.site.register(RegionalBusiness)
admin.site.register(RegionalOffer)
admin.site.register(PlatformSetting)
admin.site.register(UserProfile)
admin.site.register(Address)
admin.site.register(PointsTransaction)
admin.site.register(BusinessCategory)
admin.site.register(BusinessProfile)
admin.site.register(BusinessVerification)
admin.site.register(Restaurant)
admin.site.register(FoodCategory)
admin.site.register(FoodCustomization)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Wishlist)
admin.site.register(OrderItem)
admin.site.register(Payment)
admin.site.register(DeliveryPartner)
admin.site.register(Delivery)
admin.site.register(Review)
admin.site.register(Coupon)
admin.site.register(Offer)
admin.site.register(UserPreference)
admin.site.register(Recommendation)
admin.site.register(Notification)
admin.site.register(BusinessAnalytics)
