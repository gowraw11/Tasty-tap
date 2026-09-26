from datetime import datetime
from django.conf import settings
from core.models import Region
from cart.utils import get_or_create_cart
from notifications.models import Notification


def get_time_greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Good Morning"
    elif hour < 17:
        return "Good Afternoon"
    return "Good Evening"


def get_active_region(request):
    """
    Resolves the currently selected Region from query param, session, or user profile.
    Supports 'all-india' mode or a specific state Region.
    """
    region_slug = request.GET.get('region') or request.session.get('selected_region_slug')
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        profile = request.user.profile
        if not region_slug and profile.selected_region:
            region_slug = profile.selected_region.slug

    if region_slug == 'all-india':
        return None

    try:
        if region_slug:
            region = Region.objects.select_related('theme').filter(slug=region_slug, is_active=True).first()
            if region:
                return region
        return Region.objects.select_related('theme').filter(is_active=True).order_by('display_order').first()
    except Exception:
        return None


def tasty_tap_global_context(request):
    """
    Global context processor providing Region theme, Delivery Location separation,
    Smart Cart state, Notifications, and User Role flags across all templates.
    """
    try:
        all_regions = list(Region.objects.select_related('theme').filter(is_active=True).order_by('display_order'))
    except Exception:
        all_regions = []

    current_region = get_active_region(request)
    current_theme = getattr(current_region, 'theme', None) if current_region else None
    is_all_india = request.session.get('selected_region_slug') == 'all-india'

    # Delivery Location (distinct from Explore Region per Section 94)
    delivery_city = request.session.get('delivery_city', 'Mangaluru')
    delivery_area = request.session.get('delivery_area', 'MG Road')
    delivery_state = request.session.get('delivery_state', 'Karnataka')
    delivery_label = request.session.get('delivery_label', 'Current Location')

    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        prof = request.user.profile
        delivery_city = request.session.get('delivery_city') or prof.delivery_city
        delivery_area = request.session.get('delivery_area') or prof.delivery_area
        delivery_state = request.session.get('delivery_state') or prof.delivery_state
        delivery_label = request.session.get('delivery_label') or prof.delivery_location_label

    cross_region_warning = False
    if current_region and delivery_state:
        if current_region.name.lower() != delivery_state.lower() and current_region.slug != 'all-india':
            cross_region_warning = True

    # Onboarding modal trigger on first visit if region not chosen yet
    has_chosen_region = bool(request.session.get('has_chosen_region', False))
    if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.has_chosen_region:
        has_chosen_region = True

    # Cart context
    cart = None
    cart_items = []
    cart_count = 0
    try:
        cart = get_or_create_cart(request)
        cart_items = list(cart.items.select_related('food_item', 'food_item__business').all())
        cart_count = sum(i.quantity for i in cart_items)
    except Exception:
        pass

    # Notifications & Role flags
    unread_notifications_count = 0
    recent_notifications = []
    user_role = 'CUSTOMER'
    tasty_points = 0
    if request.user.is_authenticated:
        try:
            if hasattr(request.user, 'profile'):
                user_role = request.user.profile.role
                tasty_points = request.user.profile.tasty_points
            if request.user.is_superuser:
                user_role = 'ADMIN'
            unread_notifications_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
            recent_notifications = list(Notification.objects.filter(recipient=request.user)[:6])
        except Exception:
            pass

    return {
        'time_greeting': get_time_greeting(),
        'all_regions': all_regions,
        'current_region': current_region,
        'current_theme': current_theme,
        'is_all_india': is_all_india,
        'show_region_onboarding': not has_chosen_region,
        'delivery_city': delivery_city,
        'delivery_area': delivery_area,
        'delivery_state': delivery_state,
        'delivery_label': delivery_label,
        'cross_region_warning': cross_region_warning,
        'global_cart': cart,
        'global_cart_items': cart_items,
        'global_cart_count': cart_count,
        'unread_notifications_count': unread_notifications_count,
        'recent_notifications': recent_notifications,
        'user_role': user_role,
        'user_tasty_points': tasty_points,
        'maps_api_key': getattr(settings, 'MAPS_API_KEY', 'tt_maps_live_9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c'),
    }

