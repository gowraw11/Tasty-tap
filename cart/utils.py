from cart.models import Cart, Wishlist


def get_or_create_cart(request):
    """
    Retrieves the active Cart for an authenticated user or anonymous session.
    """
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).select_related('business', 'applied_coupon').first()
        if not cart:
            # Merge session cart if one exists
            session_cart = Cart.objects.filter(session_key=session_key, user__isnull=True).first()
            if session_cart:
                session_cart.user = request.user
                session_cart.save(update_fields=['user'])
                cart = session_cart
            else:
                cart = Cart.objects.create(user=request.user, session_key=session_key)
        return cart
    else:
        cart = Cart.objects.filter(session_key=session_key, user__isnull=True).select_related('business', 'applied_coupon').first()
        if not cart:
            cart = Cart.objects.create(session_key=session_key)
        return cart


def get_or_create_wishlist(user):
    if not user or not user.is_authenticated:
        return None
    wishlist, _ = Wishlist.objects.get_or_create(user=user)
    return wishlist
