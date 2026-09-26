from decimal import Decimal
import uuid
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.html import strip_tags

from accounts.models import Address, PointsTransaction, UserProfile
from cart.models import CartItem
from cart.utils import get_or_create_cart
from core.context_processors import get_active_region
from delivery.models import Delivery, DeliveryPartner
from notifications.models import Notification
from offers.models import Coupon
from orders.invoice import generate_order_invoice_pdf
from orders.models import Order, OrderItem
from payments.models import Payment
from reviews.models import Review


def cart_checkout_view(request):
    """
    /cart/ — Smart Multi-Vendor Cart & Checkout Page (Sections 9, 26, 27, 37).
    """
    cart = get_or_create_cart(request)
    items = list(cart.items.select_related('food_item', 'food_item__business').all())
    available_coupons = Coupon.objects.filter(is_active=True)[:6]
    saved_addresses = Address.objects.filter(user=request.user) if request.user.is_authenticated else []

    if request.method == 'POST':
        action = request.POST.get('action', 'place_order')

        if action == 'apply_coupon':
            code = (request.POST.get('coupon_code') or '').strip().upper()
            coupon = Coupon.objects.filter(code__iexact=code, is_active=True).first()
            if not coupon:
                messages.error(request, "Invalid or expired coupon code.")
            elif cart.get_subtotal() < coupon.min_order_amount:
                messages.warning(request, f"Add ₹{coupon.min_order_amount - cart.get_subtotal():.0f} more to use {coupon.code}.")
            elif coupon.business_id and cart.business_id and coupon.business_id != cart.business_id:
                messages.warning(request, f"Coupon {coupon.code} is valid only at {coupon.business.name}.")
            else:
                cart.applied_coupon = coupon
                cart.save(update_fields=['applied_coupon'])
                messages.success(request, f"Coupon {coupon.code} applied! You saved ₹{cart.get_discount()}.")
            return redirect('/cart/')

        if action == 'remove_coupon':
            cart.applied_coupon = None
            cart.save(update_fields=['applied_coupon'])
            messages.info(request, "Removed coupon from cart.")
            return redirect('/cart/')

        if action == 'place_order':
            if not items or not cart.business:
                messages.warning(request, "Your cart is empty. Add delicious food first!")
                return redirect('/')

            if not request.user.is_authenticated:
                messages.info(request, "Please sign in or use a 1-Click Demo Account to complete your order.")
                return redirect('/accounts/login/?next=/cart/')

            customer_name = strip_tags(request.POST.get('customer_name') or request.user.get_full_name() or request.user.username).strip()
            customer_phone = strip_tags(request.POST.get('customer_phone') or '+91 9876543210').strip()
            delivery_address = strip_tags(request.POST.get('delivery_address') or '14 Coastal Residency, MG Road').strip()
            delivery_area = strip_tags(request.POST.get('delivery_area') or request.session.get('delivery_area', 'MG Road')).strip()
            delivery_city = strip_tags(request.POST.get('delivery_city') or request.session.get('delivery_city', 'Mangaluru')).strip()
            payment_method = request.POST.get('payment_method', 'UPI')
            special_instructions = strip_tags(request.POST.get('special_instructions') or '').strip()

            subtotal = cart.get_subtotal()
            discount_amt = cart.get_discount()
            points_disc = cart.get_points_discount()
            tax_amt = cart.get_tax()
            del_fee = cart.get_delivery_fee()
            total_amt = cart.get_total()

            points_earned = max(5, int(total_amt // Decimal('10.00')))
            next_num = 1024 + Order.objects.count() + 1
            order_number = f"TT{next_num}"
            while Order.objects.filter(order_number=order_number).exists():
                next_num += 1
                order_number = f"TT{next_num}"

            order = Order.objects.create(
                order_number=order_number,
                customer=request.user,
                business=cart.business,
                region=cart.business.region or get_active_region(request),
                customer_name=customer_name,
                customer_phone=customer_phone,
                delivery_address=delivery_address,
                delivery_area=delivery_area,
                delivery_city=delivery_city,
                delivery_lat=cart.business.latitude + 0.012,
                delivery_lng=cart.business.longitude + 0.012,
                subtotal=subtotal,
                discount_amount=discount_amt,
                points_redeemed=cart.redeem_points,
                points_discount=points_disc,
                tax_amount=tax_amt,
                delivery_fee=del_fee,
                total_amount=total_amt,
                coupon_code=cart.applied_coupon.code if cart.applied_coupon else '',
                status='CONFIRMED',
                payment_method=payment_method,
                payment_status='PENDING' if payment_method == 'COD' else 'PAID',
                estimated_delivery_mins=cart.business.delivery_mins_numeric,
                points_earned=points_earned,
                special_instructions=special_instructions,
            )

            item_summary_parts = []
            for ci in items:
                OrderItem.objects.create(
                    order=order,
                    food_item=ci.food_item,
                    food_name=ci.food_item.name,
                    unit_price=ci.food_item.effective_price,
                    addon_price=ci.addon_unit_price,
                    quantity=ci.quantity,
                    customization_details=ci.get_customization_display(),
                    line_total=ci.get_line_total(),
                )
                item_summary_parts.append(f"{ci.food_item.name} ×{ci.quantity}")
                ci.food_item.order_count += ci.quantity
                ci.food_item.stock_quantity = max(0, ci.food_item.stock_quantity - ci.quantity)
                ci.food_item.save(update_fields=['order_count', 'stock_quantity'])

            # Safe Payment record (never stores card number or CVV - Section 26)
            masked_ref = {
                'UPI': 'upi-verified@okaxis',
                'CARD': 'CARD-MASKED-XXXX-4242',
                'NET_BANKING': 'NETBANK-HDFC-VERIFIED',
                'COD': 'CASH-ON-DELIVERY',
            }.get(payment_method, 'MOCK-VERIFIED')

            Payment.objects.create(
                order=order,
                user=request.user,
                transaction_id=f"TXN-{uuid.uuid4().hex[:10].upper()}",
                gateway='TASTY_TAP_MOCK_GATEWAY',
                payment_method=payment_method,
                amount=total_amt,
                status='PENDING' if payment_method == 'COD' else 'SUCCESS',
                masked_instrument=masked_ref,
            )

            # Create Delivery tracking record
            rider = DeliveryPartner.objects.filter(is_available=True).first()
            Delivery.objects.create(
                order=order,
                partner=rider,
                status='WAITING_PARTNER',
                pickup_address=f"{cart.business.name}, {cart.business.area}, {cart.business.city}",
                drop_address=f"{delivery_address}, {delivery_area}, {delivery_city}",
                distance_km=cart.business.distance_km,
                estimated_mins=cart.business.delivery_mins_numeric,
                delivery_earning=max(Decimal('30.00'), del_fee + Decimal('15.00')),
                rider_lat=cart.business.latitude,
                rider_lng=cart.business.longitude,
            )

            # Update Tasty Points Wallet (Section 27)
            prof, _ = UserProfile.objects.get_or_create(user=request.user)
            if cart.redeem_points > 0:
                prof.tasty_points = max(0, prof.tasty_points - cart.redeem_points)
                PointsTransaction.objects.create(
                    user=request.user,
                    points=-cart.redeem_points,
                    transaction_type='REDEEMED',
                    description=f"Redeemed on Order #{order.order_number}",
                )
            prof.tasty_points += points_earned
            prof.save(update_fields=['tasty_points'])
            PointsTransaction.objects.create(
                user=request.user,
                points=points_earned,
                transaction_type='EARNED',
                description=f"Earned from Order #{order.order_number} at {cart.business.name}",
            )

            # Send Notifications to Customer & Business Owner (Sections 16 & 52)
            summary_str = ", ".join(item_summary_parts[:3])
            Notification.objects.create(
                recipient=request.user,
                target_role='CUSTOMER',
                notification_type='ORDER',
                title=f"Order #{order.order_number} Confirmed! 🎉",
                message=f"Your order ({summary_str}) has been sent to {cart.business.name}. You earned +{points_earned} Tasty Points!",
                link_url=f"/orders/{order.order_number}/track/",
            )
            Notification.objects.create(
                recipient=cart.business.owner,
                target_role='BUSINESS_PARTNER',
                notification_type='ORDER',
                title=f"New Order Received! Order #{order.order_number}",
                message=f"Customer ordered {summary_str} (Total: ₹{total_amt}). Accept to start preparing!",
                link_url=f"/dashboard/business/?business_id={cart.business.id}",
            )

            # Clear cart
            cart.items.all().delete()
            cart.business = None
            cart.applied_coupon = None
            cart.redeem_points = 0
            cart.save()

            messages.success(request, f"Order #{order.order_number} confirmed! Track live preparation & delivery below.")
            return redirect(f"/orders/{order.order_number}/track/")

    return render(request, 'orders/cart_checkout.html', {
        'cart': cart,
        'items': items,
        'available_coupons': available_coupons,
        'saved_addresses': saved_addresses,
        'free_delivery_progress': cart.get_free_delivery_progress(),
    })


def order_tracking_view(request, order_number):
    """
    /orders/<order_number>/track/ — Live Animated Order Tracking + Leaflet Map + Review Submission (Sections 17, 25, 28).
    """
    order = get_object_or_404(
        Order.objects.select_related('business', 'business__profile', 'customer').prefetch_related('items', 'items__food_item'),
        order_number=order_number
    )
    delivery = getattr(order, 'delivery', None)

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'advance_demo_status':
            progression = {
                'CONFIRMED': 'ACCEPTED',
                'ACCEPTED': 'PREPARING',
                'PREPARING': 'READY',
                'READY': 'OUT_FOR_DELIVERY',
                'ASSIGNED': 'OUT_FOR_DELIVERY',
                'PICKED_UP': 'OUT_FOR_DELIVERY',
                'OUT_FOR_DELIVERY': 'DELIVERED',
            }
            next_st = progression.get(order.status)
            if next_st:
                order.status = next_st
                if next_st == 'DELIVERED':
                    order.delivered_at = timezone.now()
                    order.payment_status = 'PAID'
                    order.business.total_orders_completed += 1
                    order.business.save(update_fields=['total_orders_completed'])
                order.save()
                if delivery:
                    if next_st == 'OUT_FOR_DELIVERY':
                        delivery.status = 'OUT_FOR_DELIVERY'
                        delivery.rider_lat = (order.business.latitude + order.delivery_lat) / 2.0
                        delivery.rider_lng = (order.business.longitude + order.delivery_lng) / 2.0
                    elif next_st == 'DELIVERED':
                        delivery.status = 'DELIVERED'
                        delivery.delivered_at = timezone.now()
                        delivery.rider_lat = order.delivery_lat
                        delivery.rider_lng = order.delivery_lng
                    delivery.save()
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': order.status,
                        'status_display': order.get_status_display(),
                        'timeline': order.get_timeline_steps(),
                        'rider_lat': delivery.rider_lat if delivery else order.business.latitude,
                        'rider_lng': delivery.rider_lng if delivery else order.business.longitude,
                    })
                messages.success(request, f"Order #{order.order_number} advanced to: {order.get_status_display()}")
            return redirect(f"/orders/{order.order_number}/track/")

        elif action == 'submit_review' and request.user.is_authenticated:
            business_rating = max(1, min(5, int(request.POST.get('business_rating') or 5)))
            food_rating = max(1, min(5, int(request.POST.get('food_rating') or 5)))
            comment = strip_tags(request.POST.get('comment') or 'Delicious food and timely delivery!').strip()
            photo_url = (request.POST.get('photo_url') or '').strip()
            first_order_item = order.items.first()
            food_obj = first_order_item.food_item if first_order_item else None

            rev = Review.objects.create(
                user=request.user,
                business=order.business,
                food_item=food_obj,
                order=order,
                business_rating=business_rating,
                food_rating=food_rating,
                comment=comment,
                photo_url=photo_url,
                is_verified_order=True,
            )
            if request.FILES.get('photo'):
                rev.photo = request.FILES['photo']
                rev.save()

            # Recompute business average rating from DB
            agg = order.business.reviews.aggregate(avg_r=Avg('business_rating'))
            if agg['avg_r']:
                order.business.rating = Decimal(str(round(agg['avg_r'], 1)))
                order.business.total_reviews = order.business.reviews.count()
                order.business.save(update_fields=['rating', 'total_reviews'])

            Notification.objects.create(
                recipient=order.business.owner,
                target_role='BUSINESS_PARTNER',
                notification_type='BUSINESS',
                title=f"New {business_rating}★ Verified Review for {order.business.name}",
                message=f'{request.user.username}: "{comment[:90]}"',
                link_url=f"/dashboard/business/?business_id={order.business.id}",
            )
            messages.success(request, "Thank you! Your Verified Order Review has been published.")
            return redirect(f"/orders/{order.order_number}/track/")

    existing_review = order.reviews.first()
    return render(request, 'orders/track.html', {
        'order': order,
        'delivery': delivery,
        'timeline_steps': order.get_timeline_steps(),
        'existing_review': existing_review,
    })


def order_invoice_pdf_view(request, order_number):
    """
    /orders/<order_number>/invoice/ — Streams downloadable PDF tax invoice (Section 53).
    """
    order = get_object_or_404(
        Order.objects.select_related('business', 'customer').prefetch_related('items'),
        order_number=order_number
    )
    pdf_bytes = generate_order_invoice_pdf(order)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="TastyTap_Invoice_{order.order_number}.pdf"'
    return response


@login_required
def reorder_view(request, order_number):
    """
    /orders/<order_number>/reorder/ — One-click Reorder (Section 30).
    Automatically adds previously ordered available items to the cart and warns if any item is unavailable.
    """
    order = get_object_or_404(Order.objects.prefetch_related('items__food_item'), order_number=order_number)
    cart = get_or_create_cart(request)
    cart.items.all().delete()
    cart.business = order.business
    cart.applied_coupon = None
    cart.save()

    unavailable_items = []
    added_count = 0

    for oi in order.items.all():
        food = oi.food_item
        if food and food.is_available and food.stock_quantity > 0:
            CartItem.objects.create(
                cart=cart,
                food_item=food,
                quantity=oi.quantity,
                selected_size='Regular',
                selected_spice=food.get_spice_level_display(),
                addon_unit_price=oi.addon_price,
            )
            added_count += 1
        else:
            unavailable_items.append(oi.food_name)

    if unavailable_items:
        messages.warning(request, "Some items are currently unavailable.")
    if added_count > 0:
        messages.success(request, f"Added {added_count} item(s) from Order #{order.order_number} to your cart!")
    return redirect('/cart/')
