"""
Seed script for test data.

Usage:
    python manage.py seed_test_data
    python manage.py seed_test_data --clear   # wipe existing seed data first

Place this file at:
    Inventory/management/commands/seed_test_data.py

Also create empty __init__.py files at:
    Inventory/management/__init__.py
    Inventory/management/commands/__init__.py
"""

from django.core.management.base import BaseCommand
from django.conf import settings

# ── Models ────────────────────────────────────────────────────────────────────
from Base_Models.models import District_Location, District_Department, Current_Status
from Inventory.models import District_Device_Inventory, Device_Model
from District_Member_Information.models import District_Member


# ── Seed constants ────────────────────────────────────────────────────────────

# 5 buildings × 2 rooms = 10 locations
LOCATIONS = [
    ("HHHS", "Room 101"),
    ("HHHS", "Room 102"),
    ("BMMS", "Room 201"),
    ("BMMS", "Room 202"),
    ("BV",   "Room 101"),
    ("BV",   "Room 102"),
    ("FGL",  "Room 101"),
    ("FGL",  "Room 102"),
    ("FW",   "Room 101"),
    ("FW",   "Room 102"),
]

# Prerequisites (created if missing)
DEPARTMENT_NAME  = "Test Department"
STATUS_NAME      = "Active"
MODEL_TYPE       = "Test-Model-X1"

# 20 test devices
DEVICE_TEMPLATE = [
    {
        "asset_name":   f"TEST-DEVICE-{str(i).zfill(2)}",
        "asset_id":     9000 + i,
        "serial_number": f"SN-TEST-{str(i).zfill(4)}",
        "vendor":       "Test Vendor",
        "manufacture_make": "TestMake",
        "source_of_funding": "Test Fund",
    }
    for i in range(1, 21)
]

# 5 district members
MEMBERS = [
    {
        "district_member_id":    "TST-001",
        "district_member_name":  "Doe, John",
        "district_member_email": "jdoe@test.district.org",
        "district_member_grade": "9",
        "district_member_building": "HHHS",
    },
    {
        "district_member_id":    "TST-002",
        "district_member_name":  "Smith, Jane",
        "district_member_email": "jsmith@test.district.org",
        "district_member_grade": "10",
        "district_member_building": "HHHS",
    },
    {
        "district_member_id":    "TST-003",
        "district_member_name":  "Garcia, Maria",
        "district_member_email": "mgarcia@test.district.org",
        "district_member_grade": "STAFF",
        "district_member_building": "BMMS",
    },
    {
        "district_member_id":    "TST-004",
        "district_member_name":  "Johnson, Alex",
        "district_member_email": "ajohnson@test.district.org",
        "district_member_grade": "7",
        "district_member_building": "BMMS",
    },
    {
        "district_member_id":    "TST-005",
        "district_member_name":  "Williams, Sam",
        "district_member_email": "swilliams@test.district.org",
        "district_member_grade": "STAFF",
        "district_member_building": "DO",
    },
]


class Command(BaseCommand):
    help = "Seeds the database with 5 District Members, 20 Test Devices, and 10 Locations (2 per building)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing seed data before inserting.",
        )

    # ── Main entry ────────────────────────────────────────────────────────────

    def handle(self, *args, **options):
        if options["clear"]:
            self._clear_seed_data()

        self.stdout.write(self.style.MIGRATE_HEADING("\n── Step 1: Locations ──"))
        locations = self._seed_locations()

        self.stdout.write(self.style.MIGRATE_HEADING("\n── Step 2: Prerequisites ──"))
        department, status, model = self._seed_prerequisites()

        self.stdout.write(self.style.MIGRATE_HEADING("\n── Step 3: Devices ──"))
        self._seed_devices(locations, department, status, model)

        self.stdout.write(self.style.MIGRATE_HEADING("\n── Step 4: District Members ──"))
        self._seed_members()

        self.stdout.write(self.style.SUCCESS("\n✅  Seed complete.\n"))

    # ── Clear ─────────────────────────────────────────────────────────────────

    def _clear_seed_data(self):
        self.stdout.write(self.style.WARNING("Clearing existing seed data…"))

        deleted, _ = District_Device_Inventory.objects.filter(
            asset_name__startswith="TEST-DEVICE-"
        ).delete()
        self.stdout.write(f"  Deleted {deleted} test devices.")

        for school, room in LOCATIONS:
            District_Location.objects.filter(school=school, room=room).delete()
        self.stdout.write(f"  Deleted up to {len(LOCATIONS)} test locations.")

        for m in MEMBERS:
            # Use the search index to find & delete — avoids decrypting all rows
            District_Member.objects.filter(
                district_member_id_index=self._hash_id(m["district_member_id"])
            ).delete()
        self.stdout.write(f"  Deleted up to {len(MEMBERS)} test members.")

    # ── Locations ─────────────────────────────────────────────────────────────

    def _seed_locations(self):
        created_locations = []
        for school, room in LOCATIONS:
            obj, created = District_Location.objects.get_or_create(
                school=school, room=room
            )
            status = "CREATED" if created else "exists"
            self.stdout.write(f"  [{status}] {obj}")
            created_locations.append(obj)
        return created_locations

    # ── Prerequisites ─────────────────────────────────────────────────────────

    def _seed_prerequisites(self):
        dept, created = District_Department.objects.get_or_create(department=DEPARTMENT_NAME)
        self.stdout.write(f"  Department  → {'CREATED' if created else 'exists'}: {dept}")

        status, created = Current_Status.objects.get_or_create(Status=STATUS_NAME)
        self.stdout.write(f"  Status      → {'CREATED' if created else 'exists'}: {status}")

        model, created = Device_Model.objects.get_or_create(Model_Type=MODEL_TYPE)
        self.stdout.write(f"  Device Model→ {'CREATED' if created else 'exists'}: {model}")

        return dept, status, model

    # ── Devices ───────────────────────────────────────────────────────────────

    def _seed_devices(self, locations, department, status, model):
        for i, data in enumerate(DEVICE_TEMPLATE):
            # Assign locations round-robin across the 10 locations
            location = locations[i % len(locations)]

            obj, created = District_Device_Inventory.objects.get_or_create(
                asset_id=data["asset_id"],
                defaults={
                    **data,
                    "location":       location,
                    "department":     department,
                    "current_status": status,
                    "model_type":     model,
                },
            )
            action = "CREATED" if created else "exists"
            self.stdout.write(f"  [{action}] {obj.asset_name} → {location}")

    # ── Members ───────────────────────────────────────────────────────────────

    def _seed_members(self):
        """
        District_Member uses encrypted + SearchField columns.
        We look up existing records via the hashed index, then create if missing.
        """
        for data in MEMBERS:
            hashed_id = self._hash_id(data["district_member_id"])

            existing = District_Member.objects.filter(
                district_member_id_index=hashed_id
            ).first()

            if existing:
                self.stdout.write(f"  [exists]   Member {data['district_member_id']}")
                continue

            member = District_Member(
                district_member_grade=data["district_member_grade"],
                district_member_building=data["district_member_building"],
            )
            # Assign encrypted fields directly — the library handles encryption on save
            member.district_member_id    = data["district_member_id"]
            member.district_member_name  = data["district_member_name"]
            member.district_member_email = data["district_member_email"]
            member.save()

            self.stdout.write(
                f"  [CREATED]  Member {data['district_member_id']} "
                f"(pk={member.pk}) → {data['district_member_building']}"
            )

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _hash_id(value: str) -> str:
        """
        Reproduces the hash stored by django-searchable-encrypted-fields SearchField.
        Format: "xx" + sha256( (value + hash_key).encode() ).hexdigest()
        """
        import hashlib
        hash_key = settings.SEARCH_D_M_ID_HASH_KEY
        raw = str(value) + hash_key
        return "xx" + hashlib.sha256(raw.encode()).hexdigest()