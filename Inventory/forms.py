from django import forms
from .models import District_Device_Inventory

# class Device_Inventory_Form(fomrs.ModelForm):
# 	class Meta:
# 		model:
# 		fields={

# 		}
# 		widgets ={

# 		}

# 	def __init__(self, *args, user=None, **kwargs):
# 		super().__init__(*args, **kwargs)

		

class Device_Inventory_Form(fomrs.ModelForm):
	class Meta:
		model:
		fields={

		}
		widgets ={

		}

	def __init__(self, *args, user=None, **kwargs):
		super().__init__(*args, **kwargs)

