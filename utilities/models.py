from django.db import models
from django.conf import settings


class Note(models.Model):
	
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="notes",
		null=True,
		blank=True,
	)
	title = models.CharField(max_length=100)
	body = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.title