"""
Payment Models - MPesa Integration for Booking Payments
"""
import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class Payment(models.Model):
    """MPesa payment record for booking fees."""

    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    PAYMENT_METHOD_MPESA = 'mpesa'
    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_METHOD_MPESA, 'M-Pesa'),
    ]

    payment_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    booking = models.OneToOneField('bookings.Booking', on_delete=models.CASCADE, related_name='payment')
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')

    amount_kes = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default=PAYMENT_METHOD_MPESA)

    # MPesa specific fields
    mpesa_receipt_number = models.CharField(max_length=20, blank=True, null=True)
    mpesa_transaction_id = models.CharField(max_length=50, blank=True, null=True)
    mpesa_phone_number = models.CharField(max_length=15, blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Callback data
    callback_data = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-initiated_at']

    def __str__(self):
        return f"Payment {self.payment_id} - {self.amount_kes} KES - {self.status}"

    @property
    def payment_ref(self):
        return f"PAY-{str(self.payment_id)[:8].upper()}"

    @property
    def tracking_code(self):
        """Generate tracking code from M-Pesa receipt or payment ID."""
        if self.mpesa_receipt_number:
            return f"TRK-{self.mpesa_receipt_number}"
        return self.payment_ref

    def mark_completed(self, receipt_number=None, transaction_id=None):
        """Mark payment as completed and auto-approve booking."""
        from django.utils import timezone
        self.status = self.STATUS_COMPLETED
        self.completed_at = timezone.now()
        if receipt_number:
            self.mpesa_receipt_number = receipt_number
        if transaction_id:
            self.mpesa_transaction_id = transaction_id
        self.save()

        # Auto-approve the booking
        self.booking.status = self.booking.STATUS_CONFIRMED
        self.booking.save()

        # Create inventory record and generate automated receipt
        self._create_inventory_record()

    def _create_inventory_record(self):
        """Create inventory record for approved booking and its digital receipt."""
        from inventory.models import InventoryRecord

        booking = self.booking
        warehouse = booking.warehouse

        # Update warehouse capacity
        warehouse.available_capacity_mt -= booking.quantity_mt
        warehouse.save()

        # Create inventory record
        InventoryRecord.objects.get_or_create(
            warehouse=warehouse,
            farmer=booking.farmer,
            cereal_type=booking.cereal_type,
            booking=booking,
            defaults={
                'quantity_bags': booking.quantity_bags,
                'quantity_mt': booking.quantity_mt,
                'status': 'stored',
            }
        )

        # Generate receipt for the paid booking
        from receipts.models import Receipt
        Receipt.objects.get_or_create(
            booking=booking,
            defaults={
                'farmer': booking.farmer,
                'warehouse': warehouse,
                'cereal_type': booking.cereal_type,
                'quantity_bags': booking.quantity_bags,
                'quantity_mt': booking.quantity_mt,
                'storage_start_date': booking.storage_start_date,
                'storage_end_date': booking.storage_end_date,
                'total_fee_kes': booking.total_fee_kes,
                'issued_by': booking.farmer,
            }
        )