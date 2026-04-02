from django.db import models




class Current_Status(models.Model):
	Status= models.CharField(max_length=50)


	def __str__(self):
		return f"{self.Status}"