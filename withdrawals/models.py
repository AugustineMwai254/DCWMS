"""
Withdrawal Models - Schedule and Manage Grain Retrieval
"""
import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class Withdrawal(models.Model):
    STATUS_SCHEDULED = 'scheduled'
    STATUS_ACCEPTED = 'accepted'
    STATUS_APPROVED = 'approved'
    STATUS_COMPLETED = 'completed'
    STATUS_REJECTED = 'rejected'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    withdrawal_reference = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='withdrawals', limit_choices_to={'role': 'farmer'}
    )
    warehouse = models.ForeignKey('warehouses.Warehouse', on_delete=models.CASCADE, related_name='withdrawals')
    inventory_record = models.ForeignKey('inventory.InventoryRecord', on_delete=models.CASCADE, related_name='withdrawals')
    booking = models.ForeignKey('bookings.Booking', on_delete=models.CASCADE, related_name='withdrawals')

    bags_to_withdraw = models.IntegerField(validators=[MinValueValidator(1)])
    mt_to_withdraw = models.DecimalField(max_digits=8, decimal_places=3)
    scheduled_date = models.DateField()
    actual_withdrawal_date = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SCHEDULED)
    farmer_notes = models.TextField(blank=True)
    operator_notes = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Track who accepted/approved
    accepted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='accepted_withdrawals')
    accepted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        ref = str(self.withdrawal_reference)[:8].upper()
        return f"WD-{ref} | {self.farmer.get_full_name()} | {self.bags_to_withdraw} bags"

    @property
    def withdrawal_ref_short(self):
        return f"WD-{str(self.withdrawal_reference)[:8].upper()}"

    def save(self, *args, **kwargs):
        self.mt_to_withdraw = round(self.bags_to_withdraw * 90 / 1000, 3)
        super().save(*args, **kwargs)
