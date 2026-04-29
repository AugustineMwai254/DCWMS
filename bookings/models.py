"""
Booking Models - Storage Space Reservation
"""
import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone


class Booking(models.Model):
    """Farmer storage booking."""

    STATUS_PENDING_PAYMENT = 'pending_payment'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_ACTIVE = 'active'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING_PAYMENT, 'Pending Payment'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    CEREAL_CHOICES = [
        ('maize', 'Maize'), ('wheat', 'Wheat'), ('sorghum', 'Sorghum'),
        ('millet', 'Millet'), ('barley', 'Barley'), ('rice', 'Rice'),
        ('beans', 'Beans'), ('peas', 'Peas'), ('other', 'Other'),
    ]

    booking_reference = models.CharField(max_length=20, unique=True, editable=False)
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='bookings', limit_choices_to={'role': 'farmer'}
    )
    warehouse = models.ForeignKey(
        'warehouses.Warehouse', on_delete=models.CASCADE, related_name='bookings'
    )
    
    cereal_type = models.CharField(max_length=30, choices=CEREAL_CHOICES, default='maize')
    quantity_bags = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Number of 90kg bags"
    )
    quantity_mt = models.DecimalField(
        max_digits=8, decimal_places=3,
        help_text="Weight in metric tonnes (auto-calculated)"
    )
    
    # Duration
    storage_start_date = models.DateField()
    storage_end_date = models.DateField()
    
    # Pricing
    total_fee_kes = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING_PAYMENT)
    
    # Notes
    farmer_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.booking_reference} | {self.farmer.get_full_name()} | {self.warehouse.name}"

    @property
    def booking_ref_short(self):
        return self.booking_reference

    @property
    def booking_ref_human(self):
        return self.booking_reference or 'BK-UNKNOWN'

    def calculate_fee(self):
        """Calculate storage fee based on bags, duration, and warehouse rate."""
        from datetime import timedelta
        if self.storage_start_date and self.storage_end_date:
            days = (self.storage_end_date - self.storage_start_date).days
            months = max(1, days / 30)
            fee = self.quantity_bags * float(self.warehouse.storage_fee_per_bag_month) * months
            return round(fee, 2)
        return 0

    def save(self, *args, **kwargs):
        # Auto-calculate metric tonnes from bags
        self.quantity_mt = round(self.quantity_bags * 90 / 1000, 3)
        # Calculate fee only if not already set
        if not self.total_fee_kes:
            self.total_fee_kes = self.calculate_fee()

        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and not self.booking_reference:
            month = self.created_at.strftime('%b')
            self.booking_reference = f"BK-{month}-{self.created_at.year}-{self.pk:03d}"
            super().save(update_fields=['booking_reference'])
