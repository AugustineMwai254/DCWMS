"""
Accounts Models - Custom User with Role-Based Access
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


KENYA_COUNTIES_LIST = [
    'Baringo', 'Bomet', 'Bungoma', 'Busia', 'Elgeyo-Marakwet', 'Embu',
    'Garissa', 'Homa Bay', 'Isiolo', 'Kajiado', 'Kakamega', 'Kericho',
    'Kiambu', 'Kilifi', 'Kirinyaga', 'Kisii', 'Kisumu', 'Kitui', 'Kwale',
    'Laikipia', 'Lamu', 'Machakos', 'Makueni', 'Mandera', 'Marsabit', 'Meru',
    'Migori', 'Mombasa', "Murang'a", 'Nairobi', 'Nakuru', 'Nandi', 'Narok',
    'Nyamira', 'Nyandarua', 'Nyeri', 'Samburu', 'Siaya', 'Taita-Taveta',
    'Tana River', 'Tharaka-Nithi', 'Trans Nzoia', 'Turkana', 'Uasin Gishu',
    'Vihiga', 'Wajir', 'West Pokot',
]

COUNTY_CHOICES = [(c, c) for c in KENYA_COUNTIES_LIST]


class User(AbstractUser):
    """Custom user with farmer/operator/admin roles."""
    
    ROLE_FARMER = 'farmer'
    ROLE_OPERATOR = 'operator'
    ROLE_ADMIN = 'admin'
    
    ROLE_CHOICES = [
        (ROLE_FARMER, 'Farmer'),
        (ROLE_OPERATOR, 'Warehouse Operator'),
        (ROLE_ADMIN, 'Admin'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_FARMER)
    phone_number = models.CharField(max_length=15, blank=True)
    national_id = models.CharField(max_length=20, blank=True, unique=True, null=True)
    county = models.CharField(max_length=100, blank=True)
    sub_county = models.CharField(max_length=100, blank=True)
    village = models.CharField(max_length=100, blank=True)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_farmer(self):
        return self.role == self.ROLE_FARMER

    @property
    def is_operator(self):
        return self.role == self.ROLE_OPERATOR

    @property
    def is_admin_user(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser


class FarmerProfile(models.Model):
    """Extended profile for farmers."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='farmer_profile')
    farm_size_acres = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    main_crop = models.CharField(max_length=100, default='Maize')
    cooperative_name = models.CharField(max_length=200, blank=True)
    annual_production_bags = models.IntegerField(null=True, blank=True, help_text="Estimated bags per year (90kg)")

    def __str__(self):
        return f"Profile: {self.user.username}"


class OperatorProfile(models.Model):
    """Extended profile for warehouse operators."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='operator_profile')
    company_name = models.CharField(max_length=200)
    business_license = models.CharField(max_length=100, blank=True)
    assigned_county = models.CharField(
        max_length=100, choices=COUNTY_CHOICES,
        help_text="County where this operator manages warehouses"
    )
    
    def __str__(self):
        return f"Operator: {self.company_name} ({self.assigned_county})"
