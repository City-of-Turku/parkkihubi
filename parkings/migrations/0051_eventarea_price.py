# Generated by Django 2.2.15 on 2023-11-13 13:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parkings', '0050_eventarea_rename_event_start_and_event_end_to_time_start_and_time_end'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventarea',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
    ]