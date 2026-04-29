"""Reports Views - Analytics and Statistics"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
import datetime

from bookings.models import Booking
from warehouses.models import Warehouse
from inventory.models import InventoryRecord
from withdrawals.models import Withdrawal
from accounts.models import User


@login_required
def reports_home(request):
    user = request.user
    today = timezone.now().date()
    thirty_days_ago = today - datetime.timedelta(days=30)

    ctx = {}

    if user.is_operator:
        warehouses = Warehouse.objects.filter(operator=user)
        ctx['warehouses'] = warehouses
        ctx['warehouse_utilization'] = []
        for w in warehouses:
            ctx['warehouse_utilization'].append({
                'name': w.name,
                'total': float(w.total_capacity_mt),
                'used': float(w.total_capacity_mt - w.available_capacity_mt),
                'available': float(w.available_capacity_mt),
                'pct': w.utilization_percent,
                'county': w.county,
            })

        ctx['monthly_bookings'] = (
            Booking.objects.filter(warehouse__operator=user, created_at__gte=thirty_days_ago)
            .values('status').annotate(count=Count('id'))
        )
        ctx['total_bookings_30d'] = Booking.objects.filter(
            warehouse__operator=user, created_at__gte=thirty_days_ago
        ).count()
        ctx['total_stored_mt'] = InventoryRecord.objects.filter(
            warehouse__operator=user, status='stored'
        ).aggregate(total=Sum('remaining_mt'))['total'] or 0
        ctx['pending_withdrawals'] = Withdrawal.objects.filter(
            warehouse__operator=user, status='pending'
        ).count()

        # Cereal breakdown
        ctx['cereal_breakdown'] = (
            InventoryRecord.objects.filter(warehouse__operator=user, status='stored')
            .values('cereal_type').annotate(bags=Sum('remaining_bags'), mt=Sum('remaining_mt'))
            .order_by('-bags')
        )

    elif user.is_farmer:
        ctx['my_bookings_count'] = Booking.objects.filter(farmer=user).count()
        ctx['active_storage'] = InventoryRecord.objects.filter(
            farmer=user, status='stored'
        ).aggregate(total=Sum('remaining_bags'))['total'] or 0
        ctx['total_withdrawn'] = Withdrawal.objects.filter(
            farmer=user, status='completed'
        ).count()
        ctx['booking_history'] = (
            Booking.objects.filter(farmer=user)
            .values('status').annotate(count=Count('id'))
        )
        ctx['cereal_stored'] = (
            InventoryRecord.objects.filter(farmer=user, status='stored')
            .values('cereal_type').annotate(bags=Sum('remaining_bags'))
        )

    else:  # Admin
        ctx['total_warehouses'] = Warehouse.objects.count()
        ctx['total_farmers'] = User.objects.filter(role='farmer').count()
        ctx['total_operators'] = User.objects.filter(role='operator').count()
        ctx['total_bookings'] = Booking.objects.count()
        ctx['total_stored_mt'] = InventoryRecord.objects.filter(
            status='stored'
        ).aggregate(total=Sum('remaining_mt'))['total'] or 0
        ctx['bookings_by_status'] = (
            Booking.objects.values('status').annotate(count=Count('id'))
        )
        ctx['warehouses_by_county'] = (
            Warehouse.objects.values('county').annotate(count=Count('id')).order_by('-count')[:10]
        )
        ctx['monthly_bookings_30d'] = Booking.objects.filter(
            created_at__gte=thirty_days_ago
        ).count()

    return render(request, 'reports/home.html', ctx)
