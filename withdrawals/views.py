"""Withdrawal Views - Schedule, Approve, Complete"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse

from .models import Withdrawal
from .forms import WithdrawalForm
from inventory.models import InventoryRecord, InventoryMovement


@login_required
def schedule_withdrawal(request, inventory_pk):
    """Farmer schedules a grain withdrawal."""
    if not request.user.is_farmer:
        messages.error(request, "Only farmers can schedule withdrawals.")
        return redirect('dashboard:home')

    record = get_object_or_404(InventoryRecord, pk=inventory_pk, farmer=request.user)

    if record.remaining_bags <= 0:
        messages.error(request, "No remaining bags to withdraw.")
        return redirect('inventory:detail', pk=inventory_pk)

    form = WithdrawalForm(request.POST or None, inventory_record=record)
    if form.is_valid():
        withdrawal = form.save(commit=False)
        withdrawal.farmer = request.user
        withdrawal.warehouse = record.warehouse
        withdrawal.inventory_record = record
        withdrawal.booking = record.booking
        withdrawal.mt_to_withdraw = round(withdrawal.bags_to_withdraw * 90 / 1000, 3)
        withdrawal.save()
        messages.success(request, f"Withdrawal {withdrawal.withdrawal_ref_short} scheduled for {withdrawal.scheduled_date}.")
        return redirect('withdrawals:detail', pk=withdrawal.pk)

    return render(request, 'withdrawals/schedule.html', {
        'form': form, 'record': record
    })


@login_required
def withdrawal_list(request):
    user = request.user
    if user.is_farmer:
        withdrawals = Withdrawal.objects.filter(farmer=user).order_by('-created_at')
    elif user.is_operator:
        withdrawals = Withdrawal.objects.filter(warehouse__operator=user).order_by('-created_at')
    else:
        withdrawals = Withdrawal.objects.all().order_by('-created_at')

    status_filter = request.GET.get('status', '')
    if status_filter:
        withdrawals = withdrawals.filter(status=status_filter)

    return render(request, 'withdrawals/list.html', {
        'withdrawals': withdrawals,
        'STATUS_CHOICES': Withdrawal.STATUS_CHOICES,
        'status_filter': status_filter,
    })


@login_required
def withdrawal_detail(request, pk):
    user = request.user
    if user.is_farmer:
        withdrawal = get_object_or_404(Withdrawal, pk=pk, farmer=user)
    elif user.is_operator:
        withdrawal = get_object_or_404(Withdrawal, pk=pk, warehouse__operator=user)
    else:
        withdrawal = get_object_or_404(Withdrawal, pk=pk)
    return render(request, 'withdrawals/detail.html', {'withdrawal': withdrawal})


@login_required
def process_withdrawal(request, pk):
    """Handle withdrawal actions: accept, approve, complete, reject, cancel."""
    user = request.user
    if user.is_farmer:
        withdrawal = get_object_or_404(Withdrawal, pk=pk, farmer=user)
    elif user.is_operator:
        withdrawal = get_object_or_404(Withdrawal, pk=pk, warehouse__operator=user)
    else:
        withdrawal = get_object_or_404(Withdrawal, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')

        with transaction.atomic():
            if action == 'accept':
                # Operator accepts the withdrawal request
                if withdrawal.status == Withdrawal.STATUS_SCHEDULED:
                    withdrawal.status = Withdrawal.STATUS_ACCEPTED
                    withdrawal.accepted_by = user
                    withdrawal.accepted_at = timezone.now()
                    withdrawal.operator_notes = request.POST.get('operator_notes', '')
                    withdrawal.save()
                    messages.success(request, f"Withdrawal {withdrawal.withdrawal_ref_short} accepted.")
                else:
                    messages.error(request, "Can only accept scheduled withdrawals.")
            
            elif action == 'approve':
                # Operator approves after accepting
                if withdrawal.status == Withdrawal.STATUS_ACCEPTED:
                    withdrawal.status = Withdrawal.STATUS_APPROVED
                    withdrawal.save()
                    messages.success(request, f"Withdrawal {withdrawal.withdrawal_ref_short} approved.")
                else:
                    messages.error(request, "Withdrawal must be accepted first.")
            
            elif action == 'complete':
                # Complete the withdrawal and update inventory
                if withdrawal.status not in [Withdrawal.STATUS_APPROVED, Withdrawal.STATUS_ACCEPTED]:
                    messages.error(request, "Withdrawal must be accepted/approved before completion.")
                    return redirect('withdrawals:detail', pk=pk)
                
                record = withdrawal.inventory_record
                if withdrawal.bags_to_withdraw > record.remaining_bags:
                    messages.error(request, f"Not enough bags remaining. Available: {record.remaining_bags}, Requested: {withdrawal.bags_to_withdraw}")
                    return redirect('withdrawals:detail', pk=pk)

                # Update inventory
                record.remaining_bags -= withdrawal.bags_to_withdraw
                record.remaining_mt -= withdrawal.mt_to_withdraw
                if record.remaining_bags == 0:
                    record.status = 'fully_withdrawn'
                else:
                    record.status = 'partial_withdrawn'
                record.save()

                # Restore warehouse capacity
                warehouse = withdrawal.warehouse
                warehouse.available_capacity_mt += withdrawal.mt_to_withdraw
                warehouse.save()

                # Log movement
                InventoryMovement.objects.create(
                    inventory=record,
                    movement_type='out',
                    bags_moved=withdrawal.bags_to_withdraw,
                    mt_moved=withdrawal.mt_to_withdraw,
                    performed_by=request.user,
                    reference=withdrawal.withdrawal_ref_short,
                    notes='Withdrawal completed',
                )

                withdrawal.status = Withdrawal.STATUS_COMPLETED
                withdrawal.actual_withdrawal_date = timezone.now().date()
                withdrawal.operator_notes = request.POST.get('operator_notes', '')
                withdrawal.save()

                # Generate withdrawal completion receipt
                _create_withdrawal_receipt(withdrawal)

                messages.success(request, f"Withdrawal {withdrawal.withdrawal_ref_short} completed successfully. Inventory updated.")

            elif action == 'reject':
                # Operator rejects the withdrawal
                if withdrawal.status in [Withdrawal.STATUS_SCHEDULED, Withdrawal.STATUS_ACCEPTED]:
                    withdrawal.status = Withdrawal.STATUS_REJECTED
                    withdrawal.rejection_reason = request.POST.get('rejection_reason', '')
                    withdrawal.operator_notes = request.POST.get('operator_notes', '')
                    withdrawal.save()
                    messages.warning(request, f"Withdrawal {withdrawal.withdrawal_ref_short} rejected.")
                else:
                    messages.error(request, "Cannot reject approved/completed withdrawals.")
            
            elif action == 'cancel':
                # Farmer or operator cancels the withdrawal
                if withdrawal.status != Withdrawal.STATUS_COMPLETED:
                    withdrawal.status = Withdrawal.STATUS_CANCELLED
                    withdrawal.save()
                    messages.warning(request, "Withdrawal cancelled.")
                else:
                    messages.error(request, "Cannot cancel completed withdrawals.")

    return redirect('withdrawals:detail', pk=pk)


def _create_withdrawal_receipt(withdrawal):
    """Generate a receipt for completed withdrawal."""
    from receipts.models import Receipt
    
    Receipt.objects.get_or_create(
        booking=withdrawal.booking,
        defaults={
            'farmer': withdrawal.farmer,
            'warehouse': withdrawal.warehouse,
            'cereal_type': withdrawal.inventory_record.cereal_type,
            'quantity_bags': withdrawal.bags_to_withdraw,
            'quantity_mt': withdrawal.mt_to_withdraw,
            'storage_start_date': withdrawal.booking.storage_start_date,
            'storage_end_date': withdrawal.booking.storage_end_date,
            'total_fee_kes': withdrawal.booking.total_fee_kes,
        }
    )


@login_required
def accept_withdrawal_ajax(request, pk):
    """AJAX endpoint for operator to accept a withdrawal."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=400)
    
    try:
        withdrawal = get_object_or_404(Withdrawal, pk=pk, warehouse__operator=request.user)
        
        if withdrawal.status != Withdrawal.STATUS_SCHEDULED:
            return JsonResponse({
                'status': 'error',
                'message': f'Withdrawal must be scheduled. Current status: {withdrawal.get_status_display()}'
            })
        
        with transaction.atomic():
            withdrawal.status = Withdrawal.STATUS_ACCEPTED
            withdrawal.accepted_by = request.user
            withdrawal.accepted_at = timezone.now()
            withdrawal.operator_notes = request.POST.get('operator_notes', '')
            withdrawal.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Withdrawal {withdrawal.withdrawal_ref_short} accepted',
            'new_status': withdrawal.get_status_display(),
            'withdrawal_status': withdrawal.status,
        })
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def approve_withdrawal_ajax(request, pk):
    """AJAX endpoint for operator to approve a withdrawal."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=400)
    
    try:
        withdrawal = get_object_or_404(Withdrawal, pk=pk, warehouse__operator=request.user)
        
        if withdrawal.status != Withdrawal.STATUS_ACCEPTED:
            return JsonResponse({
                'status': 'error',
                'message': f'Withdrawal must be accepted first. Current status: {withdrawal.get_status_display()}'
            })
        
        with transaction.atomic():
            withdrawal.status = Withdrawal.STATUS_APPROVED
            withdrawal.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Withdrawal {withdrawal.withdrawal_ref_short} approved',
            'new_status': withdrawal.get_status_display(),
            'withdrawal_status': withdrawal.status,
        })
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def complete_withdrawal_ajax(request, pk):
    """AJAX endpoint for operator to complete a withdrawal and update inventory."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=400)
    
    try:
        withdrawal = get_object_or_404(Withdrawal, pk=pk, warehouse__operator=request.user)
        
        if withdrawal.status not in [Withdrawal.STATUS_APPROVED, Withdrawal.STATUS_ACCEPTED]:
            return JsonResponse({
                'status': 'error',
                'message': f'Withdrawal must be approved/accepted. Current status: {withdrawal.get_status_display()}'
            })
        
        record = withdrawal.inventory_record
        if withdrawal.bags_to_withdraw > record.remaining_bags:
            return JsonResponse({
                'status': 'error',
                'message': f'Not enough bags. Available: {record.remaining_bags}, Requested: {withdrawal.bags_to_withdraw}'
            })
        
        with transaction.atomic():
            # Update inventory
            record.remaining_bags -= withdrawal.bags_to_withdraw
            record.remaining_mt -= withdrawal.mt_to_withdraw
            if record.remaining_bags == 0:
                record.status = 'fully_withdrawn'
            else:
                record.status = 'partial_withdrawn'
            record.save()

            # Restore warehouse capacity
            warehouse = withdrawal.warehouse
            warehouse.available_capacity_mt += withdrawal.mt_to_withdraw
            warehouse.save()

            # Log movement
            InventoryMovement.objects.create(
                inventory=record,
                movement_type='out',
                bags_moved=withdrawal.bags_to_withdraw,
                mt_moved=withdrawal.mt_to_withdraw,
                performed_by=request.user,
                reference=withdrawal.withdrawal_ref_short,
                notes='Withdrawal completed via AJAX',
            )

            # Complete the withdrawal
            withdrawal.status = Withdrawal.STATUS_COMPLETED
            withdrawal.actual_withdrawal_date = timezone.now().date()
            withdrawal.operator_notes = request.POST.get('operator_notes', '')
            withdrawal.save()

            # Generate receipt
            _create_withdrawal_receipt(withdrawal)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Withdrawal {withdrawal.withdrawal_ref_short} completed. Inventory updated.',
            'new_status': withdrawal.get_status_display(),
            'withdrawal_status': withdrawal.status,
            'actual_withdrawal_date': withdrawal.actual_withdrawal_date.isoformat(),
            'inventory_update': {
                'remaining_bags': record.remaining_bags,
                'remaining_mt': float(record.remaining_mt),
                'inventory_status': record.get_status_display(),
            },
            'warehouse_update': {
                'available_capacity_mt': float(warehouse.available_capacity_mt),
            }
        })
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def reject_withdrawal_ajax(request, pk):
    """AJAX endpoint for operator to reject a withdrawal."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=400)
    
    try:
        withdrawal = get_object_or_404(Withdrawal, pk=pk, warehouse__operator=request.user)
        
        if withdrawal.status not in [Withdrawal.STATUS_SCHEDULED, Withdrawal.STATUS_ACCEPTED]:
            return JsonResponse({
                'status': 'error',
                'message': f'Can only reject scheduled/accepted withdrawals. Current: {withdrawal.get_status_display()}'
            })
        
        with transaction.atomic():
            withdrawal.status = Withdrawal.STATUS_REJECTED
            withdrawal.rejection_reason = request.POST.get('rejection_reason', '')
            withdrawal.operator_notes = request.POST.get('operator_notes', '')
            withdrawal.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Withdrawal {withdrawal.withdrawal_ref_short} rejected',
            'new_status': withdrawal.get_status_display(),
            'withdrawal_status': withdrawal.status,
        })
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
