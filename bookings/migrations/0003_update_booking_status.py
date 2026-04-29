# Generated manually for bookings status changes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0002_alter_booking_booking_reference'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='status',
            field=models.CharField(choices=[('pending_payment', 'Pending Payment'), ('confirmed', 'Confirmed'), ('active', 'Active'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending_payment', max_length=20),
        ),
        migrations.RemoveField(
            model_name='booking',
            name='operator_notes',
        ),
        migrations.RemoveField(
            model_name='booking',
            name='rejection_reason',
        ),
        migrations.RemoveField(
            model_name='booking',
            name='approved_at',
        ),
        migrations.RemoveField(
            model_name='booking',
            name='approved_by',
        ),
    ]