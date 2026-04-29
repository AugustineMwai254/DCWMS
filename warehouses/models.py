"""
Warehouse Models - Profiles, Capacity, Certification
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from accounts.models import KENYA_COUNTIES_LIST, COUNTY_CHOICES

STORAGE_TYPE_CHOICES = [
    ('bulk', 'Bulk Storage'),
    ('bagged', 'Bagged Storage'),
    ('both', 'Bulk & Bagged'),
    ('hermetic', 'Hermetic Bags/Silos'),
    ('cold', 'Cold Storage'),
]

CERTIFICATION_CHOICES = [
    ('ncpb', 'NCPB Certified'),
    ('wrsc', 'WRSC Certified'),
    ('both', 'NCPB & WRSC Certified'),
    ('pending', 'Certification Pending'),
    ('none', 'Not Certified'),
]


class Warehouse(models.Model):
    """Certified warehouse profile."""
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='warehouses',
        limit_choices_to={'role': 'operator'}
    )
    name = models.CharField(max_length=200)
    registration_number = models.CharField(max_length=50, unique=True, blank=True)
    county = models.CharField(max_length=100, choices=COUNTY_CHOICES)
    sub_county = models.CharField(max_length=100)
    village = models.CharField(max_length=100, blank=True)
    physical_address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Capacity fields (in metric tonnes)
    total_capacity_mt = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Total capacity in metric tonnes"
    )
    available_capacity_mt = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Currently available capacity in metric tonnes"
    )
    
    storage_type = models.CharField(max_length=20, choices=STORAGE_TYPE_CHOICES, default='bagged')
    certification_status = models.CharField(max_length=20, choices=CERTIFICATION_CHOICES, default='wrsc')
    certification_expiry = models.DateField(null=True, blank=True)
    
    # Features
    has_pest_control = models.BooleanField(default=True)
    has_moisture_control = models.BooleanField(default=False)
    has_security = models.BooleanField(default=True)
    has_fumigation = models.BooleanField(default=False)
    accepts_wrs = models.BooleanField(default=True, verbose_name="Accepts WRS Receipts")
    
    # Contact
    contact_phone = models.CharField(max_length=15)
    contact_email = models.EmailField(blank=True)
    
    # Pricing (KES per bag per month, 90kg bag)
    storage_fee_per_bag_month = models.DecimalField(
        max_digits=8, decimal_places=2, default=50.00,
        help_text="KES per 90kg bag per month"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Warehouse'
        verbose_name_plural = 'Warehouses'

    def __str__(self):
        return f"{self.name} - {self.county}"

    @property
    def utilization_percent(self):
        if self.total_capacity_mt > 0:
            used = self.total_capacity_mt - self.available_capacity_mt
            return round((used / self.total_capacity_mt) * 100, 1)
        return 0

    @property
    def is_certified(self):
        return self.certification_status not in ['pending', 'none']

    @property
    def available_bags(self):
        """Convert available MT to 90kg bags."""
        return int(self.available_capacity_mt * 1000 / 90)

    @property
    def total_bags(self):
        return int(self.total_capacity_mt * 1000 / 90)


class WarehouseImage(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='warehouses/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.warehouse.name}"
