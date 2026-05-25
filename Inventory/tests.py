from django.test import TestCase

# Create your tests here.

from django.test import TestCase
from django.core.exceptions import ValidationError
from Inventory.models import District_Device_Inventory, Device_Model
from Base_Models.models import District_Location, District_Department, Current_Status


class DistrictDeviceInventoryModelTests(TestCase):
    """
    Tests that don't touch HTTP — just the model.
    Fast, reliable, and they catch schema/constraint bugs.
    """

    # def setUp(self):
    #     # setUp runs before EACH test method. It builds a clean slate.
    #     # If you find yourself repeating this in 5 tests, that's the signal
    #     # to put it here.
    #     self.model = Device_Model.objects.create(Model_Type="Chromebook-X1")
    #     self.status = Current_Status.objects.create(Current_Status="Active")
    #     self.location = District_Location.objects.create(
    #         school="HHHS", room="Room 101"
    #     )
    #     self.department = District_Department.objects.create(
    #         department="IT"  # adjust to your actual field name
    #     )

    def test_device_can_be_created_with_minimum_fields(self):
        """A device only needs asset_name to be created."""
        device = District_Device_Inventory.objects.create(
            asset_name="TEST-01",
            asset_id=1001,
            serial_number="SN-0001",
            Current_Status="INSTORAGE",
        )
        self.assertEqual(str(device), "TEST-01")
        self.assertIsNone(device.last_seen_at)  # Should default to None

    # def test_asset_id_must_be_unique(self):
    #     """Two devices can't share an asset_id — DB-level constraint."""
    #     District_Device_Inventory.objects.create(
    #         asset_name="A", asset_id=2001, serial_number="SN-A"
    #     )
    #     with self.assertRaises(Exception):  # IntegrityError, specifically
    #         District_Device_Inventory.objects.create(
    #             asset_name="B", asset_id=2001, serial_number="SN-B"
    #         )

    # def test_audit_representation_includes_asset_and_serial(self):
    #     """The audit log uses this string — make sure it stays meaningful."""
    #     device = District_Device_Inventory.objects.create(
    #         asset_name="LAPTOP-99",
    #         asset_id=3001,
    #         serial_number="SN-99",
    #     )
    #     repr_str = device.get_audit_representation()
    #     self.assertIn("LAPTOP-99", repr_str)
    #     self.assertIn("3001", repr_str)
    #     self.assertIn("SN-99", repr_str)