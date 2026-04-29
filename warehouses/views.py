"""
Warehouse Views - Finder, CRUD, Detail
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Case, When, Value, IntegerField
from django.core.paginator import Paginator

from .models import Warehouse, COUNTY_CHOICES
from .forms import WarehouseForm, WarehouseSearchForm
from accounts.models import User


def warehouse_finder(request):
    """Public warehouse search - farmers find certified warehouses."""
    form = WarehouseSearchForm(request.GET or None)
    warehouses = Warehouse.objects.filter(is_active=True)
    
    query = request.GET.get('q', '')
    county = request.GET.get('county', '')
    sub_county = request.GET.get('sub_county', '')
    min_capacity = request.GET.get('min_capacity', '')
    storage_type = request.GET.get('storage_type', '')
    certified_only = request.GET.get('certified_only', '')
    sort = request.GET.get('sort', '')

    if query:
        warehouses = warehouses.filter(
            Q(name__icontains=query) |
            Q(county__icontains=query) |
            Q(sub_county__icontains=query)
        )
    if county:
        warehouses = warehouses.filter(county=county)
    if sub_county:
        warehouses = warehouses.filter(sub_county__icontains=sub_county)
    if min_capacity:
        try:
            warehouses = warehouses.filter(available_capacity_mt__gte=float(min_capacity))
        except ValueError:
            pass
    if storage_type:
        warehouses = warehouses.filter(storage_type=storage_type)
    if certified_only:
        warehouses = warehouses.exclude(certification_status__in=['pending', 'none'])

    # Only show warehouses with available capacity
    warehouses = warehouses.filter(available_capacity_mt__gt=0)

    if sort == 'nearest' and county:
        warehouses = warehouses.annotate(
            same_county=Case(
                When(county=county, then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            ),
            same_sub_county=Case(
                When(sub_county__iexact=sub_county, then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            )
        ).order_by('same_county', 'same_sub_county', '-available_capacity_mt')
    else:
        warehouses = warehouses.order_by('-available_capacity_mt')
    
    paginator = Paginator(warehouses, 12)
    page = request.GET.get('page', 1)
    warehouses_page = paginator.get_page(page)

    return render(request, 'warehouses/finder.html', {
        'warehouses': warehouses_page,
        'form': form,
        'counties': COUNTY_CHOICES,
        'total_results': warehouses.count(),
    })


def warehouse_detail(request, pk):
    """View warehouse details."""
    warehouse = get_object_or_404(Warehouse, pk=pk, is_active=True)
    return render(request, 'warehouses/detail.html', {'warehouse': warehouse})


@login_required
def warehouse_create(request):
    """Operators create new warehouse profiles."""
    if not request.user.is_operator and not request.user.is_admin_user:
        messages.error(request, "Only warehouse operators can create warehouses.")
        return redirect('dashboard:home')
    
    from .forms import WarehouseForm
    form = WarehouseForm(request.POST or None)
    if form.is_valid():
        warehouse = form.save(commit=False)
        warehouse.operator = request.user
        
        # Restrict operators to their assigned county
        if request.user.is_operator and hasattr(request.user, 'operator_profile'):
            assigned_county = request.user.operator_profile.assigned_county
            if warehouse.county != assigned_county:
                messages.error(request, f"You can only create warehouses in {assigned_county}.")
                return render(request, 'warehouses/form.html', {'form': form, 'action': 'Create'})
        
        # Set available = total on creation
        warehouse.available_capacity_mt = warehouse.total_capacity_mt
        # Generate registration number
        import uuid
        warehouse.registration_number = f"WH-{str(uuid.uuid4())[:8].upper()}"
        warehouse.save()
        messages.success(request, f"Warehouse '{warehouse.name}' created successfully!")
        return redirect('warehouses:detail', pk=warehouse.pk)
    
    return render(request, 'warehouses/form.html', {'form': form, 'action': 'Create'})


@login_required
def warehouse_edit(request, pk):
    """Edit warehouse profile."""
    warehouse = get_object_or_404(Warehouse, pk=pk)
    
    if warehouse.operator != request.user and not request.user.is_admin_user:
        messages.error(request, "You can only edit your own warehouses.")
        return redirect('warehouses:detail', pk=pk)
    
    from .forms import WarehouseForm
    form = WarehouseForm(request.POST or None, instance=warehouse)
    if form.is_valid():
        form.save()
        messages.success(request, "Warehouse updated successfully!")
        return redirect('warehouses:detail', pk=pk)
    
    return render(request, 'warehouses/form.html', {'form': form, 'warehouse': warehouse, 'action': 'Edit'})


@login_required
def my_warehouses(request):
    """Operator's warehouse list."""
    if not request.user.is_operator and not request.user.is_admin_user:
        return redirect('dashboard:home')
    
    warehouses = Warehouse.objects.filter(operator=request.user)
    
    # Filter by assigned county if operator
    if request.user.is_operator and hasattr(request.user, 'operator_profile'):
        assigned_county = request.user.operator_profile.assigned_county
        warehouses = warehouses.filter(county=assigned_county)
    
    return render(request, 'warehouses/my_warehouses.html', {'warehouses': warehouses})


@login_required
def warehouse_toggle_status(request, pk):
    """Activate/deactivate warehouse."""
    warehouse = get_object_or_404(Warehouse, pk=pk, operator=request.user)
    warehouse.is_active = not warehouse.is_active
    warehouse.save()
    status = "activated" if warehouse.is_active else "deactivated"
    messages.success(request, f"Warehouse {status}.")
    return redirect('warehouses:my_warehouses')
