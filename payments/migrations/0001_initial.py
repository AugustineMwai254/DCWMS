# Generated manually for payments app

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('bookings', '0002_alter_booking_booking_reference'),
        ('accounts', '0002_operatorprofile_assigned_county'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('amount_kes', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('payment_method', models.CharField(choices=[('mpesa', 'M-Pesa')], default='mpesa', max_length=20)),
                ('mpesa_receipt_number', models.CharField(blank=True, max_length=20, null=True)),
                ('mpesa_transaction_id', models.CharField(blank=True, max_length=50, null=True)),
                ('mpesa_phone_number', models.CharField(blank=True, max_length=15, null=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('initiated_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('callback_data', models.JSONField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True)),
                ('booking', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='payment', to='bookings.booking')),
                ('farmer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='accounts.user')),
            ],
            options={
                'ordering': ['-initiated_at'],
            },
        ),
    ]