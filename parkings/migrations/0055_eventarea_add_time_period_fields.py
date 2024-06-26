# Generated by Django 2.2.15 on 2023-11-17 11:51

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parkings', '0054_eventarea_make_timeend_non_nullable'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventarea',
            name='time_period_days_of_week',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.SmallIntegerField(choices=[(1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'), (4, 'Thursday'), (5, 'Friday'), (6, 'Saturday'), (7, 'Sunday')]), blank=True, default=list, null=True, size=None, verbose_name='time period days of week'),
        ),
        migrations.AddField(
            model_name='eventarea',
            name='time_period_time_end',
            field=models.TimeField(blank=True, db_index=True, null=True, verbose_name='time period end time'),
        ),
        migrations.AddField(
            model_name='eventarea',
            name='time_period_time_start',
            field=models.TimeField(blank=True, db_index=True, null=True, verbose_name='time period start time'),
        ),
    ]
