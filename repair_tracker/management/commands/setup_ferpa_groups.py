from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from repair_tracker.models import Repair, LongTermLoaner

class Command(BaseCommand):
    help = 'Set up FERPA-compliant user groups'

    def handle(self, *args, **kwargs):
        # Create groups
        tech_group, _ = Group.objects.get_or_create(name='Technicians')
        admin_group, _ = Group.objects.get_or_create(name='IT Administrators')
        readonly_group, _ = Group.objects.get_or_create(name='Read-Only Staff')
        
        # Get content types
        repair_ct = ContentType.objects.get_for_model(Repair)
        loaner_ct = ContentType.objects.get_for_model(LongTermLoaner)
        
        # Technician permissions
        tech_permissions = Permission.objects.filter(
            content_type__in=[repair_ct, loaner_ct],
            codename__in=['add_repair', 'change_repair', 'view_repair',
                         'add_longtermloaner', 'change_longtermloaner', 'view_longtermloaner']
        )
        tech_group.permissions.set(tech_permissions)
        
        # Admin permissions
        admin_permissions = Permission.objects.filter(content_type__in=[repair_ct, loaner_ct])
        admin_group.permissions.set(admin_permissions)
        
        # Read-only permissions
        readonly_permissions = Permission.objects.filter(
            content_type__in=[repair_ct, loaner_ct],
            codename__in=['view_repair', 'view_longtermloaner']
        )
        readonly_group.permissions.set(readonly_permissions)
        
        self.stdout.write(self.style.SUCCESS('Successfully created FERPA groups'))