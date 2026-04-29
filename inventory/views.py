"""Inventory Views"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import InventoryRecord


@login_required
def inventory_list(request):
    user = request.user
    if user.is_farmer:
        records = InventoryRecord.objects.filter(farmer=user).exclude(status='fully_withdrawn')
    elif user.is_operator:
        records = InventoryRecord.objects.filter(warehouse__operator=user)
    else:
        records = InventoryRecord.objects.all()

    warehouse_filter = request.GET.get('warehouse', '')
    status_filter = request.GET.get('status', '')
    if warehouse_filter:
        records = records.filter(warehouse_id=warehouse_filter)
    if status_filter:
        records = records.filter(status=status_filter)

    return render(request, 'inventory/list.html', {
        'records': records,
        'STATUS_CHOICES': InventoryRecord.STATUS_CHOICES,
    })


@login_required
def inventory_detail(request, pk):
    user = request.user
    if user.is_farmer:
        record = get_object_or_404(InventoryRecord, pk=pk, farmer=user)
    else:
        record = get_object_or_404(InventoryRecord, pk=pk)
    movements = record.movements.order_by('-timestamp')
    return render(request, 'inventory/detail.html', {'record': record, 'movements': movements})
