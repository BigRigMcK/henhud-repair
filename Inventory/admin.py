from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
#from .models import 
from repair_tracker.audit_models import AuditLog, ConsentRecord
from repair_tracker.csv_export_actions import (
      export_repairs_csv,
      export_loaners_csv,
      export_checkout_history_csv,
      export_audit_log_csv,
  )
# Register your models here.



#@admin.register(Inventory)
