from django.db import models




class Current_Status(models.Model):
	Status= models.CharField(max_length=50)
	class Meta:
		verbose_name_plural = "Device Statuses"

	def __str__(self):
		return f"{self.Status}"