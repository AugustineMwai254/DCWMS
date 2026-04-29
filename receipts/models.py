"""
Digital Receipt Models - Warehouse Receipt System
"""
import uuid
import hashlib
from django.db import models
from django.conf import settings


class Receipt(models.Model):
    """Digital Warehouse Receipt (e-WRS)."""
    
    # Unique receipt identifiers
    receipt_number = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    receipt_code = models.CharField(max_length=20, unique=True, editable=False)
    security_hash = models.CharField(max_length=64, editable=False)  # SHA-256
    
    booking = models.OneToOneField(
        'bookings.Booking', on_delete=models.CASCADE, related_name='receipt'
    )
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='receipts', limit_choices_to={'role': 'farmer'}
    )
    warehouse = models.ForeignKey(
        'warehouses.Warehouse', on_delete=models.CASCADE, related_name='receipts'
    )
    
    # Grain details
    cereal_type = models.CharField(max_length=30)
    quantity_bags = models.IntegerField()
    quantity_mt = models.DecimalField(max_digits=8, decimal_places=3)
    
    # Storage period
    storage_start_date = models.DateField()
    storage_end_date = models.DateField()
    
    # Financial
    total_fee_kes = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Issuance
    issued_at = models.DateTimeField(auto_now_add=True)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='issued_receipts'
    )
    
    # Status
    is_valid = models.BooleanField(default=True)
    voided_at = models.DateTimeField(null=True, blank=True)
    void_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-issued_at']

    def __str__(self):
        return f"Receipt {self.receipt_code} | {self.farmer.get_full_name()} | {self.warehouse.name}"

    def save(self, *args, **kwargs):
        if not self.receipt_code:
            # Generate short human-readable code: RC-XXXXXXXX
            self.receipt_code = f"RC-{str(self.receipt_number)[:8].upper()}"
        
        if not self.security_hash:
            # Generate verification hash
            data = f"{self.receipt_number}{self.farmer_id}{self.warehouse_id}{self.quantity_mt}{self.issued_at or ''}"
            self.security_hash = hashlib.sha256(data.encode()).hexdigest()
        
        super().save(*args, **kwargs)

    @property
    def receipt_ref(self):
        return self.receipt_code

    def verify(self, provided_hash):
        """Verify receipt authenticity."""
        return self.security_hash == provided_hash

    def generate_qr_code(self):
        """Generate QR code containing verification URL."""
        import qrcode
        from io import BytesIO
        from django.core.files.base import ContentFile
        
        # Create QR code with verification URL
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(f"https://dcwms.com/receipts/verify/?code={self.receipt_code}")
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer.getvalue()
