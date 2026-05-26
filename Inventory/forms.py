from django import forms
from .models import District_Device_Inventory

class District_Device_Inventory_Form(forms.ModelForm):
	class Meta:
		model= District_Device_Inventory
		fields=['asset_name', 'asset_id', 'serial_number','model_type',
		'current_status','location','department','mac_address',
		'capacity_hard_drive_size','manufacture_make', 'vendor',
		'notes', 'source_of_funding', 'po_order', 'purchase_value',
		

		]
		widgets ={
			'model_type': forms.Select(attrs={
				'class': 'form-control',
				'style' :  'width: 200px; height: 40px',

				}),
			'current_status': forms.Select(attrs={
				'class': 'form-control',
					'style': 'width: 200px;',
		}),
			'notes' : forms.Textarea(attrs={
					'class': 'form-control',
		}),
			'asset_name': forms.Textarea(attrs={
				'class': 'form-control',
				'style':   'width: 200px; height: 40px',
				}),
			'asset_id': forms.Textarea(attrs={
				'class': 'form-control',
				'style':   'width: 200px; height: 40px',

				}),
			'serial_number': forms.Textarea(attrs={
				'class': 'form-control',
				'style':   'width: 200px; height: 40px',
				}),
			'student_id_number_encrypted': forms.TextInput(attrs={
			    'class': 'form-control',
			    'style': 'width: 200px;',
			    
			}),



		}

		labels = {

			'student_id_number_encrypted': "Student ID :"

		}

	def __init__(self, *args, user=None, **kwargs):
		super().__init__(*args, **kwargs)

		# ------------------------------------------------------------------
		# Fix for: InvalidCursorName "_django_curs_..._sync_X" does not exist
		# ------------------------------------------------------------------
		# Each ForeignKey field on a ModelForm becomes a ModelChoiceField,
		# whose .queryset is LAZY. The template renders <option> tags by
		# iterating that queryset, and on Postgres that iteration can use
		# a server-side cursor. If the connection/transaction closes before
		# the template finishes iterating (middleware, CONN_MAX_AGE, etc.),
		# the cursor disappears mid-render and you get InvalidCursorName.
		#
		# Forcing the queryset to a list here evaluates it ONCE, right now,
		# inside the view's normal request flow — no cursor left dangling.
		# The trade-off: we hold all rows in memory for the request. For
		# dropdowns (locations, statuses, models, departments) that's tiny.
		# ------------------------------------------------------------------
		fk_fields = ['model_type', 'current_status', 'location', 'department']
		for name in fk_fields:
			if name in self.fields:
				# list(qs) forces immediate evaluation. After this, iteration
				# in the template hits Python memory, not the DB.
				self.fields[name].queryset = self.fields[name].queryset.all()
				self.fields[name].choices = list(self.fields[name].choices)

		

# class Device_Inventory_Form(forms.ModelForm):
# 	class Meta:
# 		model= 
# 		fields={

# 		}
# 		widgets ={

# 		}

# 	def __init__(self, *args, user=None, **kwargs):
# 		super().__init__(*args, **kwargs)
