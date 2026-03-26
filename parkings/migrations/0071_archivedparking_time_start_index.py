from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Re-add an index on ArchivedParking.time_start, which was removed in 0042.
    The field is used both for ORDER BY in the public API and for range filtering
    (time_start__gte / time_start__lte), so the missing index caused full table
    scans on every paginated request.
    """

    dependencies = [
        ("parkings", "0070_alter_permit_subjects_permitcheck"),
    ]

    operations = [
        migrations.AlterField(
            model_name="archivedparking",
            name="time_start",
            field=models.DateTimeField(
                db_index=True, verbose_name="parking start time"
            ),
        ),
    ]
