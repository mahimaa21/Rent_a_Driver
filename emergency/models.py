from django.db import models
from django.conf import settings


class EmergencyContact(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
	phone_number = models.CharField(max_length=20)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = "core_emergencycontact"  
		managed = False  

	def __str__(self):
		return f"{self.user.username} - {self.phone_number}"


class EmergencyAlert(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
	contact = models.ForeignKey(EmergencyContact, on_delete=models.CASCADE)
	triggered_at = models.DateTimeField(auto_now_add=True)
	status = models.CharField(max_length=20, choices=[("sent", "Sent"), ("failed", "Failed")], default="sent")

	class Meta:
		db_table = "core_emergencyalert"  
		managed = False

	def __str__(self):
		return f"Alert by {self.user.username} to {self.contact.phone_number} at {self.triggered_at}"