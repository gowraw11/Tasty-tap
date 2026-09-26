from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from accounts.models import Address, PointsTransaction, UserProfile
from core.models import Region
from cart.utils import get_or_create_wishlist
from orders.models import Order
from recommendations.models import UserPreference


def login_view(request):
    """
    Role-aware login view with 1-Click Demo Account Login for college viva / portfolio demonstration (Sections 42, 61).
    """
    if request.method == 'POST':
        quick_role = request.POST.get('demo_role')
        if quick_role:
            role_map = {
                'CUSTOMER': 'customer_demo',
                'BUSINESS_PARTNER': 'rahul_tastybites',
                'DELIVERY_PARTNER': 'kiran_rider',
                'ADMIN': 'admin',
            }
            target_username = role_map.get(quick_role, 'customer_demo')
            user = User.objects.filter(username=target_username).first()
            if user:
                login(request, user)
                messages.success(request, f"Signed in as {user.get_full_name() or user.username} ({quick_role.replace('_', ' ').title()})!")
                if quick_role == 'BUSINESS_PARTNER':
                    return redirect('/dashboard/business/')
                elif quick_role == 'DELIVERY_PARTNER':
                    return redirect('/dashboard/delivery/')
                elif quick_role == 'ADMIN':
                    return redirect('/dashboard/admin/')
                return redirect('/')

        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''
        user = authenticate(request, username=username, password=password)
        if not user and '@' in username:
            by_email = User.objects.filter(email__iexact=username).first()
            if by_email:
                user = authenticate(request, username=by_email.username, password=password)

        if user:
            login(request, user)
            prof = getattr(user, 'profile', None)
            role = prof.role if prof else ('ADMIN' if user.is_superuser else 'CUSTOMER')
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            if role == 'BUSINESS_PARTNER':
                return redirect('/dashboard/business/')
            elif role == 'DELIVERY_PARTNER':
                return redirect('/dashboard/delivery/')
            elif role == 'ADMIN' or user.is_superuser:
                return redirect('/dashboard/admin/')
            return redirect('/')
        else:
            messages.error(request, "Invalid username/email or password. You can also use a 1-Click Demo Account below.")

    return render(request, 'accounts/login.html')


def register_view(request):
    """
    Customer registration with Welcome Tasty Points bonus & Region selection onboarding (Sections 42, 70).
    """
    regions = Region.objects.filter(is_active=True).order_by('display_order')
    if request.method == 'POST':
        full_name = (request.POST.get('full_name') or '').strip()
        username = (request.POST.get('username') or '').strip()
        email = (request.POST.get('email') or '').strip()
        phone = (request.POST.get('phone') or '').strip()
        password = request.POST.get('password') or ''
        region_slug = request.POST.get('region_slug', 'karnataka')
        role = request.POST.get('role', 'CUSTOMER')
        if role not in ('CUSTOMER', 'DELIVERY_PARTNER'):
            role = 'CUSTOMER'

        if not username or not password:
            messages.error(request, "Please provide both a username and password.")
            return render(request, 'accounts/register.html', {'regions': regions})

        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, "That username is already taken. Please choose another.")
            return render(request, 'accounts/register.html', {'regions': regions})

        first_name = full_name.split(' ')[0] if full_name else username
        last_name = ' '.join(full_name.split(' ')[1:]) if ' ' in full_name else ''
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        region_obj = Region.objects.filter(slug=region_slug).first()
        prof, _ = UserProfile.objects.get_or_create(user=user)
        prof.role = role
        prof.phone = phone
        prof.selected_region = region_obj
        prof.has_chosen_region = bool(region_obj)
        prof.tasty_points = 150
        prof.save()

        PointsTransaction.objects.create(
            user=user,
            points=150,
            transaction_type='BONUS',
            description='Welcome to Tasty Tap Bonus Points 🎉',
        )
        UserPreference.objects.get_or_create(
            user=user,
            defaults={'preferred_region': region_obj}
        )

        if role == 'DELIVERY_PARTNER':
            from delivery.models import DeliveryPartner
            DeliveryPartner.objects.get_or_create(
                user=user,
                defaults={
                    'full_name': full_name or username,
                    'phone': phone or '+91 9876543210',
                    'city': region_obj.default_city if region_obj else 'Mangaluru',
                }
            )

        login(request, user)
        if region_obj:
            request.session['selected_region_slug'] = region_obj.slug
            request.session['has_chosen_region'] = True

        messages.success(request, f"Welcome to Tasty Tap, {first_name}! You earned 150 Welcome Tasty Points.")
        if role == 'DELIVERY_PARTNER':
            return redirect('/dashboard/delivery/')
        return redirect('/')

    return render(request, 'accounts/register.html', {'regions': regions})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been signed out safely.")
    return redirect('/')


def forgot_password_view(request):
    """
    Password reset assistance workflow (Section 42).
    """
    reset_sent = False
    email_submitted = ''
    if request.method == 'POST':
        email_submitted = (request.POST.get('email') or '').strip()
        reset_sent = True
        messages.success(request, f"Password recovery instructions generated for {email_submitted}.")
    return render(request, 'accounts/forgot_password.html', {
        'reset_sent': reset_sent,
        'email_submitted': email_submitted,
    })


@login_required
def profile_view(request):
    """
    Customer Profile, Tasty Points Wallet, Saved Addresses, Taste Preferences & Order History (Sections 24, 27, 30, 42).
    """
    prof, _ = UserProfile.objects.get_or_create(user=request.user)
    pref, _ = UserPreference.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form_type = request.POST.get('form_type', 'profile')
        if form_type == 'profile':
            request.user.first_name = (request.POST.get('first_name') or '').strip()
            request.user.last_name = (request.POST.get('last_name') or '').strip()
            request.user.email = (request.POST.get('email') or '').strip()
            request.user.save()

            prof.phone = (request.POST.get('phone') or '').strip()
            region_slug = request.POST.get('selected_region')
            if region_slug:
                reg = Region.objects.filter(slug=region_slug).first()
                prof.selected_region = reg
                prof.has_chosen_region = True
                if reg:
                    request.session['selected_region_slug'] = reg.slug
            prof.save()

            pref.favorite_cuisines = (request.POST.get('favorite_cuisines') or pref.favorite_cuisines).strip()
            pref.dietary_preference = request.POST.get('dietary_preference', pref.dietary_preference)
            pref.spice_preference = request.POST.get('spice_preference', pref.spice_preference)
            pref.save()
            messages.success(request, "Profile & regional preferences updated!")

        elif form_type == 'add_address':
            Address.objects.create(
                user=request.user,
                label=request.POST.get('label', 'Home'),
                recipient_name=request.POST.get('recipient_name') or request.user.get_full_name() or request.user.username,
                phone=request.POST.get('phone') or prof.phone,
                address_line=request.POST.get('address_line', ''),
                area=request.POST.get('area', ''),
                city=request.POST.get('city', 'Mangaluru'),
                state=request.POST.get('state', 'Karnataka'),
                pincode=request.POST.get('pincode', '575001'),
                is_default=True,
            )
            messages.success(request, "New delivery address saved!")

        return redirect('/accounts/profile/')

    orders = Order.objects.filter(customer=request.user).select_related('business').prefetch_related('items')[:15]
    addresses = Address.objects.filter(user=request.user)
    points_history = PointsTransaction.objects.filter(user=request.user)[:15]

    return render(request, 'accounts/profile.html', {
        'profile': prof,
        'preference': pref,
        'orders': orders,
        'addresses': addresses,
        'points_history': points_history,
    })


@login_required
def wishlist_view(request):
    """
    Customer "My Favorites" Wishlist for saved Food Items and Local Businesses (Section 29).
    """
    wishlist = get_or_create_wishlist(request.user)
    saved_foods = wishlist.food_items.select_related('business', 'category', 'region').all() if wishlist else []
    saved_businesses = wishlist.businesses.select_related('region', 'profile').all() if wishlist else []
    return render(request, 'accounts/wishlist.html', {
        'saved_foods': saved_foods,
        'saved_businesses': saved_businesses,
    })
