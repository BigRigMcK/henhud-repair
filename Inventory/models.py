# from django.db import models
# from repair_tracker.models import Device_Model
# # Create your models here.
# class District_Location(models.Model):
# 	School=CharField
# 	Room=CharField
# class District_Department(models.Model):
# 		Department=CharField()
# class District_Device_Inventory(models.Model):
# 		Asset Name=CharField(max_lenth=50, null=False, blank=False)
#     	Asset_ID=IntegerField(max_lenth=10)
#     	Serial_Number=CharField(max_lenth=30, null=True, blank=True)
#     	Current_Status=ForeignKey(Device_Model)
#     	Location=ForeignKey(District_Location)
#     	Department=ForeignKey(District_Department)
#     	Current_Asset_Type=ForeignKey(Device_Model)
#     	Asset_History=(Own Model - Audit must be available for Changes Made)
#     	Capacity_Hard Drive_Size=(CharField)
#     	MAC Address=(CharField)
#     	Manufacture_Make=(CharField)
#     	Model_type=(CharField)
#    		Vendor=(CharField)
#     	Notes=(TextField)
#     	Source_of_Funding=(CharField)
#     	PO_Order=(CharField)
#     	Purchase Value (CharField) (default="$")

