from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from delivery.models import Delivery, DeliveryPartner
from notifications.models import Notification


@login_required
def delivery_dashboard_view(request):
    """
    /dashboard/delivery/ — Delivery Partner System Dashboard (Sections 17 & 18).
    Displays Available Deliveries, Active Delivery, Completed Deliveries, Today's Earnings,
    and handles Accept, Picked Up, Out for Delivery, and Delivered transitions.
    """
    partner, _ = DeliveryPartner.objects.get_or_create(
        user=request.user,
        defaults={
            'full_name': request.user.get_full_name() or request.user.username,
            'phone': '+91 9845012345',
            'city': 'Mangaluru',
        }
    )

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'toggle_availability':
            partner.is_available = not partner.is_available
            partner.save(update_fields=['is_available'])
            messages.info(request, f"Rider status set to {'Online & Available 🟢' if partner.is_available else 'Offline ⚪'}.")
            return redirect('/dashboard/delivery/')

        delivery_id = request.POST.get('delivery_id')
        delivery = get_object_or_404(Delivery.objects.select_related('order', 'order__business', 'order__customer'), id=delivery_id)
        order = delivery.order

        if action == 'accept_delivery':
            delivery.partner = partner
            delivery.status = 'ASSIGNED'
            delivery.assigned_at = timezone.now()
            delivery.save()
            if order.status in ('CONFIRMED', 'ACCEPTED', 'PREPARING', 'READY'):
                order.status = 'ASSIGNED'
                order.save(update_fields=['status'])
            Notification.objects.create(
                recipient=order.customer,
                target_role='CUSTOMER',
                notification_type='DELIVERY',
                title=f"Delivery Partner Assigned for Order #{order.order_number} 🚴",
                message=f"{partner.full_name} ({partner.get_vehicle_type_display()}) is assigned to deliver your order.",
                link_url=f"/orders/{order.order_number}/track/",
            )
            messages.success(request, f"Accepted delivery for Order #{order.order_number}!")

        elif action == 'picked_up':
            delivery.partner = partner
            delivery.status = 'OUT_FOR_DELIVERY'
            delivery.picked_up_at = timezone.now()
            delivery.rider_lat = (order.business.latitude + order.delivery_lat) / 2.0
            delivery.rider_lng = (order.business.longitude + order.delivery_lng) / 2.0
            delivery.save()
            order.status = 'OUT_FOR_DELIVERY'
            order.save(update_fields=['status'])
            Notification.objects.create(
                recipient=order.customer,
                target_role='CUSTOMER',
                notification_type='DELIVERY',
                title=f"Order #{order.order_number} is Out for Delivery! 🛵",
                message=f"{partner.full_name} picked up your order from {order.business.name} and is on the way.",
                link_url=f"/orders/{order.order_number}/track/",
            )
            messages.success(request, f"Marked Order #{order.order_number} as Picked Up & Out for Delivery!")

        elif action == 'delivered':
            delivery.partner = partner
            delivery.status = 'DELIVERED'
            delivery.delivered_at = timezone.now()
            delivery.rider_lat = order.delivery_lat
            delivery.rider_lng = order.delivery_lng
            delivery.save()

            order.status = 'DELIVERED'
            order.delivered_at = timezone.now()
            order.payment_status = 'PAID'
            order.save(update_fields=['status', 'delivered_at', 'payment_status'])

            partner.total_deliveries += 1
            partner.today_earnings += delivery.delivery_earning
            partner.total_earnings += delivery.delivery_earning
            partner.save(update_fields=['total_deliveries', 'today_earnings', 'total_earnings'])

            Notification.objects.create(
                recipient=order.customer,
                target_role='CUSTOMER',
                notification_type='DELIVERY',
                title=f"Order #{order.order_number} Delivered! 🏠",
                message=f"Enjoy your meal from {order.business.name}! Tap to rate & review your food.",
                link_url=f"/orders/{order.order_number}/track/",
            )
            messages.success(request, f"Order #{order.order_number} Delivered! +₹{delivery.delivery_earning} added to Today's Earnings.")

        return redirect('/dashboard/delivery/')

    available_deliveries = Delivery.objects.filter(
        status__in=['WAITING_PARTNER', 'ASSIGNED']
    ).exclude(status='DELIVERED').select_related('order', 'order__business')[:10]

    active_deliveries = Delivery.objects.filter(
        partner=partner,
        status__in=['ASSIGNED', 'PICKED_UP', 'OUT_FOR_DELIVERY']
    ).select_related('order', 'order__business')

    completed_deliveries = Delivery.objects.filter(
        status='DELIVERED'
    ).select_related('order', 'order__business')[:12]

    return render(request, 'delivery/dashboard.html', {
        'partner': partner,
        'available_deliveries': available_deliveries,
        'active_deliveries': active_deliveries,
        'completed_deliveries': completed_deliveries,
    })
