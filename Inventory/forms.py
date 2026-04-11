from django import forms
from .models import District_Device_Inventory

class District_Device_Inventory_Form(forms.ModelForm):
	class Meta:
		model= District_Device_Inventory
		fields=['asset_name', 'asset_id', 'serial_number','model_type',
		'current_status','location','department','mac_address',
		'capacity_hard_drive_size','manufacture_make', 'vendor',
		'notes', 'source_of_funding', 'po_order', 'purchase_value',
		'student_id_number',

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



		}

	def __init__(self, *args, user=None, **kwargs):
		super().__init__(*args, **kwargs)

		

# class Device_Inventory_Form(forms.ModelForm):
# 	class Meta:
# 		model= 
# 		fields={

# 		}
# 		widgets ={

# 		}

# 	def __init__(self, *args, user=None, **kwargs):
# 		super().__init__(*args, **kwargs)
