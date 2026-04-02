from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import District_Location, District_Department,District_Device_Inventory, Asset_History
from repair_tracker.audit_models import AuditLog, ConsentRecord
from repair_tracker.csv_export_actions import (
      export_repairs_csv,
      export_loaners_csv,
      export_checkout_history_csv,
      export_audit_log_csv,
  )
# Register your models here.



@admin.register(District_Device_Inventory)
class District_Device_InventoryAdmin(admin.ModelAdmin):
      list_display = [
      'asset_name',
      'asset_id',
      'serial_number',
      ]



      def save_model(self, request, obj, form, change):
            if not change:
                  obj.created_by = request.user
                  action = 'CREATE'
            else:
                  action = 'UPDATE'

                  changes = {}
            if change:
                  for field in form.changed_data:
                      changes[field] = {
                          'old': str(form.initial.get(field, '')),
                          'new': str(form.cleaned_data.get(field, ''))
                      }

            super().save_model(request, obj, form, change)

            # Log the action
            AuditLog.objects.create(
            user=request.user,
            username=request.user.username,
            action=action,
            content_object=obj,
            object_repr=obj.get_audit_representation(),
            changes=changes if changes else None,
            )