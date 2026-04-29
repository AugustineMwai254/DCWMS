"""
Inventory Models - Track Grain in Warehouse
"""
from django.db import models
from django.conf import settings


class InventoryRecord(models.Model):
    STATUS_CHOICES = [
        ('stored', 'In Storage'),
        ('partial_withdrawn', 'Partially Withdrawn'),
        ('fully_withdrawn', 'Fully Withdrawn'),
        ('spoiled', 'Spoiled/Condemned'),
    ]

    warehouse = models.ForeignKey('warehouses.Warehouse', on_delete=models.CASCADE, related_name='inventory')
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='inventory')
    booking = models.OneToOneField('bookings.Booking', on_delete=models.CASCADE, related_name='inventory_record', null=True, blank=True)
    cereal_type = models.CharField(max_length=30)
    quantity_bags = models.IntegerField()
    quantity_mt = models.DecimalField(max_digits=8, decimal_places=3)
    remaining_bags = models.IntegerField()
    remaining_mt = models.DecimalField(max_digits=8, decimal_places=3)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='stored')
    date_stored = models.DateField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date_stored']

    def __str__(self):
        return f"{self.farmer.get_full_name()} | {self.cereal_type} | {self.remaining_bags} bags @ {self.warehouse.name}"

    def save(self, *args, **kwargs):
        if not self.pk:  # New record
            self.remaining_bags = self.quantity_bags
            self.remaining_mt = self.quantity_mt
        super().save(*args, **kwargs)


class InventoryMovement(models.Model):
    """Audit log of all grain movements."""
    MOVEMENT_IN = 'in'
    MOVEMENT_OUT = 'out'
    MOVEMENT_ADJUST = 'adjust'

    MOVEMENT_CHOICES = [
        (MOVEMENT_IN, 'Inbound (Deposit)'),
        (MOVEMENT_OUT, 'Outbound (Withdrawal)'),
        (MOVEMENT_ADJUST, 'Adjustment'),
    ]

    inventory = models.ForeignKey(InventoryRecord, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_CHOICES)
    bags_moved = models.IntegerField()
    mt_moved = models.DecimalField(max_digits=8, decimal_places=3)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.movement_type.upper()} | {self.bags_moved} bags | {self.timestamp.strftime('%Y-%m-%d')}"
