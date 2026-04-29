"""
Accounts Views - Registration, Login, Dashboard routing
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum

from .forms import FarmerRegistrationForm, OperatorRegistrationForm, LoginForm
from .models import User
from warehouses.models import Warehouse
from bookings.models import Booking
from inventory.models import InventoryRecord
from withdrawals.models import Withdrawal


def landing_page(request):
    """
    Display landing page. If user is authenticated, redirect to dashboard.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    return render(request, 'landing.html')


def register_farmer(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    form = FarmerRegistrationForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Welcome, {user.first_name}! Your farmer account has been created.")
        return redirect('dashboard:home')
    return render(request, 'accounts/register_farmer.html', {'form': form})


def register_operator(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    form = OperatorRegistrationForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Welcome, {user.first_name}! Operator account created. Please complete your warehouse profile.")
        return redirect('warehouses:create')
    return render(request, 'accounts/register_operator.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    form = LoginForm(request, data=request.POST or None)
    if form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, f"Welcome back, {user.first_name or user.username}!")
        return redirect(request.GET.get('next', 'dashboard:home'))
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('accounts:login')


@login_required
def profile_view(request):
    from .forms import UserProfileForm
    form = UserProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {'form': form})


# --- DASHBOARD VIEWS ---

@login_required
def dashboard_home(request):
    user = request.user
    ctx = {}

    if user.is_farmer:
        ctx['my_bookings'] = Booking.objects.filter(farmer=user).order_by('-created_at')[:5]
        ctx['pending_bookings'] = Booking.objects.filter(farmer=user, status='pending').count()
        ctx['active_bookings'] = Booking.objects.filter(farmer=user, status='approved').count()
        ctx['my_withdrawals'] = Withdrawal.objects.filter(farmer=user).order_by('-created_at')[:5]
        ctx['total_bookings'] = Booking.objects.filter(farmer=user).count()

    elif user.is_operator:
        my_warehouses = Warehouse.objects.filter(operator=user)
        
        # Filter by assigned county
        if hasattr(user, 'operator_profile'):
            assigned_county = user.operator_profile.assigned_county
            my_warehouses = my_warehouses.filter(county=assigned_county)
            
            ctx['my_warehouses'] = my_warehouses
            ctx['warehouse_count'] = my_warehouses.count()
            
            # Get pending bookings for approval
            pending_bookings_qs = Booking.objects.filter(
                warehouse__operator=user, status='pending_payment', warehouse__county=assigned_county
            ).order_by('-created_at')
            ctx['pending_bookings'] = pending_bookings_qs.count()
            ctx['pending_bookings_list'] = pending_bookings_qs[:10]
            
            ctx['approved_bookings'] = Booking.objects.filter(
                warehouse__operator=user, status='confirmed', warehouse__county=assigned_county
            ).count()
            
            # Get payments made
            from payments.models import Payment
            payments_made = Payment.objects.filter(
                booking__warehouse__operator=user,
                booking__warehouse__county=assigned_county,
                status=Payment.STATUS_COMPLETED
            ).order_by('-completed_at')[:10]
            ctx['payments_made'] = payments_made
            ctx['payments_made_count'] = Payment.objects.filter(
                booking__warehouse__operator=user,
                booking__warehouse__county=assigned_county,
                status=Payment.STATUS_COMPLETED
            ).count()
            
            ctx['recent_bookings'] = Booking.objects.filter(
                warehouse__operator=user, warehouse__county=assigned_county
            ).order_by('-created_at')[:10]
            
            # Get pending withdrawals (scheduled or accepted)
            pending_withdrawals_qs = Withdrawal.objects.filter(
                warehouse__operator=user, 
                status__in=['scheduled', 'accepted'],
                warehouse__county=assigned_county
            ).order_by('-created_at')
            ctx['pending_withdrawals'] = pending_withdrawals_qs.count()
            ctx['pending_withdrawals_list'] = pending_withdrawals_qs[:10]
            
            # Get completed withdrawals for stats
            ctx['completed_withdrawals'] = Withdrawal.objects.filter(
                warehouse__operator=user,
                status='completed',
                warehouse__county=assigned_county
            ).count()
        else:
            ctx['my_warehouses'] = my_warehouses
            ctx['warehouse_count'] = my_warehouses.count()
            
            # Get pending bookings for approval
            pending_bookings_qs = Booking.objects.filter(
                warehouse__operator=user, status='pending_payment'
            ).order_by('-created_at')
            ctx['pending_bookings'] = pending_bookings_qs.count()
            ctx['pending_bookings_list'] = pending_bookings_qs[:10]
            
            ctx['approved_bookings'] = Booking.objects.filter(warehouse__operator=user, status='confirmed').count()
            
            # Get payments made
            from payments.models import Payment
            payments_made = Payment.objects.filter(
                booking__warehouse__operator=user,
                status=Payment.STATUS_COMPLETED
            ).order_by('-completed_at')[:10]
            ctx['payments_made'] = payments_made
            ctx['payments_made_count'] = Payment.objects.filter(
                booking__warehouse__operator=user,
                status=Payment.STATUS_COMPLETED
            ).count()
            
            ctx['recent_bookings'] = Booking.objects.filter(warehouse__operator=user).order_by('-created_at')[:10]
            
            # Get pending withdrawals (scheduled or accepted)
            pending_withdrawals_qs = Withdrawal.objects.filter(
                warehouse__operator=user,
                status__in=['scheduled', 'accepted']
            ).order_by('-created_at')
            ctx['pending_withdrawals'] = pending_withdrawals_qs.count()
            ctx['pending_withdrawals_list'] = pending_withdrawals_qs[:10]
            
            # Get completed withdrawals for stats
            ctx['completed_withdrawals'] = Withdrawal.objects.filter(
                warehouse__operator=user,
                status='completed'
            ).count()

    elif user.is_admin_user:
        ctx['total_warehouses'] = Warehouse.objects.count()
        ctx['total_farmers'] = User.objects.filter(role='farmer').count()
        ctx['total_operators'] = User.objects.filter(role='operator').count()
        ctx['total_bookings'] = Booking.objects.count()
        ctx['pending_bookings'] = Booking.objects.filter(status='pending').count()
        ctx['recent_bookings'] = Booking.objects.order_by('-created_at')[:10]

    return render(request, 'accounts/dashboard.html', ctx)
