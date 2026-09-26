from decimal import Decimal
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Region
from core.context_processors import get_active_region
from core.serializers import (
    RegionSerializer, BusinessSerializer, FoodCategorySerializer,
    FoodItemSerializer, OrderSerializer, PaymentSerializer,
    ReviewSerializer, OfferSerializer, CouponSerializer,
    DeliverySerializer, NotificationSerializer
)
from businesses.models import Business
from menu.models import FoodCategory, FoodItem
from cart.models import CartItem
from cart.utils import get_or_create_cart, get_or_create_wishlist
from orders.models import Order
from payments.models import Payment
from reviews.models import Review
from offers.models import Offer, Coupon
from delivery.models import Delivery
from notifications.models import Notification
from recommendations.engine import (
    get_tasty_ai_recommendations,
    build_smart_meal,
    answer_tap_ai_query
)


def serialize_cart_payload(cart):
    items_data = []
    for item in cart.items.select_related('food_item', 'food_item__business').all():
        items_data.append({
            'id': item.id,
            'food_id': item.food_item.id,
            'name': item.food_item.name,
            'business_name': item.food_item.business.name,
            'image_url': item.food_item.get_image(),
            'rating': float(item.food_item.rating),
            'prep_time': item.food_item.preparation_time,
            'quantity': item.quantity,
            'unit_price': float(item.get_unit_price()),
            'line_total': float(item.get_line_total()),
            'customization': item.get_customization_display(),
        })
    progress = cart.get_free_delivery_progress()
    return {
        'cart_id': cart.id,
        'business_id': cart.business_id,
        'business_name': cart.business.name if cart.business else None,
        'business_delivery_time': cart.business.estimated_delivery_time if cart.business else '20–30 min',
        'item_count': cart.get_item_count(),
        'items': items_data,
        'subtotal': float(cart.get_subtotal()),
        'discount': float(cart.get_discount()),
        'points_discount': float(cart.get_points_discount()),
        'tax': float(cart.get_tax()),
        'delivery_fee': float(cart.get_delivery_fee()),
        'total': float(cart.get_total()),
        'applied_coupon': cart.applied_coupon.code if cart.applied_coupon else None,
        'free_delivery_progress': {
            'unlocked': progress['unlocked'],
            'remaining': float(progress['remaining']),
            'percent': progress['percent'],
            'threshold': float(progress['threshold']),
        },
    }


class AuthAPIView(APIView):
    """
    /api/auth/ — Inspect current session user or authenticate via REST API (Section 54).
    """
    def get(self, request):
        if request.user.is_authenticated:
            prof = getattr(request.user, 'profile', None)
            return Response({
                'authenticated': True,
                'username': request.user.username,
                'email': request.user.email,
                'role': prof.role if prof else 'CUSTOMER',
                'tasty_points': prof.tasty_points if prof else 0,
                'selected_region': prof.selected_region.slug if (prof and prof.selected_region) else None,
            })
        return Response({'authenticated': False})

    def post(self, request):
        action = request.data.get('action', 'login')
        if action == 'logout':
            logout(request)
            return Response({'status': 'logged_out'})
        username = request.data.get('username', '')
        password = request.data.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            prof = getattr(user, 'profile', None)
            return Response({
                'authenticated': True,
                'username': user.username,
                'role': prof.role if prof else 'CUSTOMER',
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)


class RegionSwitchAPIView(APIView):
    """
    /api/regions/ — Returns all dynamic regions or switches active region with full theme payload (Sections 71, 72, 88, 89).
    """
    def get(self, request):
        regions = Region.objects.select_related('theme').filter(is_active=True)
        current = get_active_region(request)
        return Response({
            'current_region': RegionSerializer(current).data if current else None,
            'regions': RegionSerializer(regions, many=True).data,
        })

    def post(self, request):
        slug = request.data.get('region_slug', '').strip()
        request.session['has_chosen_region'] = True
        if slug == 'all-india':
            request.session['selected_region_slug'] = 'all-india'
            if request.user.is_authenticated and hasattr(request.user, 'profile'):
                request.user.profile.selected_region = None
                request.user.profile.has_chosen_region = True
                request.user.profile.save(update_fields=['selected_region', 'has_chosen_region'])
            return Response({
                'status': 'switched',
                'region_slug': 'all-india',
                'region_name': 'All India',
                'greeting': 'Welcome to Tasty Tap India 🇮🇳',
                'subheading': 'Explore authentic regional dishes and local food businesses across India.',
            })

        region = get_object_or_404(Region.objects.select_related('theme'), slug=slug, is_active=True)
        request.session['selected_region_slug'] = region.slug
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            request.user.profile.selected_region = region
            request.user.profile.has_chosen_region = True
            request.user.profile.save(update_fields=['selected_region', 'has_chosen_region'])

        businesses = Business.objects.filter(status='APPROVED', region=region).select_related('profile', 'region')[:8]
        foods = FoodItem.objects.filter(is_available=True, business__status='APPROVED').filter(
            Q(region=region) | Q(business__region=region)
        ).select_related('business', 'category', 'region')[:8]

        return Response({
            'status': 'switched',
            'region': RegionSerializer(region).data,
            'businesses': BusinessSerializer(businesses, many=True).data,
            'foods': FoodItemSerializer(foods, many=True).data,
        })


class BusinessListAPIView(APIView):
    """
    /api/businesses/ — Lists approved local food businesses with regional & category filtering (Section 54).
    """
    def get(self, request):
        qs = Business.objects.filter(status='APPROVED').select_related('region', 'profile', 'category')
        region_slug = request.GET.get('region')
        if region_slug and region_slug != 'all-india':
            qs = qs.filter(region__slug=region_slug)
        btype = request.GET.get('type')
        if btype:
            qs = qs.filter(business_type=btype.upper())
        diet = request.GET.get('diet')
        if diet in ('VEG', 'NON_VEG'):
            qs = qs.filter(dietary_type=diet)
        q = request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(name__icontains=q) | Q(cuisine__icontains=q) | Q(city__icontains=q) | Q(area__icontains=q)
            )
        return Response(BusinessSerializer(qs[:40], many=True).data)


class BusinessDetailAPIView(APIView):
    """
    /api/businesses/<id>/ — Detailed business storefront & menu items (Section 54).
    """
    def get(self, request, pk):
        business = get_object_or_404(Business.objects.select_related('region', 'profile'), pk=pk)
        foods = business.food_items.filter(is_available=True).select_related('category', 'region')
        data = BusinessSerializer(business).data
        data['menu'] = FoodItemSerializer(foods, many=True).data
        return Response(data)


class FoodListAPIView(APIView):
    """
    /api/foods/ — Lists food items with filters for region, category, veg/non-veg, price, search (Section 54).
    """
    def get(self, request):
        qs = FoodItem.objects.filter(is_available=True, business__status='APPROVED').select_related(
            'business', 'category', 'region'
        ).prefetch_related('customizations')

        region_slug = request.GET.get('region')
        if region_slug and region_slug != 'all-india':
            qs = qs.filter(Q(region__slug=region_slug) | Q(business__region__slug=region_slug))

        cat_slug = request.GET.get('category')
        if cat_slug and cat_slug != 'all':
            qs = qs.filter(Q(category__slug=cat_slug) | Q(category__name__icontains=cat_slug))

        veg = request.GET.get('veg')
        if veg in ('VEG', 'NON_VEG'):
            qs = qs.filter(veg_type=veg)

        max_price = request.GET.get('max_price')
        if max_price and max_price.isdigit():
            qs = qs.filter(price__lte=Decimal(max_price))

        q = request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(description__icontains=q)
                | Q(business__name__icontains=q)
                | Q(category__name__icontains=q)
            )

        return Response(FoodItemSerializer(qs[:48], many=True).data)


class CategoryListAPIView(APIView):
    """
    /api/categories/ — Food categories list (Section 54).
    """
    def get(self, request):
        categories = FoodCategory.objects.filter(is_active=True)
        return Response(FoodCategorySerializer(categories, many=True).data)


class CartAPIView(APIView):
    """
    /api/cart/ — Multi-Vendor Smart Cart API (Sections 9, 37, 54).
    Enforces single-business per order with explicit conflict prompt & resolution.
    """
    def get(self, request):
        cart = get_or_create_cart(request)
        return Response(serialize_cart_payload(cart))

    def post(self, request):
        cart = get_or_create_cart(request)
        action = request.data.get('action', 'add')

        if action == 'clear':
            cart.items.all().delete()
            cart.business = None
            cart.applied_coupon = None
            cart.redeem_points = 0
            cart.save()
            return Response({'status': 'cleared', 'cart': serialize_cart_payload(cart)})

        if action == 'apply_coupon':
            code = (request.data.get('code') or '').strip().upper()
            coupon = Coupon.objects.filter(code__iexact=code, is_active=True).first()
            if not coupon:
                return Response({'error': 'Invalid or expired coupon code.'}, status=status.HTTP_400_BAD_REQUEST)
            if cart.get_subtotal() < coupon.min_order_amount:
                return Response({
                    'error': f'Minimum order of ₹{coupon.min_order_amount} required for {coupon.code}.'
                }, status=status.HTTP_400_BAD_REQUEST)
            if coupon.business_id and cart.business_id and coupon.business_id != cart.business_id:
                return Response({
                    'error': f'Coupon {coupon.code} is only valid for {coupon.business.name}.'
                }, status=status.HTTP_400_BAD_REQUEST)
            cart.applied_coupon = coupon
            cart.save(update_fields=['applied_coupon'])
            return Response({
                'status': 'coupon_applied',
                'message': f'Coupon {coupon.code} applied!',
                'cart': serialize_cart_payload(cart)
            })

        if action == 'toggle_points':
            use_points = bool(request.data.get('use_points', False))
            if use_points and request.user.is_authenticated and hasattr(request.user, 'profile'):
                cart.redeem_points = min(request.user.profile.tasty_points, 100)
            else:
                cart.redeem_points = 0
            cart.save(update_fields=['redeem_points'])
            return Response({'status': 'points_updated', 'cart': serialize_cart_payload(cart)})

        if action == 'update_qty':
            item_id = request.data.get('item_id')
            food_id = request.data.get('food_id')
            delta = int(request.data.get('delta', 0))
            if item_id:
                cart_item = cart.items.filter(id=item_id).first()
            else:
                cart_item = cart.items.filter(food_item_id=food_id).first()

            if cart_item:
                new_qty = cart_item.quantity + delta
                if new_qty <= 0:
                    cart_item.delete()
                    if not cart.items.exists():
                        cart.business = None
                        cart.applied_coupon = None
                        cart.save(update_fields=['business', 'applied_coupon'])
                else:
                    cart_item.quantity = min(25, new_qty)
                    cart_item.save(update_fields=['quantity'])
            return Response({'status': 'updated', 'cart': serialize_cart_payload(cart)})

        # Default action == 'add' or 'add_bundle'
        if action == 'add_bundle':
            food_ids = request.data.get('food_ids', [])
            force_replace = bool(request.data.get('force_replace', False))
            if force_replace:
                cart.items.all().delete()
                cart.business = None
            added_names = []
            for entry in food_ids:
                fid = entry.get('food_id') if isinstance(entry, dict) else entry
                qty = int(entry.get('quantity', 1)) if isinstance(entry, dict) else 1
                food = FoodItem.objects.select_related('business').filter(id=fid, is_available=True).first()
                if not food:
                    continue
                if cart.business_id and cart.business_id != food.business_id and cart.items.exists():
                    if not force_replace:
                        return Response({
                            'conflict': True,
                            'current_business': cart.business.name,
                            'new_business': food.business.name,
                            'message': "You're ordering from another business. Food from different businesses will be placed in separate orders.",
                        }, status=status.HTTP_409_CONFLICT)
                cart.business = food.business
                cart.save(update_fields=['business'])
                ci, created = CartItem.objects.get_or_create(
                    cart=cart,
                    food_item=food,
                    selected_size='Regular',
                    selected_spice=food.get_spice_level_display(),
                    selected_addons='',
                    defaults={'quantity': qty}
                )
                if not created:
                    ci.quantity += qty
                    ci.save(update_fields=['quantity'])
                added_names.append(food.name)
            return Response({
                'status': 'added_bundle',
                'added': added_names,
                'cart': serialize_cart_payload(cart),
            })

        food_id = request.data.get('food_id')
        food = get_object_or_404(FoodItem.objects.select_related('business'), id=food_id)
        if not food.is_available or food.stock_quantity <= 0:
            return Response({'error': 'This item is currently unavailable.'}, status=status.HTTP_400_BAD_REQUEST)

        force_separate = bool(request.data.get('force_separate', False))

        # Check Multi-Vendor Cart rule (Section 9)
        if cart.business_id and cart.business_id != food.business_id and cart.items.exists():
            if not force_separate:
                return Response({
                    'conflict': True,
                    'current_business': cart.business.name,
                    'new_business': food.business.name,
                    'food_id': food.id,
                    'message': "You're ordering from another business. Food from different businesses will be placed in separate orders.",
                }, status=status.HTTP_409_CONFLICT)
            else:
                cart.items.all().delete()
                cart.applied_coupon = None
                cart.redeem_points = 0

        cart.business = food.business
        cart.save(update_fields=['business'])

        quantity = max(1, int(request.data.get('quantity', 1)))
        selected_size = request.data.get('size', 'Regular')
        selected_spice = request.data.get('spice', food.get_spice_level_display())
        selected_addons = request.data.get('addons', '')
        addon_price = Decimal(str(request.data.get('addon_price', '0.00')))

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            food_item=food,
            selected_size=selected_size,
            selected_spice=selected_spice,
            selected_addons=selected_addons,
            defaults={
                'quantity': quantity,
                'addon_unit_price': addon_price,
            }
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.addon_unit_price = addon_price
            cart_item.save(update_fields=['quantity', 'addon_unit_price'])

        return Response({
            'status': 'added',
            'message': f'Added {food.name} to your cart!',
            'cart': serialize_cart_payload(cart),
        })


class OrderAPIView(APIView):
    """
    /api/orders/ — Lists user/business orders or updates live order status (Section 54).
    """
    def get(self, request):
        order_num = request.GET.get('order_number')
        if order_num:
            order = get_object_or_404(Order.objects.prefetch_related('items'), order_number=order_num)
            data = OrderSerializer(order).data
            delivery = getattr(order, 'delivery', None)
            if delivery:
                data['delivery'] = DeliverySerializer(delivery).data
            return Response(data)

        if request.user.is_authenticated:
            orders = Order.objects.filter(customer=request.user).prefetch_related('items')[:20]
            return Response(OrderSerializer(orders, many=True).data)
        return Response([])


class PaymentAPIView(APIView):
    """
    /api/payments/ — Lists user payment records (Section 54).
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return Response([])
        payments = Payment.objects.filter(user=request.user).select_related('order')[:20]
        return Response(PaymentSerializer(payments, many=True).data)


class ReviewAPIView(APIView):
    """
    /api/reviews/ — Lists or creates verified customer reviews (Section 54).
    """
    def get(self, request):
        business_id = request.GET.get('business_id')
        qs = Review.objects.select_related('user', 'business', 'food_item')
        if business_id:
            qs = qs.filter(business_id=business_id)
        return Response(ReviewSerializer(qs[:30], many=True).data)


class OfferAPIView(APIView):
    """
    /api/offers/ — Active offers and coupons for the current region (Section 54).
    """
    def get(self, request):
        region = get_active_region(request)
        offers_qs = Offer.objects.filter(is_active=True, is_approved=True).select_related('business', 'region')
        if region:
            offers_qs = offers_qs.filter(Q(region=region) | Q(region__isnull=True))
        coupons_qs = Coupon.objects.filter(is_active=True)
        return Response({
            'offers': OfferSerializer(offers_qs[:15], many=True).data,
            'coupons': CouponSerializer(coupons_qs[:10], many=True).data,
        })


class RecommendationAPIView(APIView):
    """
    /api/recommendations/ — Region-aware Tasty AI Recommendations, TAP AI chat, & Smart Meal Builder (Sections 20, 21, 22, 54, 85, 86).
    """
    def get(self, request):
        region = get_active_region(request)
        recs = get_tasty_ai_recommendations(user=request.user, region=region, limit=8)
        return Response({
            'region': region.name if region else 'All India',
            'recommendations': [
                {
                    'food': FoodItemSerializer(r['food']).data,
                    'reason': r['reason'],
                    'match_score': r['match_score'],
                }
                for r in recs
            ]
        })

    def post(self, request):
        mode = request.data.get('mode', 'tap_ai')
        region = get_active_region(request)
        if mode == 'meal_builder':
            meal = build_smart_meal(
                budget=request.data.get('budget', 500),
                people=request.data.get('people', 2),
                cuisine=request.data.get('cuisine', ''),
                veg_type=request.data.get('veg_type', 'ANY'),
                spice_level=request.data.get('spice_level', 'ANY'),
                region=region,
            )
            for c in meal.get('courses', []):
                c.pop('food', None)
            return Response(meal)

        query = request.data.get('query', 'What should I eat?')
        ai_response = answer_tap_ai_query(query_text=query, region=region, user=request.user)
        return Response(ai_response)


class DeliveryAPIView(APIView):
    """
    /api/delivery/ — Live delivery tracking & Delivery Partner status updates (Sections 18, 25, 54).
    """
    def get(self, request):
        deliveries = Delivery.objects.select_related('order', 'order__business', 'partner')[:20]
        return Response(DeliverySerializer(deliveries, many=True).data)


class NotificationAPIView(APIView):
    """
    /api/notifications/ — Lists or marks notifications read (Section 52, 54).
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return Response([])
        notes = Notification.objects.filter(recipient=request.user)[:20]
        return Response(NotificationSerializer(notes, many=True).data)

    def post(self, request):
        if request.user.is_authenticated:
            Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'marked_read'})


class LiveSearchAPIView(APIView):
    """
    AJAX Live Search prioritizing current selected region with "Search All India" toggle (Sections 23, 87).
    Handles natural queries like "Chicken Biryani", "Hotels near me", "Food under ₹150", "Vegetarian", "Bakery", "Home food".
    """
    def get(self, request):
        q = (request.GET.get('q') or '').strip()
        all_india = request.GET.get('all_india', 'false').lower() in ('true', '1', 'yes')
        region = None if all_india else get_active_region(request)

        food_qs = FoodItem.objects.filter(is_available=True, business__status='APPROVED').select_related('business', 'category', 'region')
        biz_qs = Business.objects.filter(status='APPROVED').select_related('region', 'profile')

        ql = q.lower()
        if 'under' in ql:
            limit_val = 150
            for num in (60, 80, 100, 120, 150, 200, 250, 300):
                if str(num) in ql:
                    limit_val = num
                    break
            food_qs = food_qs.filter(price__lte=limit_val)
        elif ql in ('vegetarian', 'veg', 'pure veg'):
            food_qs = food_qs.filter(veg_type='VEG')
            biz_qs = biz_qs.filter(dietary_type='VEG')
        elif 'hotel' in ql:
            biz_qs = biz_qs.filter(business_type__in=['SMALL_HOTEL', 'RESTAURANT', 'TIFFIN_SERVICE'])
            food_qs = food_qs.filter(Q(business__business_type='SMALL_HOTEL') | Q(name__icontains=q))
        elif 'home food' in ql or 'home kitchen' in ql:
            biz_qs = biz_qs.filter(business_type='HOME_FOOD')
            food_qs = food_qs.filter(business__business_type='HOME_FOOD')
        elif 'bakery' in ql:
            biz_qs = biz_qs.filter(business_type='BAKERY')
            food_qs = food_qs.filter(Q(business__business_type='BAKERY') | Q(category__name__icontains='Bakery'))
        elif q:
            food_qs = food_qs.filter(
                Q(name__icontains=q)
                | Q(description__icontains=q)
                | Q(category__name__icontains=q)
                | Q(business__name__icontains=q)
                | Q(business__cuisine__icontains=q)
            )
            biz_qs = biz_qs.filter(
                Q(name__icontains=q)
                | Q(cuisine__icontains=q)
                | Q(city__icontains=q)
                | Q(business_type__icontains=q)
            )

        if region:
            reg_foods = list(food_qs.filter(Q(region=region) | Q(business__region=region))[:8])
            other_foods = list(food_qs.exclude(id__in=[f.id for f in reg_foods])[:4])
            foods = reg_foods + other_foods

            reg_biz = list(biz_qs.filter(region=region)[:6])
            other_biz = list(biz_qs.exclude(id__in=[b.id for b in reg_biz])[:3])
            businesses = reg_biz + other_biz
        else:
            foods = list(food_qs[:10])
            businesses = list(biz_qs[:8])

        return Response({
            'query': q,
            'prioritized_region': region.name if region else 'All India',
            'foods': FoodItemSerializer(foods, many=True).data,
            'businesses': BusinessSerializer(businesses, many=True).data,
        })


class WishlistToggleAPIView(APIView):
    """
    Toggles a FoodItem or Business in the customer's Wishlist (Section 29).
    """
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'Please log in to save favorites.'}, status=status.HTTP_401_UNAUTHORIZED)
        wishlist = get_or_create_wishlist(request.user)
        food_id = request.data.get('food_id')
        business_id = request.data.get('business_id')

        if food_id:
            food = get_object_or_404(FoodItem, id=food_id)
            if wishlist.food_items.filter(id=food.id).exists():
                wishlist.food_items.remove(food)
                saved = False
            else:
                wishlist.food_items.add(food)
                saved = True
            return Response({'status': 'ok', 'saved': saved, 'type': 'food', 'id': food.id})

        if business_id:
            biz = get_object_or_404(Business, id=business_id)
            if wishlist.businesses.filter(id=biz.id).exists():
                wishlist.businesses.remove(biz)
                saved = False
            else:
                wishlist.businesses.add(biz)
                saved = True
            return Response({'status': 'ok', 'saved': saved, 'type': 'business', 'id': biz.id})

        return Response({'error': 'Missing food_id or business_id'}, status=status.HTTP_400_BAD_REQUEST)
