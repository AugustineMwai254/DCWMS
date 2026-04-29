"""
Management command to create one operator per county with password 'musangi254'
"""
from django.core.management.base import BaseCommand
from accounts.models import User, OperatorProfile, KENYA_COUNTIES_LIST


class Command(BaseCommand):
    help = 'Create one warehouse operator per county with password musangi254'

    def handle(self, *args, **options):
        password = 'musangi254'
        created_count = 0

        for idx, county in enumerate(KENYA_COUNTIES_LIST, start=1):
            username = f'operator_{county.lower().replace(" ", "_").replace("\'", "")}'.replace("'", "")
            email = f'operator.{county.lower().replace(" ", ".").replace("\'", "")}@dcwms.local'.replace("'", "")
            
            # Check if operator already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f'Operator {username} already exists, skipping...'))
                continue
            
            try:
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=f'County Operator',
                    last_name=county,
                    role=User.ROLE_OPERATOR,
                    county=county,
                    is_active=True
                )
                user.set_password(password)
                user.save()
                
                # Create operator profile
                company_name = f'{county} Warehouse Services'
                OperatorProfile.objects.create(
                    user=user,
                    company_name=company_name,
                    business_license=f'WC-{idx:03d}-{county[:3].upper()}',
                    assigned_county=county
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created operator for {county}: {username} (password: {password})'
                    )
                )
                created_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Error creating operator for {county}: {str(e)}'))

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Successfully created {created_count} county operators')
        )
