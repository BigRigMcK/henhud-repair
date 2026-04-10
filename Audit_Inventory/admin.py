from django.contrib import admin
from django.utils import timezone
from repair_tracker.audit_models import AuditLog
from .models import District_Device_Audit, Individual_AuditDevice
# Register your models here.
@admin.register(District_Device_Audit)
class District_Device_AuditAdmin(admin.ModelAdmin):

	list_display = ['audit_date','location','auditor',]
	list_filter = ['audit_date','location','auditor']
	search_fields = ['audit_date','location','auditor']
	readonly_fields = ('audit_date','devices')
	

	fieldsets = (
	    ('Asset Identification', {
	        'fields': ('auditor','devices',),
	    }),
	    ('Location & Department', {
	        'fields': ('location',),
	    }),
	    
	    ('Notes', {
	        'fields': ('notes',),
	    }),
	)



	def save_model(self, request, obj, form, change):
	    action = 'UPDATE' if change else 'CREATE'
	    changes = {}

	    if change:
	        for field in form.changed_data:
	            changes[field] = {
	                'old': str(form.initial.get(field, '')),
	                'new': str(form.cleaned_data.get(field, '')),
	            }

	    super().save_model(request, obj, form, change)

	    # Primary AuditLog entry
	    _audit(request, action, obj, changes if changes else None)

	    # Double-log: also write to Asset_History
	    change_summary = (
	        'Updated fields: ' + ', '.join(changes.keys())
	        if changes
	        else 'Record created'
	    )
	    Asset_History.objects.create(
	        asset=obj,
	        description=f'[AuditLog mirror] {change_summary}',
	        changed_by=request.user.username,
	    )

	def delete_model(self, request, obj):
	    _audit(request, 'DELETE', obj, {'deleted': str(obj)})
	    # Asset_History cascades on delete so no separate entry needed
	    super().delete_model(request, obj)

	def delete_queryset(self, request, queryset):
	    for obj in queryset:
	        _audit(request, 'DELETE', obj, {'deleted': str(obj)})
	    super().delete_queryset(request, queryset)



@admin.register(Individual_AuditDevice)
class Individual_AuditDevice_Admin(admin.ModelAdmin):
	#'audit','device','found','notes','found_at'

	#
	list_display = ['audit','device','found','notes','found_at']
	list_filter = ['audit','device','found','found_at']
	search_fields = ['audit','device','found','found_at']

	
	fieldsets = (
	    ('Asset Identification', {
	        'fields': ('audit','found','found_at',),
	    }),
	    ('Notes', {
	        'fields': ('notes',),
	    }),
	)

	def save_model(self, request, obj, form, change):
	    action = 'UPDATE' if change else 'CREATE'
	    changes = {}

	    if change:
	        for field in form.changed_data:
	            changes[field] = {
	                'old': str(form.initial.get(field, '')),
	                'new': str(form.cleaned_data.get(field, '')),
	            }

	    super().save_model(request, obj, form, change)

	    # Primary AuditLog entry
	    _audit(request, action, obj, changes if changes else None)

	    # Double-log: also write to Asset_History
	    change_summary = (
	        'Updated fields: ' + ', '.join(changes.keys())
	        if changes
	        else 'Record created'
	    )
	    Asset_History.objects.create(
	        asset=obj,
	        description=f'[AuditLog mirror] {change_summary}',
	        changed_by=request.user.username,
	    )

	def delete_model(self, request, obj):
	    _audit(request, 'DELETE', obj, {'deleted': str(obj)})
	    # Asset_History cascades on delete so no separate entry needed
	    super().delete_model(request, obj)

	def delete_queryset(self, request, queryset):
	    for obj in queryset:
	        _audit(request, 'DELETE', obj, {'deleted': str(obj)})
	    super().delete_queryset(request, queryset)