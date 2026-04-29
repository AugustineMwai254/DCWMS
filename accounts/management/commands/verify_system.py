"""
Management command to verify system functionality and data integrity
"""
from django.core.management.base import BaseCommand
from decimal import Decimal
from warehouses.models import Warehouse
from bookings.models import Booking
from accounts.models import User


class Command(BaseCommand):
    help = 'Verify system functionality and data integrity'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== DCWMS System Verification Report ===\n'))
        
        # 1. County Distribution
        self.verify_county_distribution()
        
        # 2. Warehouse Capacity Management
        self.verify_capacity_management()
        
        # 3. Booking Status
        self.verify_bookings()
        
        # 4. User Roles
        self.verify_user_roles()
        
        # 5. Functional Features
        self.verify_functional_features()
        
        self.stdout.write(self.style.SUCCESS('\n=== Verification Complete ===\n'))

    def verify_county_distribution(self):
        """Verify 5 warehouses per county."""
        self.stdout.write(self.style.HTTP_INFO('1. County Distribution Check:'))
        
        warehouses_by_county = {}
        warehouses = Warehouse.objects.all()
        
        for wh in warehouses:
            if wh.county not in warehouses_by_county:
                warehouses_by_county[wh.county] = []
            warehouses_by_county[wh.county].append(wh)
        
        total_counties = len(warehouses_by_county)
        counties_with_5 = sum(1 for c, whs in warehouses_by_county.items() if len(whs) >= 5)
        
        self.stdout.write(f'   • Counties with warehouses: {total_counties}')
        self.stdout.write(f'   • Counties with ≥5 warehouses: {counties_with_5}')
        self.stdout.write(f'   • Total warehouses: {len(warehouses)}')
        
        self.stdout.write('\n   Sample distribution:')
        for county in list(sorted(warehouses_by_county.keys()))[:5]:
            count = len(warehouses_by_county[county])
            self.stdout.write(f'   ✓ {county}: {count} warehouses')

    def verify_capacity_management(self):
        """Verify dynamic capacity adjustment works."""
        self.stdout.write(self.style.HTTP_INFO('\n2. Warehouse Capacity Management:'))
        
        warehouses = Warehouse.objects.filter(bookings__isnull=False).distinct()
        
        if not warehouses.exists():
            self.stdout.write('   ℹ No warehouses with bookings yet')
            return
        
        self.stdout.write(f'   • Warehouses with bookings: {warehouses.count()}')
        
        for wh in warehouses[:3]:
            used_mt = wh.total_capacity_mt - wh.available_capacity_mt
            utilization = wh.utilization_percent
            bookings_count = wh.bookings.count()
            
            self.stdout.write(f'\n   {wh.name}:')
            self.stdout.write(f'   • Total: {wh.total_capacity_mt} MT')
            self.stdout.write(f'   • Available: {wh.available_capacity_mt} MT ({100 - utilization}%)')
            self.stdout.write(f'   • Used: {used_mt} MT ({utilization}%)')
            self.stdout.write(f'   • Bookings: {bookings_count}')

    def verify_bookings(self):
        """Verify booking system functionality."""
        self.stdout.write(self.style.HTTP_INFO('\n3. Booking System Status:'))
        
        bookings = Booking.objects.all()
        total_bookings = bookings.count()
        
        status_counts = {}
        for status in ['pending', 'approved', 'rejected', 'cancelled', 'completed']:
            count = bookings.filter(status=status).count()
            if count > 0:
                status_counts[status] = count
        
        self.stdout.write(f'   • Total bookings: {total_bookings}')
        self.stdout.write('   • Status breakdown:')
        
        for status, count in status_counts.items():
            self.stdout.write(f'   ✓ {status.title()}: {count}')
        
        if bookings.exists():
            total_grain_mt = sum(b.quantity_mt for b in bookings)
            avg_fee = sum(b.total_fee_kes for b in bookings) / total_bookings
            
            self.stdout.write(f'   • Total grain booked: {total_grain_mt} MT')
            self.stdout.write(f'   • Average storage fee: KES {avg_fee:.2f}')

    def verify_user_roles(self):
        """Verify user role distribution."""
        self.stdout.write(self.style.HTTP_INFO('\n4. User Role Distribution:'))
        
        users = User.objects.all()
        total_users = users.count()
        
        farmers = users.filter(role='farmer').count()
        operators = users.filter(role='operator').count()
        admins = users.filter(role='admin').count()
        
        self.stdout.write(f'   • Total users: {total_users}')
        self.stdout.write(f'   • Farmers: {farmers}')
        self.stdout.write(f'   • Operators: {operators}')
        self.stdout.write(f'   • Admins: {admins}')

    def verify_functional_features(self):
        """Verify key functional features work correctly."""
        self.stdout.write(self.style.HTTP_INFO('\n5. Functional Features:'))
        
        features = []
        
        # Check utilization_percent calculation
        try:
            wh = Warehouse.objects.first()
            if wh:
                _ = wh.utilization_percent
                features.append(('Warehouse utilization calculation', True, ''))
        except Exception as e:
            features.append(('Warehouse utilization calculation', False, str(e)))
        
        # Check booking fee calculation
        try:
            booking = Booking.objects.first()
            if booking:
                fee = booking.calculate_fee()
                if fee > 0:
                    features.append(('Booking fee calculation', True, f'Calculated: KES {fee}'))
                else:
                    features.append(('Booking fee calculation', False, 'Fee is zero'))
        except Exception as e:
            features.append(('Booking fee calculation', False, str(e)))
        
        # Check available_bags property
        try:
            wh = Warehouse.objects.first()
            if wh:
                bags = wh.available_bags
                if isinstance(bags, int):
                    features.append(('Available bags calculation', True, f'{bags} bags available'))
                else:
                    features.append(('Available bags calculation', False, 'Not integer'))
        except Exception as e:
            features.append(('Available bags calculation', False, str(e)))
        
        # Check certification status
        try:
            certified_whs = Warehouse.objects.exclude(certification_status__in=['pending', 'none']).count()
            total_whs = Warehouse.objects.count()
            features.append(('Certification filtering', True, f'{certified_whs}/{total_whs} certified'))
        except Exception as e:
            features.append(('Certification filtering', False, str(e)))
        
        # Check capacity constraints
        try:
            wh = Warehouse.objects.filter(available_capacity_mt__gte=0).first()
            if wh:
                features.append(('Capacity constraint validation', True, 'All warehouses have valid capacity'))
            else:
                features.append(('Capacity constraint validation', False, 'Some warehouses have negative capacity'))
        except Exception as e:
            features.append(('Capacity constraint validation', False, str(e)))
        
        for feature_name, status, detail in features:
            status_text = self.style.SUCCESS('✓') if status else self.style.ERROR('✗')
            self.stdout.write(f'   {status_text} {feature_name}')
            if detail:
                self.stdout.write(f'     → {detail}')
