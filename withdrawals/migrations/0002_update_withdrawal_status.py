# Generated manually for withdrawals status changes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('withdrawals', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='withdrawal',
            name='status',
            field=models.CharField(choices=[('scheduled', 'Scheduled'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='scheduled', max_length=20),
        ),
        migrations.RemoveField(
            model_name='withdrawal',
            name='operator_notes',
        ),
        migrations.RemoveField(
            model_name='withdrawal',
            name='rejection_reason',
        ),
        migrations.RemoveField(
            model_name='withdrawal',
            name='approved_by',
        ),
    ]