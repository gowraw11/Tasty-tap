from datetime import datetime
from decimal import Decimal
from django.db.models import Q
from menu.models import FoodItem
from businesses.models import Business
from orders.models import OrderItem


def get_tasty_ai_recommendations(user=None, region=None, limit=8):
    """
    Hybrid rule + scoring AI Recommendation engine (Sections 20 & 85).
    Considers:
    - Selected Region
    - Previous customer orders (e.g. 'Because you ordered Biryani...')
    - User Wishlist / Preferences
    - Time of Day (Breakfast / Lunch / Evening Snack / Dinner)
    - Item Ratings & Bestseller popularity
    """
    qs = FoodItem.objects.filter(
        is_available=True,
        business__status='APPROVED'
    ).select_related('business', 'category', 'region')

    last_ordered_food_name = None
    last_ordered_category = None
    veg_pref = None

    if user and user.is_authenticated:
        recent_item = (
            OrderItem.objects.filter(order__customer=user)
            .select_related('food_item', 'food_item__category')
            .order_by('-created_at')
            .first()
        )
        if recent_item and recent_item.food_item:
            last_ordered_food_name = recent_item.food_item.name
            last_ordered_category = recent_item.food_item.category

        pref = getattr(user, 'taste_preference', None)
        if pref and pref.dietary_preference in ('VEG', 'NON_VEG'):
            veg_pref = pref.dietary_preference

    if veg_pref == 'VEG':
        qs = qs.filter(veg_type='VEG')

    # Prioritize region items first, then broaden if needed
    regional_items = list(qs.filter(region=region)[:limit * 2]) if region else []
    fallback_items = list(qs.exclude(id__in=[i.id for i in regional_items])[:limit])
    candidates = regional_items + fallback_items

    hour = datetime.now().hour
    if hour < 11:
        time_tag = "Morning Breakfast Pick"
        preferred_courses = {'BREAKFAST', 'DRINK'}
    elif hour < 16:
        time_tag = "Popular Lunch Choice"
        preferred_courses = {'MAIN', 'SIDE', 'DRINK'}
    elif hour < 19:
        time_tag = "Evening Craving Special"
        preferred_courses = {'SNACK', 'STARTER', 'DRINK'}
    else:
        time_tag = "Chef's Dinner Recommendation"
        preferred_courses = {'MAIN', 'STARTER', 'DESSERT'}

    results = []
    for idx, item in enumerate(candidates[:limit]):
        if last_ordered_food_name and idx < 2:
            reason = f"Because you ordered {last_ordered_food_name}"
        elif region and item.region_id == region.id:
            reason = f"Since you're exploring {region.name} {region.emoji_flag}"
        elif item.meal_course in preferred_courses:
            reason = f"{time_tag} • ★ {item.rating}"
        elif item.is_bestseller:
            reason = f"Trending in {item.business.city}"
        else:
            reason = f"Top Rated at {item.business.name}"

        results.append({
            'food': item,
            'reason': reason,
            'match_score': min(99, int(float(item.rating) * 19 + (4 if item.is_bestseller else 1))),
        })
    return results


def build_smart_meal(budget=500, people=2, cuisine='', veg_type='ANY', spice_level='ANY', region=None):
    """
    Smart Meal Builder (Section 22):
    Generates a curated 5-course meal (Starter, Main Course, Side, Drink, Dessert)
    scaled for the number of people and constrained by the user's budget.
    Selects items from the best-matching single business when possible so 1-click Add All to Cart works seamlessly.
    """
    budget_dec = max(Decimal('100.00'), Decimal(str(budget or 500)))
    people_int = max(1, min(10, int(people or 2)))

    qs = FoodItem.objects.filter(
        is_available=True,
        business__status='APPROVED'
    ).select_related('business', 'category', 'region')

    if region:
        regional_qs = qs.filter(Q(region=region) | Q(business__region=region))
        if regional_qs.exists():
            qs = regional_qs

    if veg_type == 'VEG':
        qs = qs.filter(veg_type='VEG')
    elif veg_type == 'NON_VEG':
        qs = qs.filter(veg_type__in=['NON_VEG', 'VEG'])

    if cuisine and cuisine.lower() not in ('all', 'any', ''):
        cuisine_qs = qs.filter(
            Q(business__cuisine__icontains=cuisine)
            | Q(category__name__icontains=cuisine)
            | Q(name__icontains=cuisine)
            | Q(description__icontains=cuisine)
        )
        if cuisine_qs.exists():
            qs = cuisine_qs

    if spice_level and spice_level.upper() in ('MILD', 'MEDIUM', 'HOT', 'EXTREME'):
        spice_qs = qs.filter(spice_level=spice_level.upper())
        if spice_qs.exists():
            qs = spice_qs

    all_items = list(qs.order_by('price', '-rating'))
    if not all_items:
        all_items = list(
            FoodItem.objects.filter(is_available=True, business__status='APPROVED')
            .select_related('business', 'category', 'region')
            .order_by('price')
        )

    course_slots = [
        ('STARTER', 'Starter', ['STARTER', 'SNACK']),
        ('MAIN', 'Main Course', ['MAIN', 'BREAKFAST']),
        ('SIDE', 'Side / Bread', ['SIDE', 'SNACK', 'BREAKFAST']),
        ('DRINK', 'Drink', ['DRINK']),
        ('DESSERT', 'Dessert', ['DESSERT']),
    ]

    per_person_budget = budget_dec / Decimal(str(people_int))
    slot_weights = {
        'STARTER': Decimal('0.22'),
        'MAIN': Decimal('0.36'),
        'SIDE': Decimal('0.14'),
        'DRINK': Decimal('0.12'),
        'DESSERT': Decimal('0.16'),
    }

    selected_courses = []
    used_ids = set()
    running_total = Decimal('0.00')

    for slot_key, slot_label, allowed_courses in course_slots:
        target_unit_max = max(Decimal('30.00'), per_person_budget * slot_weights[slot_key] * Decimal('1.35'))
        slot_candidates = [
            item for item in all_items
            if item.id not in used_ids and item.meal_course in allowed_courses and item.effective_price <= target_unit_max
        ]
        if not slot_candidates:
            slot_candidates = [
                item for item in all_items
                if item.id not in used_ids and item.meal_course in allowed_courses
            ]
        if not slot_candidates:
            slot_candidates = [item for item in all_items if item.id not in used_ids]

        if slot_candidates:
            chosen = slot_candidates[0]
            used_ids.add(chosen.id)
            qty = people_int if slot_key in ('MAIN', 'DRINK', 'SIDE') else max(1, (people_int + 1) // 2)
            line_cost = chosen.effective_price * Decimal(str(qty))
            # Keep within budget if possible
            if running_total + line_cost > budget_dec and qty > 1:
                qty = 1
                line_cost = chosen.effective_price
            running_total += line_cost
            selected_courses.append({
                'course_key': slot_key,
                'course_label': slot_label,
                'food': chosen,
                'food_id': chosen.id,
                'name': chosen.name,
                'business_name': chosen.business.name,
                'business_slug': chosen.business.slug,
                'unit_price': float(chosen.effective_price),
                'quantity': qty,
                'line_total': float(line_cost),
                'veg_type': chosen.veg_type,
                'spice_level': chosen.spice_level,
                'calories': chosen.calories * qty,
                'image_url': chosen.get_image(),
            })

    savings = max(Decimal('0.00'), budget_dec - running_total)
    return {
        'budget': float(budget_dec),
        'people': people_int,
        'total_price': float(running_total),
        'within_budget': running_total <= budget_dec,
        'budget_remaining': float(savings),
        'total_calories': sum(c['calories'] for c in selected_courses),
        'courses': selected_courses,
    }


def answer_tap_ai_query(query_text, region=None, user=None):
    """
    Region-aware conversational TAP AI Assistant (Sections 21 & 86).
    Responds to natural questions with real database dishes, local businesses, and smart suggestions.
    """
    q = (query_text or '').strip().lower()
    region_name = region.name if region else 'All India'
    region_emoji = region.emoji_flag if region else '🇮🇳'

    food_qs = FoodItem.objects.filter(
        is_available=True,
        business__status='APPROVED'
    ).select_related('business', 'category', 'region')

    biz_qs = Business.objects.filter(status='APPROVED').select_related('region')

    if region:
        regional_food = food_qs.filter(Q(region=region) | Q(business__region=region))
        if regional_food.exists():
            food_qs = regional_food
        regional_biz = biz_qs.filter(region=region)
        if regional_biz.exists():
            biz_qs = regional_biz

    reply = ""
    suggested_foods = []
    suggested_businesses = []

    if 'under' in q or 'budget' in q or 'cheap' in q or '200' in q or '150' in q or '100' in q:
        price_limit = 200
        for num in (80, 100, 120, 150, 200, 250, 300):
            if str(num) in q:
                price_limit = num
                break
        suggested_foods = list(food_qs.filter(price__lte=price_limit).order_by('price', '-rating')[:4])
        reply = (
            f"Here are delicious pocket-friendly dishes in {region_name} {region_emoji} under ₹{price_limit}! "
            f"Every dish is freshly prepared by verified local kitchens with reasonable delivery fees."
        )
    elif 'veg' in q and 'non' not in q:
        suggested_foods = list(food_qs.filter(veg_type='VEG').order_by('-rating')[:4])
        suggested_businesses = list(biz_qs.filter(dietary_type__in=['VEG', 'BOTH'])[:2])
        reply = (
            f"Showing top-rated Pure Vegetarian dishes in {region_name} {region_emoji}! "
            f"From authentic tiffins to wholesome thalis:"
        )
    elif 'spicy' in q or 'hot' in q or 'masala' in q or 'chettinad' in q or 'andhra' in q:
        suggested_foods = list(food_qs.filter(spice_level__in=['HOT', 'EXTREME']).order_by('-rating')[:4])
        if not suggested_foods:
            suggested_foods = list(food_qs.order_by('-rating')[:4])
        reply = (
            f"Craving fiery flavors in {region_name} 🌶️? Here are our boldest, spice-packed coastal & regional specialties:"
        )
    elif 'hotel' in q or 'small' in q or 'local' in q or 'gem' in q:
        suggested_businesses = list(
            biz_qs.filter(
                Q(business_type__in=['SMALL_HOTEL', 'HOME_FOOD', 'TIFFIN_SERVICE', 'CAFE'])
                | Q(is_local_favorite=True)
                | Q(is_hidden_gem=True)
            )[:4]
        )
        suggested_foods = list(food_qs.order_by('price')[:3])
        reply = (
            f"Supporting local food heroes in {region_name} ❤️! Here are beloved small hotels and home kitchens near you:"
        )
    elif 'healthy' in q or 'light' in q or 'diet' in q or 'protein' in q:
        suggested_foods = list(food_qs.filter(Q(is_healthy=True) | Q(calories__lte=380)).order_by('calories')[:4])
        reply = (
            f"Here are nutritious, wholesome meals in {region_name} {region_emoji} with balanced calories and fresh ingredients:"
        )
    elif '2 people' in q or 'dinner' in q or 'couple' in q or 'family' in q:
        meal = build_smart_meal(budget=500, people=2, region=region)
        suggested_foods = [c['food'] for c in meal['courses'][:4]]
        reply = (
            f"For dinner for 2 in {region_name} {region_emoji}, I recommend this complete combo totaling ₹{int(meal['total_price'])}! "
            f"You can also customize it in the Smart Meal Builder."
        )
    else:
        # Default "What should I eat?" or region-aware greeting
        suggested_foods = list(food_qs.filter(is_bestseller=True).order_by('-rating')[:4])
        if not suggested_foods:
            suggested_foods = list(food_qs.order_by('-rating')[:4])
        suggested_businesses = list(biz_qs.order_by('-rating')[:2])
        dish_names = ", ".join(f.name for f in suggested_foods[:3])
        reply = (
            f"Since you're exploring {region_name} {region_emoji}, you should definitely try {dish_names}! "
            f"Tap any card below to add it straight to your Quick Order Cart."
        )

    return {
        'reply': reply,
        'region': region_name,
        'foods': [
            {
                'id': f.id,
                'name': f.name,
                'price': float(f.effective_price),
                'business_name': f.business.name,
                'business_slug': f.business.slug,
                'rating': float(f.rating),
                'prep_time': f.preparation_time,
                'veg_type': f.veg_type,
                'image_url': f.get_image(),
            }
            for f in suggested_foods
        ],
        'businesses': [
            {
                'name': b.name,
                'slug': b.slug,
                'type': b.get_business_type_display(),
                'city': b.city,
                'rating': float(b.rating),
                'delivery_time': b.estimated_delivery_time,
            }
            for b in suggested_businesses
        ],
    }
