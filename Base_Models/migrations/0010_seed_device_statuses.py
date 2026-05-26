"""
Data migration: seed the Current_Device_Status lookup table.

Why a migration instead of a fixture or admin clicks:
- Runs automatically as part of `manage.py migrate`.
- Every environment (your laptop, staging, prod, CI, a new dev) ends up
  with the same statuses without anyone remembering a manual step.
- Idempotent: get_or_create means rerunning does nothing harmful.
- Reversible: the reverse_code lets `migrate Base_Models <previous>`
  roll the data back cleanly.
"""
from django.db import migrations


# The authoritative list. Change THIS to add/remove statuses for everyone.
DEVICE_STATUSES = [
    "Assign Device Status",
    "In Use",
    "In Storage",
    "Missing",
    "Being Repaired",
    "Disposed-End of Life",
    "Lost/Stolen-Pending Payment",
    "Lost/Stolen-Paid",
]

# Old placeholder rows we want to clean out.
STALE_STATUSES = [

]



def seed_statuses(apps, schema_editor):
    """
    Forward: remove placeholders, then insert each real status.

    Note we use apps.get_model() instead of `from Base_Models.models import ...`.
    This is critical in migrations: it gives you a historical version of the
    model frozen at this migration's point in time. If you import the real
    class and someone later renames a field, old migrations will break.
    """
    Current_Device_Status = apps.get_model("Base_Models", "Current_Device_Status")

    Current_Device_Status.objects.filter(Status__in=STALE_STATUSES).delete()

    for label in DEVICE_STATUSES:
        # get_or_create makes this safe to re-run. If the row already
        # exists, it's left alone; if not, it's created.
        Current_Device_Status.objects.get_or_create(Status=label)


def unseed_statuses(apps, schema_editor):
    """
    Reverse: remove the rows this migration added.
    Used when running `migrate Base_Models 0007` (roll back to previous).
    """
    Current_Device_Status = apps.get_model("Base_Models", "Current_Device_Status")
    Current_Device_Status.objects.filter(Status__in=DEVICE_STATUSES).delete()


class Migration(migrations.Migration):

    dependencies = [
        # IMPORTANT: replace "0007_alter_current_device_status_status"
        # with the actual filename (minus .py) of the migration that
        # makemigrations just generated in step 1.
        ("Base_Models", "0009_alter_current_device_status_status"),
    ]

    operations = [
        migrations.RunPython(seed_statuses, reverse_code=unseed_statuses),
    ]