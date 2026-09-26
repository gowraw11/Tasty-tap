from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from core.views import (
    home_view,
    explore_view,
    food_story_detail_view,
    update_location_view,
    map_tile_proxy_view,
)
from core.api_views import (
    AuthAPIView,
    RegionSwitchAPIView,
    BusinessListAPIView,
    BusinessDetailAPIView,
    FoodListAPIView,
    CategoryListAPIView,
    CartAPIView,
    OrderAPIView,
    PaymentAPIView,
    ReviewAPIView,
    OfferAPIView,
    RecommendationAPIView,
    DeliveryAPIView,
    NotificationAPIView,
    LiveSearchAPIView,
    WishlistToggleAPIView,
)
from accounts.views import (
    login_view,
    register_view,
    logout_view,
    forgot_password_view,
    profile_view,
    wishlist_view,
)
from businesses.views import (
    partner_landing_view,
    business_register_wizard_view,
    store_detail_view,
    business_dashboard_view,
    admin_marketplace_dashboard_view,
)
from orders.views import (
    cart_checkout_view,
    order_tracking_view,
    order_invoice_pdf_view,
    reorder_view,
)
from delivery.views import delivery_dashboard_view

urlpatterns = [
    path('django-admin/', admin.site.urls),

    # Customer & Regional Discovery Pages
    path('', home_view, name='home'),
    path('explore/', explore_view, name='explore'),
    path('food/<slug:slug>/', food_story_detail_view, name='food_detail'),
    path('location/update/', update_location_view, name='update_location'),
    path('wishlist/', wishlist_view, name='wishlist'),

    # Authentication & Customer Profile
    path('accounts/login/', login_view, name='login'),
    path('accounts/register/', register_view, name='register'),
    path('accounts/logout/', logout_view, name='logout'),
    path('accounts/forgot-password/', forgot_password_view, name='forgot_password'),
    path('accounts/profile/', profile_view, name='profile'),

    # Tasty Tap Partner Program & Storefront
    path('partner/', partner_landing_view, name='partner_landing'),
    path('partner/register/', business_register_wizard_view, name='business_register'),
    path('store/<slug:slug>/', store_detail_view, name='store_detail'),

    # Role Dashboards (Business Partner, Delivery Partner, Admin Marketplace Control)
    path('dashboard/business/', business_dashboard_view, name='business_dashboard'),
    path('dashboard/delivery/', delivery_dashboard_view, name='delivery_dashboard'),
    path('dashboard/admin/', admin_marketplace_dashboard_view, name='admin_dashboard'),

    # Smart Cart, Checkout, Live Order Tracking, PDF Invoice & Reorder
    path('cart/', cart_checkout_view, name='cart_checkout'),
    path('orders/<str:order_number>/track/', order_tracking_view, name='order_track'),
    path('orders/<str:order_number>/invoice/', order_invoice_pdf_view, name='order_invoice'),
    path('orders/<str:order_number>/reorder/', reorder_view, name='order_reorder'),

    # REST APIs (Section 54)
    path('api/auth/', AuthAPIView.as_view(), name='api_auth'),
    path('api/regions/', RegionSwitchAPIView.as_view(), name='api_regions'),
    path('api/businesses/', BusinessListAPIView.as_view(), name='api_businesses'),
    path('api/businesses/<int:pk>/', BusinessDetailAPIView.as_view(), name='api_business_detail'),
    path('api/foods/', FoodListAPIView.as_view(), name='api_foods'),
    path('api/categories/', CategoryListAPIView.as_view(), name='api_categories'),
    path('api/cart/', CartAPIView.as_view(), name='api_cart'),
    path('api/orders/', OrderAPIView.as_view(), name='api_orders'),
    path('api/payments/', PaymentAPIView.as_view(), name='api_payments'),
    path('api/reviews/', ReviewAPIView.as_view(), name='api_reviews'),
    path('api/offers/', OfferAPIView.as_view(), name='api_offers'),
    path('api/recommendations/', RecommendationAPIView.as_view(), name='api_recommendations'),
    path('api/delivery/', DeliveryAPIView.as_view(), name='api_delivery'),
    path('api/notifications/', NotificationAPIView.as_view(), name='api_notifications'),
    path('api/search/', LiveSearchAPIView.as_view(), name='api_search'),
    path('api/wishlist/', WishlistToggleAPIView.as_view(), name='api_wishlist'),
    path('api/map-tiles/<int:z>/<int:x>/<int:y>.png', map_tile_proxy_view, name='api_map_tiles'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
