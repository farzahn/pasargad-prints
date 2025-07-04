# Generated manually to update Goshippo fields structure

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_rename_shipstation_to_goshippo'),
    ]

    operations = [
        # Remove the old goshippo_transaction_id field (was renamed from shipstation_order_id)
        migrations.RemoveField(
            model_name='order',
            name='goshippo_transaction_id',
        ),
        # Add proper Goshippo fields
        migrations.AddField(
            model_name='order',
            name='shippo_shipment_id',
            field=models.CharField(blank=True, help_text='Goshippo shipment ID', max_length=50),
        ),
        migrations.AddField(
            model_name='order',
            name='shippo_transaction_id',
            field=models.CharField(blank=True, help_text='Goshippo transaction ID for label purchase', max_length=50),
        ),
        migrations.AddField(
            model_name='order',
            name='carrier',
            field=models.CharField(blank=True, help_text='Shipping carrier (e.g., usps, fedex, ups)', max_length=50),
        ),
        migrations.AddField(
            model_name='order',
            name='service_level',
            field=models.CharField(blank=True, help_text='Service level (e.g., Priority, Ground)', max_length=100),
        ),
    ]