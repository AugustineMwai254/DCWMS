"""
Booking Views - Create, Manage, Approve/Reject
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Booking
from .forms import BookingForm, BookingApprovalForm
from warehouses.models import Warehouse
from inventory.models import InventoryRecord


@login_required
def create_booking(request, warehouse_pk):
    """Farmer creates a booking for a specific warehouse."""
    if not request.user.is_farmer:
        messages.error(request, "Only farmers can make bookings.")
        return redirect('warehouses:finder')

    warehouse = get_object_or_404(Warehouse, pk=warehouse_pk, is_active=True)
    
    if warehouse.available_capacity_mt <= 0:
        messages.error(request, "This warehouse has no available capacity.")
        return redirect('warehouses:detail', pk=warehouse_pk)

    form = BookingForm(request.POST or None, warehouse=warehouse)
    
    if form.is_valid():
        with transaction.atomic():
            booking = form.save(commit=False)
            booking.farmer = request.user
            booking.warehouse = warehouse
            booking.quantity_mt = round(booking.quantity_bags * 90 / 1000, 3)
            booking.total_fee_kes = booking.calculate_fee()
            
            # Validate capacity
            if booking.quantity_mt > warehouse.available_capacity_mt:
                messages.error(request, f"Requested quantity ({booking.quantity_mt} MT) exceeds available capacity ({warehouse.available_capacity_mt} MT).")
                return render(request, 'bookings/create.html', {'form': form, 'warehouse': warehouse})
            
            booking.save()
            messages.success(request, f"Booking {booking.booking_ref_human} created! Please complete payment to confirm your booking.")
            return redirect('payments:initiate', booking_id=booking.pk)
    
    return render(request, 'bookings/create.html', {
        'form': form,
        'warehouse': warehouse,
    })


@login_required
def booking_list(request):
    """List bookings based on user role."""
    user = request.user
    
    if user.is_farmer:
        bookings = Booking.objects.filter(farmer=user).order_by('-created_at')
        title = "My Bookings"
    elif user.is_operator:
        bookings = Booking.objects.filter(warehouse__operator=user).order_by('-created_at')
        title = "Warehouse Bookings"
    else:
        bookings = Booking.objects.all().order_by('-created_at')
        title = "All Bookings"

    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    return render(request, 'bookings/list.html', {
        'bookings': bookings,
        'title': title,
        'status_filter': status_filter,
        'STATUS_CHOICES': Booking.STATUS_CHOICES,
    })


@login_required
@login_required
def booking_detail(request, pk):
    """View booking details with payment info."""
    user = request.user
    
    if user.is_farmer:
        booking = get_object_or_404(Booking, pk=pk, farmer=user)
    elif user.is_operator:
        booking = get_object_or_404(Booking, pk=pk, warehouse__operator=user)
    else:
        booking = get_object_or_404(Booking, pk=pk)
    
    # Get payment info if exists
    payment = None
    if hasattr(booking, 'payment'):
        payment = booking.payment
    
    return render(request, 'bookings/detail.html', {'booking': booking, 'payment': payment})


@login_required
def approve_booking(request, pk):
    """Operator approves a booking - updates inventory and capacity."""
    booking = get_object_or_404(Booking, pk=pk, warehouse__operator=request.user, status='pending')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        operator_notes = request.POST.get('operator_notes', '')
        rejection_reason = request.POST.get('rejection_reason', '')
        
        with transaction.atomic():
            if action == 'approve':
                warehouse = booking.warehouse
                
                # Re-validate capacity
                if booking.quantity_mt > warehouse.available_capacity_mt:
                    messages.error(request, "Insufficient capacity. Cannot approve this booking.")
                    return redirect('bookings:detail', pk=pk)
                
                # Update warehouse available capacity
                warehouse.available_capacity_mt -= booking.quantity_mt
                warehouse.save()
                
                # Create/update inventory record
                inventory, created = InventoryRecord.objects.get_or_create(
                    warehouse=warehouse,
                    farmer=booking.farmer,
                    cereal_type=booking.cereal_type,
                    booking=booking,
                    defaults={
                        'quantity_bags': booking.quantity_bags,
                        'quantity_mt': booking.quantity_mt,
                        'status': 'stored',
                    }
                )
                
                # Update booking status
                booking.status = Booking.STATUS_APPROVED
                booking.approved_at = timezone.now()
                booking.approved_by = request.user
                booking.operator_notes = operator_notes
                booking.save()
                
                # Generate receipt
                from receipts.models import Receipt
                Receipt.objects.get_or_create(
                    booking=booking,
                    defaults={
                        'farmer': booking.farmer,
                        'warehouse': warehouse,
                        'quantity_bags': booking.quantity_bags,
                        'quantity_mt': booking.quantity_mt,
                        'cereal_type': booking.cereal_type,
                        'storage_start_date': booking.storage_start_date,
                        'storage_end_date': booking.storage_end_date,
                        'total_fee_kes': booking.total_fee_kes,
                        'issued_by': request.user,
                    }
                )
                
                messages.success(request, f"Booking {booking.booking_ref_human} approved. Receipt generated.")
            
            elif action == 'reject':
                booking.status = Booking.STATUS_REJECTED
                booking.rejection_reason = rejection_reason
                booking.operator_notes = operator_notes
                booking.save()
                messages.warning(request, f"Booking {booking.booking_ref_human} rejected.")
    
    return redirect('bookings:detail', pk=pk)


@login_required
def cancel_booking(request, pk):
    """Farmer cancels a pending payment booking."""
    booking = get_object_or_404(Booking, pk=pk, farmer=request.user)
    
    if booking.status != Booking.STATUS_PENDING_PAYMENT:
        messages.error(request, "Only pending payment bookings can be cancelled.")
        return redirect('bookings:detail', pk=pk)
    
    if request.method == 'POST':
        booking.status = Booking.STATUS_CANCELLED
        booking.save()
        messages.success(request, "Booking cancelled successfully.")
        return redirect('bookings:list')
    
    return render(request, 'bookings/cancel_confirm.html', {'booking': booking})


# AJAX VIEWS FOR DYNAMIC DASHBOARD
@login_required
@require_POST
def quick_approve_booking(request):
    """AJAX endpoint for quick booking approval from dashboard."""
    try:
        data = json.loads(request.body)
        booking_id = data.get('booking_id')
        notes = data.get('notes', '')

        booking = get_object_or_404(Booking, pk=booking_id, warehouse__operator=request.user, status='pending')

        with transaction.atomic():
            warehouse = booking.warehouse

            # Check capacity
            if booking.quantity_mt > warehouse.available_capacity_mt:
                return JsonResponse({
                    'success': False,
                    'message': 'Insufficient warehouse capacity'
                })

            # Update capacity
            warehouse.available_capacity_mt -= booking.quantity_mt
            warehouse.save()

            # Create inventory record
            InventoryRecord.objects.get_or_create(
                warehouse=warehouse,
                farmer=booking.farmer,
                cereal_type=booking.cereal_type,
                booking=booking,
                defaults={
                    'quantity_bags': booking.quantity_bags,
                    'quantity_mt': booking.quantity_mt,
                    'status': 'stored',
                }
            )

            # Update booking
            booking.status = Booking.STATUS_APPROVED
            booking.approved_at = timezone.now()
            booking.approved_by = request.user
            booking.operator_notes = notes
            booking.save()

            # Generate receipt
            from receipts.models import Receipt
            Receipt.objects.get_or_create(
                booking=booking,
                defaults={
                    'farmer': booking.farmer,
                    'warehouse': warehouse,
                    'quantity_bags': booking.quantity_bags,
                    'quantity_mt': booking.quantity_mt,
                    'cereal_type': booking.cereal_type,
                    'storage_start_date': booking.storage_start_date,
                    'storage_end_date': booking.storage_end_date,
                    'total_fee_kes': booking.total_fee_kes,
                    'issued_by': request.user,
                }
            )

        return JsonResponse({
            'success': True,
            'message': f'Booking {booking.booking_ref_human} approved',
            'booking_id': booking.id,
            'new_status': 'approved'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_POST
def quick_reject_booking(request):
    """AJAX endpoint for quick booking rejection from dashboard."""
    try:
        data = json.loads(request.body)
        booking_id = data.get('booking_id')
        reason = data.get('reason', '')
        notes = data.get('notes', '')

        booking = get_object_or_404(Booking, pk=booking_id, warehouse__operator=request.user, status='pending')

        booking.status = Booking.STATUS_REJECTED
        booking.rejection_reason = reason
        booking.operator_notes = notes
        booking.save()

        return JsonResponse({
            'success': True,
            'message': f'Booking {booking.booking_ref_human} rejected',
            'booking_id': booking.id,
            'new_status': 'rejected'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def get_pending_bookings_count(request):
    """AJAX endpoint to get current pending bookings count for operator."""
    if request.user.is_operator:
        count = Booking.objects.filter(warehouse__operator=request.user, status='pending').count()
        return JsonResponse({'count': count})
    return JsonResponse({'count': 0})


@login_required
def get_recent_bookings(request):
    """AJAX endpoint to get recent bookings for operator dashboard."""
    if not request.user.is_operator:
        return JsonResponse({'error': 'Unauthorized'})

    limit = int(request.GET.get('limit', 10))
    bookings = Booking.objects.filter(warehouse__operator=request.user).order_by('-created_at')[:limit]

    data = []
    for booking in bookings:
        data.append({
            'id': booking.id,
            'ref': booking.booking_ref_human,
            'farmer': booking.farmer.get_full_name(),
            'warehouse': booking.warehouse.name,
            'bags': booking.quantity_bags,
            'cereal': booking.cereal_type,
            'date': booking.created_at.strftime('%d %b %Y'),
            'status': booking.status,
            'status_display': booking.get_status_display(),
        })

    return JsonResponse({'bookings': data})
