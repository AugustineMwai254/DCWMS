"""
Management command to inject sample data into the database
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random

from accounts.models import User, FarmerProfile, OperatorProfile
from warehouses.models import Warehouse, KENYA_COUNTIES_LIST, STORAGE_TYPE_CHOICES, CERTIFICATION_CHOICES
from bookings.models import Booking
from receipts.models import Receipt
from inventory.models import InventoryRecord


class Command(BaseCommand):
    help = 'Inject sample data into the database for testing and demo purposes'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting data injection...'))
        
        # Create operators
        operators = self.create_operators()
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(operators)} operators'))
        
        # Get county operators for warehouse assignment
        county_operators = User.objects.filter(role='operator', username__startswith='operator_')
        if not county_operators.exists():
            # Fallback to regular operators if county operators don't exist
            county_operators = operators
        
        # Create warehouses (5 per county)
        warehouses = self.create_warehouses(list(county_operators))
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(warehouses)} warehouses'))
        
        # Create farmers
        farmers = self.create_farmers()
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(farmers)} farmers'))
        
        # Create bookings with dynamic capacity adjustment
        bookings = self.create_bookings(farmers, warehouses)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(bookings)} bookings'))
        
        # Create receipts and inventory records
        receipts = self.create_receipts(bookings)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(receipts)} receipts'))
        
        inventory = self.create_inventory_records(warehouses, receipts)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(inventory)} inventory records'))
        
        self.stdout.write(self.style.SUCCESS('\n✓ Data injection completed successfully!'))

    def create_operators(self):
        """Create warehouse operators."""
        operators = []
        operator_data = [
            ('John', 'Kipchoge', 'kipchoge_op', 'Nakuru'),
            ('Mary', 'Wanjiru', 'wanjiru_op', 'Nairobi'),
            ('Samuel', 'Otieno', 'otieno_op', 'Kisumu'),
            ('Grace', 'Kamau', 'kamau_op', 'Kiambu'),
            ('Peter', 'Maina', 'maina_op', 'Nyeri'),
        ]
        
        for first, last, username, county in operator_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'email': f'{username}@dcwms.ke',
                    'role': User.ROLE_OPERATOR,
                    'phone_number': f'07{random.randint(10000000, 99999999)}',
                    'national_id': f'{random.randint(10000000, 99999999)}',
                    'is_verified': True,
                    'is_active': True,
                }
            )
            if created:
                user.set_password('operator123')
                user.save()
                OperatorProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'company_name': f'{first} & Co. Grain Storage',
                        'assigned_county': county
                    }
                )
            else:
                # Update existing operator profile with county
                profile, _ = OperatorProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'company_name': f'{first} & Co. Grain Storage',
                        'assigned_county': county
                    }
                )
                if not profile.assigned_county:
                    profile.assigned_county = county
                    profile.save()
            operators.append(user)
        
        return operators

    def create_warehouses(self, operators):
        """Create 5 warehouses per county."""
        warehouses = []
        
        sub_counties_map = {
            'Baringo': ['Baringo Central', 'Eldama Ravine', 'Marigat'],
            'Bomet': ['Bomet Central', 'Chepalungu', 'Sotik'],
            'Bungoma': ['Bungoma Central', 'Bungoma East', 'Bungoma North'],
            'Busia': ['Busia Central', 'Budalangi', 'Nambale'],
            'Elgeyo-Marakwet': ['Iten', 'Keiyo North', 'Marakwet East'],
            'Embu': ['Embu Central', 'Embu North', 'Mbeere North'],
            'Garissa': ['Garissa Central', 'Garissa North', 'Garissa East'],
            'Homa Bay': ['Homa Bay Central', 'Rachuonyo North', 'Rachuonyo South'],
            'Isiolo': ['Isiolo Central', 'Isiolo North', 'Merti'],
            'Kajiado': ['Kajiado Central', 'Kajiado East', 'Kajiado North'],
            'Kakamega': ['Kakamega Central', 'Kakamega East', 'Kakamega South'],
            'Kericho': ['Kericho Central', 'Kipchoge', 'Sigowet'],
            'Kiambu': ['Kiambu Central', 'Kiambu North', 'Kiambu South'],
            'Kilifi': ['Kilifi Central', 'Kilifi East', 'Kilifi North'],
            'Kirinyaga': ['Kirinyaga Central', 'Kirinyaga East', 'Kirinyaga West'],
            'Kisii': ['Kisii Central', 'Kitutu Central', 'Nyaribari Chache'],
            'Kisumu': ['Kisumu Central', 'Kisumu East', 'Kisumu North'],
            'Kitui': ['Kitui Central', 'Kitui East', 'Kitui South'],
            'Kwale': ['Kwale Central', 'Mombasa Central', 'Lunga Lunga'],
            'Laikipia': ['Laikipia East', 'Laikipia North', 'Laikipia West'],
            'Lamu': ['Lamu Central', 'Lamu East', 'Lamu West'],
            'Machakos': ['Machakos Central', 'Machakos East', 'Machakos North'],
            'Makueni': ['Makueni Central', 'Makueni East', 'Makueni North'],
            'Mandera': ['Mandera Central', 'Mandera East', 'Mandera North'],
            'Marsabit': ['Marsabit Central', 'Marsabit East', 'Marsabit North'],
            'Meru': ['Meru Central', 'Meru East', 'Meru North'],
            'Migori': ['Migori Central', 'Migori East', 'Rongo'],
            'Mombasa': ['Mombasa Central', 'Likoni', 'Kisauni'],
            "Murang'a": ["Murang'a Central", "Murang'a East", "Murang'a North"],
            'Nairobi': ['Westlands', 'Central', 'Embakasi'],
            'Nakuru': ['Nakuru Central', 'Nakuru East', 'Nakuru North'],
            'Nandi': ['Nandi Central', 'Nandi North', 'Nandi South'],
            'Narok': ['Narok Central', 'Narok East', 'Narok North'],
            'Nyamira': ['Nyamira Central', 'Nyamira North', 'Nyamira South'],
            'Nyandarua': ['Nyandarua Central', 'Nyandarua North', 'Nyandarua South'],
            'Nyeri': ['Nyeri Central', 'Nyeri East', 'Nyeri North'],
            'Samburu': ['Samburu Central', 'Samburu East', 'Samburu North'],
            'Siaya': ['Siaya Central', 'Siaya East', 'Siaya North'],
            'Taita-Taveta': ['Taita Taveta Central', 'Taita Taveta North', 'Wundanyi'],
            'Tana River': ['Tana North', 'Tana South', 'Tana Central'],
            'Tharaka-Nithi': ['Tharaka', 'Tharaka Central', 'Tharaka South'],
            'Trans Nzoia': ['Trans Nzoia Central', 'Trans Nzoia North', 'Trans Nzoia West'],
            'Turkana': ['Turkana Central', 'Turkana East', 'Turkana North'],
            'Uasin Gishu': ['Uasin Gishu Central', 'Uasin Gishu East', 'Uasin Gishu North'],
            'Vihiga': ['Vihiga Central', 'Vihiga East', 'Vihiga North'],
            'Wajir': ['Wajir Central', 'Wajir East', 'Wajir North'],
            'West Pokot': ['West Pokot Central', 'West Pokot North', 'West Pokot South'],
        }
        
        storage_types = [t[0] for t in STORAGE_TYPE_CHOICES]
        certifications = [c[0] for c in CERTIFICATION_CHOICES]
        
        warehouse_names = [
            'Grain Hub', 'Farmers Coop Store', 'Hermetic Vault', 
            'Certified Depot', 'Regional Storage'
        ]
        
        for county in KENYA_COUNTIES_LIST:
            sub_counties = sub_counties_map.get(county, ['Central', 'East', 'West'])
            
            # Find operators assigned to this county
            county_operators = [op for op in operators if hasattr(op, 'operator_profile') and op.operator_profile.assigned_county == county]
            
            for i in range(5):
                name = f'{county} {warehouse_names[i % len(warehouse_names)]} {i+1}'
                sub_county = sub_counties[i % len(sub_counties)]
                
                # Assign operator from same county, or random if none available
                if county_operators:
                    operator = random.choice(county_operators)
                else:
                    operator = random.choice(operators)
                
                warehouse, created = Warehouse.objects.get_or_create(
                    registration_number=f'WH-{county[:3].upper()}-{i+1:03d}',
                    defaults={
                        'operator': operator,
                        'name': name,
                        'county': county,
                        'sub_county': sub_county,
                        'village': f'Village {i+1}',
                        'physical_address': f'{i+1} Storage Lane, {county}',
                        'latitude': Decimal(str(random.uniform(-4, 5))),
                        'longitude': Decimal(str(random.uniform(33, 42))),
                        'total_capacity_mt': Decimal(str(random.choice([100, 200, 300, 500, 1000]))),
                        'available_capacity_mt': Decimal(str(random.choice([100, 200, 300, 500, 1000]))),
                        'storage_type': random.choice(storage_types),
                        'certification_status': random.choice(certifications),
                        'certification_expiry': timezone.now().date() + timedelta(days=random.randint(30, 730)),
                        'has_pest_control': random.choice([True, False]),
                        'has_moisture_control': random.choice([True, False]),
                        'has_security': True,
                        'has_fumigation': random.choice([True, False]),
                        'accepts_wrs': random.choice([True, False]),
                        'contact_phone': f'07{random.randint(10000000, 99999999)}',
                        'contact_email': f'wh-{i+1}@{county.lower().replace(" ", "")}.ke',
                        'storage_fee_per_bag_month': Decimal(str(random.choice([35, 45, 50, 60]))),
                        'is_active': True,
                    }
                )
                
                if created:
                    warehouse.available_capacity_mt = warehouse.total_capacity_mt
                    warehouse.save()
                
                warehouses.append(warehouse)
        
        return warehouses

    def create_farmers(self):
        """Create sample farmers."""
        farmers = []
        farmer_names = [
            ('John', 'Kipchoge', 'farmer_john', 'Nairobi', 'Westlands'),
            ('Mary', 'Wanjiru', 'farmer_mary', 'Nakuru', 'Bahati'),
            ('Samuel', 'Otieno', 'farmer_samuel', 'Kisumu', 'Kisumu Central'),
            ('Grace', 'Kamau', 'farmer_grace', 'Kericho', 'Kericho Central'),
            ('Peter', 'Maina', 'farmer_peter', 'Kirinyaga', 'Kirinyaga Central'),
            ('Hannah', 'Kipchoge', 'farmer_hannah', 'Bungoma', 'Bungoma Central'),
            ('David', 'Ochieng', 'farmer_david', 'Homa Bay', 'Homa Bay Central'),
            ('Ruth', 'Mutua', 'farmer_ruth', 'Machakos', 'Machakos Central'),
            ('James', 'Kipchoge', 'farmer_james', 'Trans Nzoia', 'Trans Nzoia North'),
            ('Elizabeth', 'Kiplagat', 'farmer_elizabeth', 'Elgeyo-Marakwet', 'Iten'),
        ]
        
        for first, last, username, county, sub_county in farmer_names:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'email': f'{username}@dcwms.ke',
                    'role': User.ROLE_FARMER,
                    'phone_number': f'07{random.randint(10000000, 99999999)}',
                    'national_id': f'{random.randint(10000000, 99999999)}',
                    'county': county,
                    'sub_county': sub_county,
                    'is_verified': True,
                    'is_active': True,
                }
            )
            if created:
                user.set_password('farmer123')
                user.save()
                FarmerProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'farm_size_acres': Decimal(str(random.uniform(0.5, 5))),
                        'main_crop': random.choice(['Maize', 'Wheat', 'Rice', 'Beans']),
                        'cooperative_name': f'{county} Farmers Coop',
                        'annual_production_bags': random.randint(50, 500),
                    }
                )
            farmers.append(user)
        
        return farmers

    def create_bookings(self, farmers, warehouses):
        """Create sample bookings and adjust warehouse capacity dynamically."""
        bookings = []
        
        for i in range(30):
            farmer = random.choice(farmers)
            warehouse = random.choice(warehouses)
            
            # Check if warehouse has enough capacity
            available_bags = warehouse.available_bags
            if available_bags < 10:
                continue
            
            quantity_bags = random.randint(10, min(100, available_bags - 5))
            quantity_mt = Decimal(str(quantity_bags * 90 / 1000))
            
            start_date = timezone.now().date()
            end_date = start_date + timedelta(days=random.randint(30, 180))
            
            booking, created = Booking.objects.get_or_create(
                farmer=farmer,
                warehouse=warehouse,
                storage_start_date=start_date,
                defaults={
                    'cereal_type': random.choice(['maize', 'wheat', 'rice', 'beans']),
                    'quantity_bags': quantity_bags,
                    'quantity_mt': quantity_mt,
                    'storage_end_date': end_date,
                    'status': random.choice(['pending', 'approved']),
                    'farmer_notes': 'Quality grains for storage',
                }
            )
            
            if created:
                booking.total_fee_kes = booking.calculate_fee()
                booking.save()
                
                # DYNAMICALLY ADJUST WAREHOUSE CAPACITY
                warehouse.available_capacity_mt -= quantity_mt
                warehouse.save()
            
            bookings.append(booking)
        
        return bookings

    def create_receipts(self, bookings):
        """Create receipts from approved bookings."""
        receipts = []
        
        for booking in bookings[:len(bookings)//2]:
            if booking.status != 'approved':
                continue
            
            receipt, created = Receipt.objects.get_or_create(
                booking=booking,
                defaults={
                    'farmer': booking.farmer,
                    'warehouse': booking.warehouse,
                    'cereal_type': booking.cereal_type,
                    'quantity_bags': booking.quantity_bags,
                    'quantity_mt': booking.quantity_mt,
                    'storage_start_date': booking.storage_start_date,
                    'storage_end_date': booking.storage_end_date,
                    'total_fee_kes': booking.total_fee_kes,
                    'issued_by': booking.warehouse.operator,
                }
            )
            receipts.append(receipt)
        
        return receipts

    def create_inventory_records(self, warehouses, receipts):
        """Create inventory records and track space changes."""
        records = []
        
        for receipt in receipts:
            quantity = receipt.quantity_mt
            
            record, created = InventoryRecord.objects.get_or_create(
                booking=receipt.booking,
                defaults={
                    'warehouse': receipt.warehouse,
                    'farmer': receipt.farmer,
                    'cereal_type': receipt.cereal_type,
                    'quantity_bags': receipt.quantity_bags,
                    'quantity_mt': quantity,
                    'remaining_bags': receipt.quantity_bags,
                    'remaining_mt': quantity,
                    'status': 'stored',
                    'notes': f'Stock received from {receipt.farmer.get_full_name()}',
                }
            )
            records.append(record)
        
        return records
