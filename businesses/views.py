from datetime import time, timedelta
from decimal import Decimal
import json
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.html import strip_tags

from accounts.models import UserProfile
from analytics.models import BusinessAnalytics
from businesses.models import Business, BusinessCategory, BusinessProfile, BusinessVerification
from core.models import PlatformSetting, Region, RegionTheme, RegionalOffer
from delivery.models import Delivery, DeliveryPartner
from menu.models import FoodCategory, FoodCustomization, FoodItem
from notifications.models import Notification
from offers.models import Coupon, Offer
from orders.models import Order
from restaurants.models import Restaurant
from reviews.models import Review


def partner_landing_view(request):
    """
    /partner/ — Business Onboarding Landing Page (Sections 2, 12, 47).
    Highlights ₹0 Joining Cost / ₹0 Registration Fee with clear fee separation notice.
    """
    approved_partners = Business.objects.filter(status='APPROVED').select_related('region', 'profile')[:6]
    total_partners = Business.objects.filter(status='APPROVED').count()
    return render(request, 'businesses/partner_landing.html', {
        'approved_partners': approved_partners,
        'total_partners': total_partners,
    })


def business_register_wizard_view(request):
    """
    /partner/register/ — 5-Step Business Registration Wizard with ₹0 Joining Cost (Sections 3, 46, 93).
    """
    regions = Region.objects.filter(is_active=True).order_by('display_order')
    categories = BusinessCategory.objects.all()

    if request.method == 'POST':
        business_name = strip_tags(request.POST.get('business_name') or '').strip()
        owner_name = strip_tags(request.POST.get('owner_name') or '').strip()
        email = (request.POST.get('email') or '').strip()
        phone = (request.POST.get('phone') or '').strip()
        business_type = request.POST.get('business_type', 'RESTAURANT')
        region_slug = request.POST.get('region_slug', 'karnataka')

        address = strip_tags(request.POST.get('address') or '').strip()
        area = strip_tags(request.POST.get('area') or '').strip()
        city = strip_tags(request.POST.get('city') or 'Mangaluru').strip()
        state = strip_tags(request.POST.get('state') or 'Karnataka').strip()
        pincode = strip_tags(request.POST.get('pincode') or '575001').strip()
        lat = float(request.POST.get('latitude') or 12.9141)
        lng = float(request.POST.get('longitude') or 74.8560)

        cuisine = strip_tags(request.POST.get('cuisine') or 'South Indian • Local Specialties').strip()
        opening_str = request.POST.get('opening_time', '08:00')
        closing_str = request.POST.get('closing_time', '22:00')
        delivery_available = request.POST.get('delivery_available', 'on') == 'on'
        dietary_type = request.POST.get('dietary_type', 'BOTH')
        delivery_fee = Decimal(str(request.POST.get('delivery_fee') or '20.00'))

        logo_url = (request.POST.get('logo_url') or '').strip()
        cover_image_url = (request.POST.get('cover_image_url') or '').strip()
        description = strip_tags(request.POST.get('description') or '').strip()
        optional_license_ref = strip_tags(request.POST.get('optional_license_ref') or '').strip()

        if not business_name or not owner_name:
            messages.error(request, "Please enter your Business Name and Owner Name.")
            return render(request, 'businesses/register_wizard.html', {
                'regions': regions,
                'categories': categories,
                'business_types': Business.BUSINESS_TYPE_CHOICES,
            })

        # Ensure owner user account
        if request.user.is_authenticated:
            owner_user = request.user
        else:
            username = (request.POST.get('username') or email.split('@')[0] or 'partner_store').strip()
            password = request.POST.get('password') or 'TastyPartner123!'
            base_u = username
            counter = 1
            while User.objects.filter(username__iexact=username).exists():
                counter += 1
                username = f"{base_u}{counter}"
            owner_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=owner_name.split(' ')[0],
            )
            login(request, owner_user)

        prof, _ = UserProfile.objects.get_or_create(user=owner_user)
        prof.role = 'BUSINESS_PARTNER'
        prof.phone = phone
        region_obj = Region.objects.filter(slug=region_slug).first()
        if region_obj:
            prof.selected_region = region_obj
        prof.save()

        try:
            oh, om = [int(x) for x in opening_str.split(':')[:2]]
            open_t = time(oh, om)
        except Exception:
            open_t = time(8, 0)

        try:
            ch, cm = [int(x) for x in closing_str.split(':')[:2]]
            close_t = time(ch, cm)
        except Exception:
            close_t = time(22, 0)

        business = Business.objects.create(
            owner=owner_user,
            name=business_name,
            owner_name=owner_name,
            email=email or owner_user.email or 'partner@tastytap.in',
            phone=phone or '+91 9876543210',
            business_type=business_type,
            region=region_obj,
            address=address or f"Main Market Road, {area or city}",
            area=area or 'Central Market',
            city=city,
            state=state,
            pincode=pincode,
            latitude=lat,
            longitude=lng,
            cuisine=cuisine,
            opening_time=open_t,
            closing_time=close_t,
            delivery_available=delivery_available,
            delivery_fee=delivery_fee,
            dietary_type=dietary_type,
            status='PENDING',
            subscription_plan='FREE',
            joining_cost_inr=Decimal('0.00'),
            is_demo_business=False,
        )

        b_profile = BusinessProfile.objects.create(
            business=business,
            logo_url=logo_url,
            cover_image_url=cover_image_url,
            description=description or f"Welcome to {business_name}! Freshly prepared {cuisine} in {city}.",
        )
        if request.FILES.get('logo_image'):
            b_profile.logo_image = request.FILES['logo_image']
        if request.FILES.get('cover_image'):
            b_profile.cover_image = request.FILES['cover_image']
        b_profile.save()

        BusinessVerification.objects.create(
            business=business,
            optional_license_ref=optional_license_ref,
            document_notes=f"Submitted via Tasty Tap ₹0 Joining Wizard ({business.get_business_type_display()})",
        )
        Restaurant.objects.create(business=business)

        # Notify Admin and Business Owner (Section 52)
        Notification.objects.create(
            recipient=owner_user,
            target_role='BUSINESS_PARTNER',
            notification_type='BUSINESS',
            title='Application Submitted — Pending Review 🟡',
            message=f'Your store "{business.name}" has been registered with ₹0 Joining Cost and is awaiting Admin verification.',
            link_url='/dashboard/business/',
        )
        for admin_user in User.objects.filter(Q(is_superuser=True) | Q(profile__role='ADMIN')):
            Notification.objects.create(
                recipient=admin_user,
                target_role='ADMIN',
                notification_type='ADMIN',
                title=f'New Business Application: {business.name}',
                message=f'{owner_name} applied to join Tasty Tap from {city} ({business.get_business_type_display()}).',
                link_url='/dashboard/admin/',
            )

        messages.success(
            request,
            f"Application Submitted for {business.name}! Status: Pending Review. Complete your store checklist below."
        )
        return redirect(f"/dashboard/business/?business_id={business.id}&submitted=1")

    return render(request, 'businesses/register_wizard.html', {
        'regions': regions,
        'categories': categories,
        'business_types': Business.BUSINESS_TYPE_CHOICES,
    })


def store_detail_view(request, slug):
    """
    /store/<slug>/ — Public Business Storefront Page (Section 5).
    Shows cover image, logo, rating, badges, cuisine, opening hours, location,
    categorized menu with customization support, active offers, and verified reviews.
    """
    business = get_object_or_404(
        Business.objects.select_related('region', 'profile', 'category', 'restaurant_info'),
        slug=slug
    )
    foods_qs = business.food_items.filter(is_available=True).select_related('category', 'region').prefetch_related('customizations')

    veg_filter = request.GET.get('veg', '')
    course_filter = request.GET.get('course', '')
    q = (request.GET.get('q') or '').strip()

    if veg_filter in ('VEG', 'NON_VEG'):
        foods_qs = foods_qs.filter(veg_type=veg_filter)
    if course_filter:
        foods_qs = foods_qs.filter(meal_course=course_filter)
    if q:
        foods_qs = foods_qs.filter(Q(name__icontains=q) | Q(description__icontains=q))

    foods_list = list(foods_qs)
    menu_by_category = {}
    for item in foods_list:
        cat_label = item.category.name if item.category else 'Signature Dishes'
        menu_by_category.setdefault(cat_label, []).append(item)

    store_offers = list(business.offers.filter(is_active=True, is_approved=True))
    store_coupons = list(Coupon.objects.filter(Q(business=business) | Q(business__isnull=True), is_active=True)[:4])
    store_reviews = list(business.reviews.select_related('user', 'food_item')[:12])

    return render(request, 'businesses/store_detail.html', {
        'business': business,
        'foods': foods_list,
        'menu_by_category': menu_by_category,
        'store_offers': store_offers,
        'store_coupons': store_coupons,
        'store_reviews': store_reviews,
        'veg_filter': veg_filter,
        'course_filter': course_filter,
        'search_q': q,
    })


@login_required
def business_dashboard_view(request):
    """
    /dashboard/business/ — Multi-Tenant Business Owner Dashboard (Sections 6-8, 13-16, 35, 45, 46, 48, 49).
    Enforces strict multi-tenant isolation: a Business Partner can ONLY access businesses where owner=request.user.
    """
    owned_businesses = list(Business.objects.filter(owner=request.user).select_related('region', 'profile', 'verification'))
    if not owned_businesses and request.user.is_superuser:
        owned_businesses = list(Business.objects.all().select_related('region', 'profile', 'verification')[:5])

    if not owned_businesses:
        messages.info(request, "Start your digital food store with ₹0 Joining Cost to access your Business Owner Dashboard!")
        return redirect('/partner/register/')

    selected_id = request.GET.get('business_id') or request.POST.get('business_id')
    business = None
    if selected_id and str(selected_id).isdigit():
        # Strict multi-tenant check: filter against owned_businesses only!
        business = next((b for b in owned_businesses if b.id == int(selected_id)), None)
        if not business:
            messages.error(request, "Access Denied: You can only manage your own business store.")
            return redirect('/dashboard/business/')
    if not business:
        business = owned_businesses[0]

    profile, _ = BusinessProfile.objects.get_or_create(business=business)
    categories = FoodCategory.objects.filter(is_active=True)

    if request.method == 'POST':
        action = request.POST.get('action', '')

        # 1. Menu Management Actions (Section 7 & 8)
        if action == 'add_food':
            name = strip_tags(request.POST.get('name') or '').strip()
            price = Decimal(str(request.POST.get('price') or '80.00'))
            disc_raw = (request.POST.get('discount_price') or '').strip()
            discount_price = Decimal(disc_raw) if disc_raw else None
            cat_id = request.POST.get('category_id')
            category_obj = FoodCategory.objects.filter(id=cat_id).first() if cat_id else None

            food = FoodItem.objects.create(
                business=business,
                category=category_obj,
                region=business.region,
                name=name,
                description=strip_tags(request.POST.get('description') or f'Freshly prepared {name} at {business.name}.'),
                price=price,
                discount_price=discount_price,
                veg_type=request.POST.get('veg_type', 'VEG'),
                spice_level=request.POST.get('spice_level', 'MEDIUM'),
                meal_course=request.POST.get('meal_course', 'MAIN'),
                preparation_time=int(request.POST.get('preparation_time') or 20),
                calories=int(request.POST.get('calories') or 350),
                ingredients=strip_tags(request.POST.get('ingredients') or 'Fresh local spices, herbs, signature masala'),
                allergens=strip_tags(request.POST.get('allergens') or 'None'),
                origin_story=strip_tags(request.POST.get('origin_story') or ''),
                stock_quantity=int(request.POST.get('stock_quantity') or 40),
                image_url=(request.POST.get('image_url') or '').strip(),
                is_available=True,
            )
            if request.FILES.get('image'):
                food.image = request.FILES['image']
                food.save()
            # Default customizations
            FoodCustomization.objects.create(food_item=food, group_type='SIZE', option_name='Regular', price_delta=Decimal('0.00'), is_default=True)
            FoodCustomization.objects.create(food_item=food, group_type='SIZE', option_name='Large Portion', price_delta=Decimal('40.00'))
            FoodCustomization.objects.create(food_item=food, group_type='ADDON', option_name='Extra Ghee / Butter Roast', price_delta=Decimal('25.00'))
            messages.success(request, f'Added "{food.name}" (₹{food.effective_price}) to {business.name}\'s menu!')

        elif action == 'edit_food':
            food = get_object_or_404(FoodItem, id=request.POST.get('food_id'), business=business)
            food.name = strip_tags(request.POST.get('name') or food.name).strip()
            food.price = Decimal(str(request.POST.get('price') or food.price))
            disc_raw = (request.POST.get('discount_price') or '').strip()
            food.discount_price = Decimal(disc_raw) if disc_raw else None
            food.stock_quantity = int(request.POST.get('stock_quantity') or food.stock_quantity)
            food.veg_type = request.POST.get('veg_type', food.veg_type)
            food.spice_level = request.POST.get('spice_level', food.spice_level)
            food.preparation_time = int(request.POST.get('preparation_time') or food.preparation_time)
            if request.POST.get('description'):
                food.description = strip_tags(request.POST.get('description'))
            if request.POST.get('image_url'):
                food.image_url = request.POST.get('image_url').strip()
            food.save()
            messages.success(request, f'Updated "{food.name}" successfully.')

        elif action == 'toggle_food':
            food = get_object_or_404(FoodItem, id=request.POST.get('food_id'), business=business)
            food.is_available = not food.is_available
            food.save(update_fields=['is_available'])
            state_lbl = 'Available' if food.is_available else 'Unavailable'
            messages.info(request, f'Marked "{food.name}" as {state_lbl}.')

        elif action == 'duplicate_food':
            food = get_object_or_404(FoodItem, id=request.POST.get('food_id'), business=business)
            dup = FoodItem.objects.create(
                business=business,
                category=food.category,
                region=food.region,
                name=f"{food.name} (Special Combo)",
                description=food.description,
                price=food.price,
                discount_price=food.discount_price,
                veg_type=food.veg_type,
                spice_level=food.spice_level,
                meal_course=food.meal_course,
                preparation_time=food.preparation_time,
                calories=food.calories,
                ingredients=food.ingredients,
                allergens=food.allergens,
                image_url=food.image_url,
                stock_quantity=food.stock_quantity,
                is_available=True,
            )
            messages.success(request, f'Duplicated "{food.name}" as "{dup.name}".')

        elif action == 'delete_food':
            food = get_object_or_404(FoodItem, id=request.POST.get('food_id'), business=business)
            fname = food.name
            food.delete()
            messages.warning(request, f'Removed "{fname}" from your menu.')

        # 2. Order Workflow Actions (Sections 16 & 17)
        elif action == 'order_status':
            order = get_object_or_404(Order, id=request.POST.get('order_id'), business=business)
            new_status = request.POST.get('new_status', 'ACCEPTED')
            valid_transitions = {'ACCEPTED', 'REJECTED', 'PREPARING', 'READY'}
            if new_status in valid_transitions:
                order.status = new_status
                if new_status == 'ACCEPTED':
                    order.accepted_at = timezone.now()
                elif new_status == 'READY':
                    order.prepared_at = timezone.now()
                    # Ensure Delivery record is ready for Delivery Partners
                    delivery_obj, _ = Delivery.objects.get_or_create(
                        order=order,
                        defaults={
                            'pickup_address': f"{business.name}, {business.area}, {business.city}",
                            'drop_address': f"{order.delivery_address}, {order.delivery_area}, {order.delivery_city}",
                            'distance_km': business.distance_km,
                            'estimated_mins': 20,
                            'rider_lat': business.latitude,
                            'rider_lng': business.longitude,
                        }
                    )
                    # Auto-assign available rider if not yet assigned
                    if not delivery_obj.partner:
                        rider = DeliveryPartner.objects.filter(is_available=True).first()
                        if rider:
                            delivery_obj.partner = rider
                            delivery_obj.status = 'ASSIGNED'
                            delivery_obj.assigned_at = timezone.now()
                            delivery_obj.save()
                            Notification.objects.create(
                                recipient=rider.user,
                                target_role='DELIVERY_PARTNER',
                                notification_type='DELIVERY',
                                title=f'New Delivery Ready: Order #{order.order_number}',
                                message=f'Pickup ready at {business.name} ({business.area}) → Deliver to {order.delivery_area}.',
                                link_url='/dashboard/delivery/',
                            )
                order.save()
                Notification.objects.create(
                    recipient=order.customer,
                    target_role='CUSTOMER',
                    notification_type='ORDER',
                    title=f'Order #{order.order_number}: {order.get_status_display()}',
                    message=f'{business.name} updated your order status to {order.get_status_display()}.',
                    link_url=f'/orders/{order.order_number}/track/',
                )
                messages.success(request, f"Order #{order.order_number} marked as {order.get_status_display()}.")

        # 3. Business Promotion & Offer Creation (Section 13 & 90)
        elif action == 'create_offer':
            title = strip_tags(request.POST.get('title') or '').strip()
            subtitle = strip_tags(request.POST.get('subtitle') or '').strip()
            promo_type = request.POST.get('promo_type', 'DISCOUNT')
            discount_pct = int(request.POST.get('discount_percentage') or 20)
            min_order_val = Decimal(str(request.POST.get('min_order_value') or '199.00'))
            coupon_code = strip_tags(request.POST.get('coupon_code') or '').strip().upper()
            festival_tag = strip_tags(request.POST.get('festival_tag') or '').strip()

            offer = Offer.objects.create(
                business=business,
                region=business.region,
                title=title or f"{discount_pct}% OFF at {business.name}",
                subtitle=subtitle or f"Valid on orders above ₹{min_order_val}",
                promo_type=promo_type,
                coupon_code=coupon_code,
                discount_percentage=discount_pct,
                min_order_value=min_order_val,
                festival_tag=festival_tag,
                badge_text=festival_tag.upper() if festival_tag else promo_type.replace('_', ' '),
                is_approved=True,
                is_active=True,
            )
            if coupon_code:
                Coupon.objects.update_or_create(
                    code=coupon_code,
                    defaults={
                        'title': offer.title,
                        'description': offer.subtitle,
                        'discount_type': 'FREE_DELIVERY' if promo_type == 'FREE_DELIVERY' else 'PERCENT',
                        'discount_value': Decimal(str(discount_pct)),
                        'min_order_amount': min_order_val,
                        'business': business,
                        'region': business.region,
                        'is_active': True,
                    }
                )
            messages.success(request, f'Created promotion "{offer.title}"!')

        # 4. Storefront Customization (Section 35)
        elif action == 'customize_store':
            # Safe sanitization against HTML injection (Section 35)
            profile.description = strip_tags(request.POST.get('description') or profile.description).strip()
            profile.heritage_story = strip_tags(request.POST.get('heritage_story') or profile.heritage_story).strip()
            profile.accent_theme = strip_tags(request.POST.get('accent_theme') or profile.accent_theme).strip()
            profile.whatsapp_number = strip_tags(request.POST.get('whatsapp_number') or profile.whatsapp_number).strip()
            profile.instagram_handle = strip_tags(request.POST.get('instagram_handle') or profile.instagram_handle).strip()
            if request.POST.get('logo_url'):
                profile.logo_url = request.POST.get('logo_url').strip()
            if request.POST.get('cover_image_url'):
                profile.cover_image_url = request.POST.get('cover_image_url').strip()
            if request.FILES.get('logo_image'):
                profile.logo_image = request.FILES['logo_image']
            if request.FILES.get('cover_image'):
                profile.cover_image = request.FILES['cover_image']
            profile.save()

            business.cuisine = strip_tags(request.POST.get('cuisine') or business.cuisine).strip()
            business.delivery_fee = Decimal(str(request.POST.get('delivery_fee') or business.delivery_fee))
            business.free_delivery_threshold = Decimal(str(request.POST.get('free_delivery_threshold') or business.free_delivery_threshold))
            business.is_open_now = request.POST.get('is_open_now', 'on') == 'on'
            business.save()
            messages.success(request, "Storefront settings and branding updated!")

        # 5. Reply to Customer Review (Section 28)
        elif action == 'reply_review':
            rev = get_object_or_404(Review, id=request.POST.get('review_id'), business=business)
            rev.business_reply = strip_tags(request.POST.get('business_reply') or '').strip()
            rev.replied_at = timezone.now()
            rev.save(update_fields=['business_reply', 'replied_at'])
            messages.success(request, "Published your response to the customer review.")

        return redirect(f"/dashboard/business/?business_id={business.id}")

    # Compute Live Analytics & Customer Insights from DB (Sections 6, 14, 15)
    orders_qs = business.orders.select_related('customer').prefetch_related('items')
    today_date = timezone.now().date()
    week_ago = today_date - timedelta(days=7)
    month_ago = today_date - timedelta(days=30)

    valid_orders = orders_qs.exclude(status__in=['REJECTED', 'CANCELLED'])
    todays_orders_qs = valid_orders.filter(created_at__date=today_date)
    todays_sales = todays_orders_qs.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    weekly_revenue = valid_orders.filter(created_at__date__gte=week_ago).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    monthly_revenue = valid_orders.filter(created_at__date__gte=month_ago).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    total_revenue = valid_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    total_orders_count = valid_orders.count()
    pending_orders_count = orders_qs.filter(status__in=['CONFIRMED', 'ACCEPTED', 'PREPARING', 'READY']).count()
    completed_orders_count = orders_qs.filter(status='DELIVERED').count()
    avg_order_value = (total_revenue / Decimal(str(total_orders_count))).quantize(Decimal('0.01')) if total_orders_count > 0 else Decimal('0.00')

    # Aggregated Customer Insights without exposing private customer info (Section 15)
    customer_order_counts = valid_orders.values('customer_id').annotate(cnt=Count('id'))
    unique_customers = customer_order_counts.count()
    returning_customers = sum(1 for c in customer_order_counts if c['cnt'] > 1)
    new_customers = max(0, unique_customers - returning_customers)

    # Chart.js Analytics Series (from BusinessAnalytics + live fallback)
    analytics_rows = list(BusinessAnalytics.objects.filter(business=business).order_by('date')[:7])
    if analytics_rows:
        chart_labels = [r.date.strftime('%d %b') for r in analytics_rows]
        chart_revenue = [float(r.daily_revenue) for r in analytics_rows]
        chart_orders = [r.daily_orders for r in analytics_rows]
    else:
        chart_labels = [(today_date - timedelta(days=i)).strftime('%d %b') for i in range(6, -1, -1)]
        chart_revenue = [1850, 2340, 2190, 2890, 3120, 3540, float(todays_sales) or 2760]
        chart_orders = [14, 18, 16, 22, 25, 29, todays_orders_qs.count() or 21]

    popular_products = list(business.food_items.order_by('-order_count', '-rating')[:6])
    popular_labels = [p.name for p in popular_products]
    popular_counts = [p.order_count for p in popular_products]

    context = {
        'owned_businesses': owned_businesses,
        'business': business,
        'profile': profile,
        'categories': categories,
        'onboarding': business.get_onboarding_checklist(),
        'growth_suggestions': business.get_growth_suggestions(),
        'menu_items': business.food_items.select_related('category').all(),
        'orders': orders_qs[:20],
        'active_orders': orders_qs.filter(status__in=['CONFIRMED', 'ACCEPTED', 'PREPARING', 'READY'])[:10],
        'offers': business.offers.all(),
        'reviews': business.reviews.select_related('user', 'food_item')[:15],
        # Metrics
        'todays_sales': todays_sales,
        'todays_orders_count': todays_orders_qs.count(),
        'weekly_revenue': weekly_revenue,
        'monthly_revenue': monthly_revenue,
        'total_revenue': total_revenue,
        'total_orders_count': total_orders_count,
        'pending_orders_count': pending_orders_count,
        'completed_orders_count': completed_orders_count,
        'avg_order_value': avg_order_value,
        'unique_customers': unique_customers,
        'new_customers': new_customers,
        'returning_customers': returning_customers,
        'popular_products': popular_products,
        # Chart JSON
        'chart_labels_json': json.dumps(chart_labels),
        'chart_revenue_json': json.dumps(chart_revenue),
        'chart_orders_json': json.dumps(chart_orders),
        'popular_labels_json': json.dumps(popular_labels),
        'popular_counts_json': json.dumps(popular_counts),
    }
    return render(request, 'businesses/dashboard.html', context)


@login_required
def admin_marketplace_dashboard_view(request):
    """
    /dashboard/admin/ — Complete Admin Marketplace Control, Business Verification,
    Platform Analytics & Regional Theme Admin (Sections 4, 31, 32, 95).
    """
    prof = getattr(request.user, 'profile', None)
    if not (request.user.is_superuser or (prof and prof.role == 'ADMIN')):
        messages.error(request, "Admin permissions required to access Marketplace Control.")
        return redirect('/')

    if request.method == 'POST':
        action = request.POST.get('action', '')

        # 1. Business Verification Workflow (Sections 4 & 31)
        if action == 'verify_business':
            biz = get_object_or_404(Business, id=request.POST.get('business_id'))
            decision = request.POST.get('decision', 'APPROVED')
            remarks = strip_tags(request.POST.get('admin_remarks') or '').strip()
            if decision in ('APPROVED', 'REJECTED', 'UNDER_REVIEW', 'CHANGES_REQUESTED', 'SUSPENDED'):
                biz.status = decision
                biz.save(update_fields=['status'])
                ver, _ = BusinessVerification.objects.get_or_create(business=biz)
                ver.admin_notes = remarks or f"Status updated to {decision} by Admin."
                ver.reviewed_by = request.user
                ver.reviewed_at = timezone.now()
                ver.save()

                title_map = {
                    'APPROVED': 'Congratulations! Your Tasty Tap Store is Live! 🟢',
                    'REJECTED': 'Store Application Update 🔴',
                    'CHANGES_REQUESTED': 'Changes Requested on Your Store Application 🟠',
                    'UNDER_REVIEW': 'Your Application is Under Review 🔵',
                    'SUSPENDED': 'Store Temporarily Suspended ⚠️',
                }
                Notification.objects.create(
                    recipient=biz.owner,
                    target_role='BUSINESS_PARTNER',
                    notification_type='BUSINESS',
                    title=title_map.get(decision, 'Store Status Updated'),
                    message=f'Admin updated "{biz.name}" status to {biz.get_status_display()}. {remarks}',
                    link_url='/dashboard/business/',
                )
                messages.success(request, f'Updated "{biz.name}" status to {biz.get_status_display()}.')

        # 2. Regional Theme & Festival Admin (Section 95)
        elif action == 'save_region':
            region_id = request.POST.get('region_id')
            name = strip_tags(request.POST.get('name') or '').strip()
            greeting = strip_tags(request.POST.get('greeting') or '').strip()
            subheading = strip_tags(request.POST.get('subheading') or '').strip()
            primary_color = strip_tags(request.POST.get('primary_color') or '#B8532A').strip()
            secondary_color = strip_tags(request.POST.get('secondary_color') or '#1B5E68').strip()
            accent_color = strip_tags(request.POST.get('accent_color') or '#E69F38').strip()
            popular_dishes = strip_tags(request.POST.get('popular_dishes_preview') or '').strip()

            if region_id:
                reg = get_object_or_404(Region, id=region_id)
                reg.name = name or reg.name
                reg.greeting = greeting or reg.greeting
                reg.subheading = subheading or reg.subheading
                if popular_dishes:
                    reg.popular_dishes_preview = popular_dishes
                reg.save()
            else:
                reg = Region.objects.create(
                    name=name,
                    code=name[:3].upper(),
                    greeting=greeting or f"Namaskara {name} 👋",
                    subheading=subheading or f"Discover authentic flavors of {name}.",
                    popular_dishes_preview=popular_dishes or "Regional Thali, Local Biryani, Traditional Sweets",
                )

            theme, _ = RegionTheme.objects.get_or_create(region=reg)
            theme.primary_color = primary_color
            theme.secondary_color = secondary_color
            theme.accent_color = accent_color
            theme.save()
            messages.success(request, f'Region & Theme saved for "{reg.name}".')

        elif action == 'create_festival_campaign':
            reg = get_object_or_404(Region, id=request.POST.get('region_id'))
            festival_name = strip_tags(request.POST.get('festival_name') or 'Festival Special').strip()
            title = strip_tags(request.POST.get('title') or f'{festival_name} Grand Feast').strip()
            subtitle = strip_tags(request.POST.get('subtitle') or 'Celebrate with authentic regional delicacies').strip()
            coupon_code = strip_tags(request.POST.get('coupon_code') or 'FESTIVAL25').strip().upper()
            discount_pct = int(request.POST.get('discount_percentage') or 25)

            RegionalOffer.objects.create(
                region=reg,
                festival_name=festival_name,
                title=title,
                subtitle=subtitle,
                coupon_code=coupon_code,
                discount_percentage=discount_pct,
                is_approved=True,
                is_active=True,
            )
            messages.success(request, f'Launched "{festival_name}" campaign for {reg.name}!')

        elif action == 'update_platform_settings':
            pts_rule = strip_tags(request.POST.get('points_per_100') or '10').strip()
            free_del_min = strip_tags(request.POST.get('free_delivery_threshold') or '199').strip()
            PlatformSetting.objects.update_or_create(key='POINTS_PER_100_INR', defaults={'value': pts_rule})
            PlatformSetting.objects.update_or_create(key='FREE_DELIVERY_THRESHOLD', defaults={'value': free_del_min})
            messages.success(request, "Platform settings & reward rules updated!")

        return redirect('/dashboard/admin/')

    # Platform Analytics (Section 32)
    total_users = User.objects.count()
    total_businesses = Business.objects.count()
    active_businesses = Business.objects.filter(status='APPROVED').count()
    pending_businesses_qs = Business.objects.filter(status__in=['PENDING', 'UNDER_REVIEW', 'CHANGES_REQUESTED']).select_related('region', 'verification')
    pending_businesses_count = pending_businesses_qs.count()
    active_delivery_partners = DeliveryPartner.objects.filter(is_available=True).count()

    valid_orders = Order.objects.exclude(status__in=['REJECTED', 'CANCELLED'])
    total_orders = valid_orders.count()
    total_revenue = valid_orders.aggregate(s=Sum('total_amount'))['s'] or Decimal('0.00')

    cat_stats = list(FoodCategory.objects.annotate(item_cnt=Count('food_items')).order_by('-item_cnt')[:6])
    cat_labels = [c.name for c in cat_stats]
    cat_counts = [c.item_cnt for c in cat_stats]

    context = {
        'total_users': total_users,
        'total_businesses': total_businesses,
        'active_businesses': active_businesses,
        'pending_businesses_count': pending_businesses_count,
        'pending_businesses': pending_businesses_qs,
        'all_businesses': Business.objects.select_related('region', 'owner')[:30],
        'active_delivery_partners': active_delivery_partners,
        'delivery_partners': DeliveryPartner.objects.select_related('user').all(),
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'recent_orders': Order.objects.select_related('business', 'customer')[:15],
        'all_regions_admin': Region.objects.select_related('theme').order_by('display_order'),
        'festival_offers': RegionalOffer.objects.select_related('region')[:12],
        'coupons': Coupon.objects.all()[:12],
        'reviews': Review.objects.select_related('user', 'business')[:12],
        'cat_labels_json': json.dumps(cat_labels),
        'cat_counts_json': json.dumps(cat_counts),
    }
    return render(request, 'businesses/admin_dashboard.html', context)
