# HenHud-Repair








Generate your own Keys:

Paste :  " python3 -c "import secrets; print(secrets.token_hex(32))" "  ( n*2=x / 32bytes=64charachers)


from Base_Models.models import District_Department
District_Department.objects.get_or_create(id=1, defaults={'department': 'Staff Loaned Devices'})
District_Department.objects.get_or_create(id=2, defaults={'department': 'Student Loaned Devices'})
District_Department.objects.get_or_create(id=3, defaults={'department': 'Classroom Loaner Devices'})
District_Department.objects.get_or_create(id=4, defaults={'department': 'HHHS Long Term Loaner Devices'})
District_Department.objects.get_or_create(id=5, defaults={'department': 'BMMS Long Term Loaner Devices'})


psql -U postgres -d repair_tracker_db