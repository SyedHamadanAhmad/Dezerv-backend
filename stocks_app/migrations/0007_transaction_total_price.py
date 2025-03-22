# Generated by Django 4.2.3 on 2025-03-21 19:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stocks_app', '0006_delete_portfolio'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='total_price',
            field=models.DecimalField(decimal_places=2, default=0.0, editable=False, max_digits=15),
            preserve_default=False,
        ),
    ]
