import io
import urllib.request
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from core.context_processors import get_active_region
from core.models import Region, RegionalCategory, RegionalFood, RegionalOffer
from businesses.models import Business, BusinessCategory
from menu.models import FoodCategory, FoodItem
from offers.models import Coupon, Offer
from orders.models import Order
from reviews.models import Review
from recommendations.engine import get_tasty_ai_recommendations, build_smart_meal
from cart.utils import get_or_create_wishlist


def home_view(request):
    """
    Dynamic Regional & Multi-Vendor Marketplace Homepage (Sections 10, 11, 19-22, 65, 69-100).
    Adapts hero, colors, categories, coastal/regional favorites, local businesses, offers,
    and AI recommendations to the currently selected Region.
    """
    if request.GET.get('region'):
        slug = request.GET.get('region').strip()
        request.session['selected_region_slug'] = slug
        request.session['has_chosen_region'] = True
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            if slug == 'all-india':
                request.user.profile.selected_region = None
            else:
                reg_obj = Region.objects.filter(slug=slug, is_active=True).first()
                if reg_obj:
                    request.user.profile.selected_region = reg_obj
            request.user.profile.has_chosen_region = True
            request.user.profile.save(update_fields=['selected_region', 'has_chosen_region'])

    current_region = get_active_region(request)

    # Regional & Global Food Categories
    food_categories = list(FoodCategory.objects.filter(is_active=True).order_by('display_order')[:12])
    regional_categories = []
    if current_region:
        regional_categories = list(RegionalCategory.objects.filter(region=current_region).order_by('display_order')[:8])

    # Businesses Query (Prioritize current region first, then include popular nationwide stores)
    approved_businesses = Business.objects.filter(status='APPROVED').select_related('region', 'profile', 'category')

    # Filter query params on homepage if provided
    active_filter = request.GET.get('filter', '').strip()
    active_category = request.GET.get('category', '').strip()

    if current_region:
        regional_businesses = list(approved_businesses.filter(region=current_region)[:12])
        other_businesses = list(approved_businesses.exclude(region=current_region)[:6])
        nearby_businesses = regional_businesses if regional_businesses else other_businesses
    else:
        nearby_businesses = list(approved_businesses[:12])

    if active_filter == 'top_rated':
        nearby_businesses = sorted(nearby_businesses, key=lambda b: b.rating, reverse=True)
    elif active_filter == 'fast_delivery':
        nearby_businesses = sorted(nearby_businesses, key=lambda b: b.delivery_mins_numeric)
    elif active_filter == 'veg':
        nearby_businesses = [b for b in nearby_businesses if b.dietary_type == 'VEG']
    elif active_filter == 'budget':
        nearby_businesses = [b for b in nearby_businesses if b.price_range == '₹']
    elif active_filter == 'hotel':
        nearby_businesses = [b for b in nearby_businesses if b.business_type == 'SMALL_HOTEL']
    elif active_filter == 'cafe':
        nearby_businesses = [b for b in nearby_businesses if b.business_type == 'CAFE']
    elif active_filter == 'home_food':
        nearby_businesses = [b for b in nearby_businesses if b.business_type == 'HOME_FOOD']
    elif active_filter == 'bakery':
        nearby_businesses = [b for b in nearby_businesses if b.business_type == 'BAKERY']

    # Food items (Regional / Coastal Favorites & Trending Food)
    foods_qs = FoodItem.objects.filter(
        is_available=True,
        business__status='APPROVED'
    ).select_related('business', 'category', 'region').prefetch_related('customizations')

    if active_category:
        foods_qs = foods_qs.filter(
            Q(category__slug=active_category) | Q(category__name__icontains=active_category)
        )

    if current_region:
        reg_foods = list(foods_qs.filter(Q(region=current_region) | Q(business__region=current_region))[:12])
        extra_foods = list(foods_qs.exclude(id__in=[f.id for f in reg_foods])[:8])
        featured_foods = reg_foods + extra_foods[:max(0, 12 - len(reg_foods))]
    else:
        featured_foods = list(foods_qs[:12])

    # Coastal Favorites row specifically highlighting coastal/signature dishes
    coastal_favorites = list(
        FoodItem.objects.filter(
            is_available=True,
            business__status='APPROVED',
            is_coastal_favorite=True
        ).select_related('business', 'category', 'region').prefetch_related('customizations')[:8]
    )
    if len(coastal_favorites) < 4:
        coastal_favorites = featured_foods[:8]

    # Small Business Spotlight sections (Sections 11, 50, 82)
    small_hotels = list(approved_businesses.filter(business_type__in=['SMALL_HOTEL', 'TIFFIN_SERVICE'])[:4])
    home_food_businesses = list(approved_businesses.filter(business_type__in=['HOME_FOOD', 'CLOUD_KITCHEN'])[:4])
    hidden_gems = list(approved_businesses.filter(Q(is_hidden_gem=True) | Q(is_local_favorite=True))[:4])

    # AI Recommendations & Initial Smart Meal Builder preview
    ai_recommendations = get_tasty_ai_recommendations(user=request.user, region=current_region, limit=6)
    sample_meal_plan = build_smart_meal(budget=500, people=2, region=current_region)

    # Regional Offers & Festival Specials
    offers_qs = Offer.objects.filter(is_active=True, is_approved=True).select_related('business', 'region')
    if current_region:
        regional_offers = list(offers_qs.filter(Q(region=current_region) | Q(region__isnull=True))[:6])
        festival_campaigns = list(RegionalOffer.objects.filter(region=current_region, is_active=True)[:4])
        iconic_regional_foods = list(RegionalFood.objects.filter(region=current_region)[:6])
    else:
        regional_offers = list(offers_qs[:6])
        festival_campaigns = list(RegionalOffer.objects.filter(is_active=True)[:4])
        iconic_regional_foods = list(RegionalFood.objects.all()[:6])

    active_coupons = list(Coupon.objects.filter(is_active=True)[:4])

    # Customer recent orders & wishlist IDs
    recent_orders = []
    wishlisted_food_ids = set()
    wishlisted_business_ids = set()
    if request.user.is_authenticated:
        recent_orders = list(
            Order.objects.filter(customer=request.user)
            .select_related('business')
            .prefetch_related('items')[:3]
        )
        wishlist = get_or_create_wishlist(request.user)
        if wishlist:
            wishlisted_food_ids = set(wishlist.food_items.values_list('id', flat=True))
            wishlisted_business_ids = set(wishlist.businesses.values_list('id', flat=True))

    recent_reviews = list(
        Review.objects.select_related('user', 'business', 'food_item')
        .filter(business_rating__gte=4)[:6]
    )

    # Menu items for the "Our Menu" tabbed section (Breakfast / Lunch / Dinner / All)
    all_foods_list = list(
        FoodItem.objects.filter(is_available=True, business__status='APPROVED')
        .select_related('business', 'category', 'region')
        .prefetch_related('customizations')
    )
    if current_region:
        all_foods_list.sort(key=lambda f: (0 if (f.region_id == current_region.id or f.business.region_id == current_region.id) else 1, -int(f.is_bestseller), f.id))

    # Map markers for the interactive Homepage Map section
    all_approved_list = list(approved_businesses)
    if current_region:
        all_approved_list.sort(key=lambda b: (0 if b.region_id == current_region.id else 1, -float(b.rating)))

    home_map_markers = []
    for b in all_approved_list:
        prof = getattr(b, 'profile', None)
        home_map_markers.append({
            'id': b.id,
            'name': b.name,
            'slug': b.slug,
            'type': b.get_business_type_display(),
            'type_code': b.business_type,
            'emoji': b.get_map_marker_emoji(),
            'cuisine': b.cuisine,
            'city': b.city,
            'area': b.area,
            'region_name': b.region.name if b.region else 'India',
            'rating': float(b.rating),
            'delivery_time': b.estimated_delivery_time,
            'delivery_fee': float(b.delivery_fee),
            'distance_km': float(b.distance_km),
            'price_range': b.price_range,
            'diet': b.dietary_type,
            'lat': b.latitude,
            'lng': b.longitude,
            'cover': prof.get_cover() if prof else '',
            'url': f"/store/{b.slug}/",
        })

    context = {
        'food_categories': food_categories,
        'regional_categories': regional_categories,
        'nearby_businesses': nearby_businesses,
        'featured_foods': featured_foods,
        'all_menu_foods': all_foods_list[:18],
        'coastal_favorites': coastal_favorites,
        'small_hotels': small_hotels,
        'home_food_businesses': home_food_businesses,
        'hidden_gems': hidden_gems,
        'ai_recommendations': ai_recommendations,
        'sample_meal_plan': sample_meal_plan,
        'regional_offers': regional_offers,
        'festival_campaigns': festival_campaigns,
        'iconic_regional_foods': iconic_regional_foods,
        'active_coupons': active_coupons,
        'recent_orders': recent_orders,
        'recent_reviews': recent_reviews,
        'wishlisted_food_ids': wishlisted_food_ids,
        'wishlisted_business_ids': wishlisted_business_ids,
        'active_filter': active_filter,
        'active_category': active_category,
        'home_map_markers': home_map_markers,
    }
    return render(request, 'core/home.html', context)


def explore_view(request):
    """
    Business Search + Interactive Map Discovery + Regional Food Filter (Sections 10, 23, 33, 81, 87).
    """
    current_region = get_active_region(request)
    q = (request.GET.get('q') or '').strip()
    region_filter = request.GET.get('region_filter', '')
    business_type = request.GET.get('type', '')
    diet = request.GET.get('diet', '')
    sort_by = request.GET.get('sort', 'rating')
    all_india = request.GET.get('all_india', '') == '1'

    businesses_qs = Business.objects.filter(status='APPROVED').select_related('region', 'profile', 'category')
    foods_qs = FoodItem.objects.filter(is_available=True, business__status='APPROVED').select_related(
        'business', 'category', 'region'
    )

    if region_filter and region_filter != 'all-india':
        businesses_qs = businesses_qs.filter(region__slug=region_filter)
        foods_qs = foods_qs.filter(Q(region__slug=region_filter) | Q(business__region__slug=region_filter))
    elif current_region and not all_india and not q:
        # Prioritize selected region first while still showing broader marketplace options
        pass

    if business_type:
        businesses_qs = businesses_qs.filter(business_type=business_type)
        foods_qs = foods_qs.filter(business__business_type=business_type)

    if diet in ('VEG', 'NON_VEG'):
        businesses_qs = businesses_qs.filter(dietary_type__in=[diet, 'BOTH'] if diet == 'NON_VEG' else ['VEG'])
        foods_qs = foods_qs.filter(veg_type=diet)

    if q:
        businesses_qs = businesses_qs.filter(
            Q(name__icontains=q)
            | Q(cuisine__icontains=q)
            | Q(city__icontains=q)
            | Q(area__icontains=q)
            | Q(region__name__icontains=q)
        )
        foods_qs = foods_qs.filter(
            Q(name__icontains=q)
            | Q(description__icontains=q)
            | Q(category__name__icontains=q)
            | Q(business__name__icontains=q)
        )

    if sort_by == 'delivery_time':
        businesses_qs = businesses_qs.order_by('delivery_mins_numeric')
    elif sort_by == 'distance':
        businesses_qs = businesses_qs.order_by('distance_km')
    else:
        businesses_qs = businesses_qs.order_by('-rating', '-total_reviews')

    businesses_list = list(businesses_qs)
    if current_region and not all_india and not region_filter:
        businesses_list.sort(key=lambda b: (0 if b.region_id == current_region.id else 1, -float(b.rating)))

    map_markers = []
    for b in businesses_list:
        prof = getattr(b, 'profile', None)
        map_markers.append({
            'id': b.id,
            'name': b.name,
            'slug': b.slug,
            'type': b.get_business_type_display(),
            'type_code': b.business_type,
            'emoji': b.get_map_marker_emoji(),
            'cuisine': b.cuisine,
            'city': b.city,
            'area': b.area,
            'region_name': b.region.name if b.region else 'India',
            'rating': float(b.rating),
            'delivery_time': b.estimated_delivery_time,
            'delivery_fee': float(b.delivery_fee),
            'distance_km': float(b.distance_km),
            'price_range': b.price_range,
            'diet': b.dietary_type,
            'lat': b.latitude,
            'lng': b.longitude,
            'cover': prof.get_cover() if prof else '',
            'url': f"/store/{b.slug}/",
        })

    context = {
        'businesses': businesses_list,
        'foods': list(foods_qs[:24]),
        'map_markers': map_markers,
        'business_categories': BusinessCategory.objects.all(),
        'food_categories': FoodCategory.objects.filter(is_active=True),
        'query': q,
        'selected_type': business_type,
        'selected_diet': diet,
        'selected_sort': sort_by,
        'all_india': all_india,
        'business_type_choices': Business.BUSINESS_TYPE_CHOICES,
    }
    return render(request, 'core/explore.html', context)


def food_story_detail_view(request, slug):
    """
    Food Detail & Regional Story Page (Section 36 & 91: "Discover the Story Behind Your Food").
    """
    food = get_object_or_404(
        FoodItem.objects.select_related('business', 'business__profile', 'category', 'region')
        .prefetch_related('customizations'),
        slug=slug
    )
    related_foods = list(
        FoodItem.objects.filter(
            is_available=True,
            business__status='APPROVED'
        ).filter(
            Q(region=food.region) | Q(category=food.category)
        ).exclude(id=food.id).select_related('business')[:4]
    )
    reviews = list(food.business.reviews.select_related('user')[:6])

    size_options = [c for c in food.customizations.all() if c.group_type == 'SIZE']
    addon_options = [c for c in food.customizations.all() if c.group_type == 'ADDON']

    context = {
        'food': food,
        'related_foods': related_foods,
        'reviews': reviews,
        'size_options': size_options,
        'addon_options': addon_options,
    }
    return render(request, 'core/food_detail.html', context)


def update_location_view(request):
    """
    Updates Customer Delivery Location (Section 24 & 94 — separate from Selected Food Region).
    """
    if request.method == 'POST':
        label = request.POST.get('label', 'Current Location')
        city = request.POST.get('city', 'Mangaluru').strip()
        area = request.POST.get('area', 'MG Road').strip()
        state = request.POST.get('state', 'Karnataka').strip()
        lat = float(request.POST.get('latitude') or 12.9141)
        lng = float(request.POST.get('longitude') or 74.8560)

        request.session['delivery_label'] = label
        request.session['delivery_city'] = city
        request.session['delivery_area'] = area
        request.session['delivery_state'] = state
        request.session['delivery_lat'] = lat
        request.session['delivery_lng'] = lng

        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            prof = request.user.profile
            prof.delivery_location_label = label
            prof.delivery_city = city
            prof.delivery_area = area
            prof.delivery_state = state
            prof.delivery_lat = lat
            prof.delivery_lng = lng
            prof.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'updated',
                'label': label,
                'city': city,
                'area': area,
                'state': state,
            })
        messages.success(request, f"Delivery location updated to {area}, {city} ({label}).")
    return redirect(request.META.get('HTTP_REFERER', '/'))


def _generate_fallback_tile_png(z: int, x: int, y: int, style: str = 'street') -> bytes:
    """
    Generates a clean, high-contrast 256x256 map tile using Pillow if upstream tile servers
    are unreachable (e.g., offline environment), ensuring maps never show broken tiles or API errors.
    """
    try:
        from PIL import Image, ImageDraw

        bg_color = (244, 241, 234) if style != 'satellite' else (28, 45, 58)
        road_major = (255, 255, 255) if style != 'satellite' else (62, 84, 99)
        road_minor = (232, 226, 213) if style != 'satellite' else (42, 62, 77)
        park_fill = (218, 235, 212) if style != 'satellite' else (33, 68, 52)
        water_fill = (195, 224, 242) if style != 'satellite' else (20, 36, 52)

        img = Image.new('RGB', (256, 256), bg_color)
        draw = ImageDraw.Draw(img)

        # Deterministic pseudo-geography based on tile (x, y)
        seed = (x * 31 + y * 17 + z * 13) % 7
        if seed in (0, 3):
            draw.polygon([(0, 180), (95, 210), (140, 256), (0, 256)], fill=water_fill)
        if seed in (1, 4, 6):
            draw.rounded_rectangle([28, 28, 110, 96], radius=12, fill=park_fill)
        if seed in (2, 5):
            draw.rounded_rectangle([148, 136, 228, 212], radius=12, fill=park_fill)

        # Subtle street grid
        for offset in (32, 64, 96, 128, 160, 192, 224):
            draw.line([(offset, 0), (offset, 256)], fill=road_minor, width=1)
            draw.line([(0, offset), (256, offset)], fill=road_minor, width=1)

        # Major arterial roads
        draw.line([(0, 128), (256, 128)], fill=road_major, width=4)
        draw.line([(128, 0), (128, 256)], fill=road_major, width=4)
        draw.line([(0, (x * 43) % 256), (256, (y * 59) % 256)], fill=road_major, width=3)

        buf = io.BytesIO()
        img.save(buf, format='PNG', optimize=True)
        return buf.getvalue()
    except Exception:
        # Minimal 1x1 transparent PNG fallback
        return (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc`\x00\x00'
            b'\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
        )


def map_tile_proxy_view(request, z, x, y):
    """
    Built-in Tasty Tap Map Tile Engine (/api/map-tiles/<z>/<x>/<y>.png).
    Eliminates external API key prompts and 403 blocks by proxying and caching map tiles
    locally on disk across multiple keyless providers (CARTO Voyager, Esri World Street Map,
    Esri World Imagery, and OSM DE) with a local Pillow vector-grid fallback.
    """
    style = (request.GET.get('style') or 'street').lower()
    if style not in ('street', 'satellite', 'light'):
        style = 'street'

    cache_dir = Path(settings.MEDIA_ROOT) / 'map_tiles' / style / str(z) / str(x)
    cache_file = cache_dir / f"{y}.png"

    if cache_file.exists() and cache_file.stat().st_size > 100:
        try:
            data = cache_file.read_bytes()
            resp = HttpResponse(data, content_type='image/png')
            resp['Cache-Control'] = 'public, max-age=604800'
            resp['X-TastyTap-Map-Engine'] = 'cache-hit'
            return resp
        except Exception:
            pass

    if style == 'satellite':
        upstream_urls = [
            f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            f"https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png",
        ]
    elif style == 'light':
        upstream_urls = [
            f"https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
            f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        ]
    else:
        sub = ('a', 'b', 'c', 'd')[(x + y) % 4]
        upstream_urls = [
            f"https://{sub}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png",
            f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
            f"https://tile.openstreetmap.de/{z}/{x}/{y}.png",
        ]

    headers = {
        'User-Agent': 'TastyTapFoodMarketplace/2.0 (+https://github.com/gowraw11; gowravhadikallu@gmail.com)',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    }

    for url in upstream_urls:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=3.5) as upstream_resp:
                if upstream_resp.status == 200:
                    tile_bytes = upstream_resp.read()
                    if len(tile_bytes) > 100:
                        try:
                            cache_dir.mkdir(parents=True, exist_ok=True)
                            cache_file.write_bytes(tile_bytes)
                        except Exception:
                            pass
                        resp = HttpResponse(tile_bytes, content_type='image/png')
                        resp['Cache-Control'] = 'public, max-age=604800'
                        resp['X-TastyTap-Map-Engine'] = 'upstream-ok'
                        return resp
        except Exception:
            continue

    fallback_bytes = _generate_fallback_tile_png(z, x, y, style=style)
    resp = HttpResponse(fallback_bytes, content_type='image/png')
    resp['Cache-Control'] = 'public, max-age=3600'
    resp['X-TastyTap-Map-Engine'] = 'local-vector-fallback'
    return resp

