
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# Custom User Model
class Account(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('driver', 'Driver'),
    )
    role = models.CharField(max_length=15, choices=ROLE_CHOICES)
    #for location
    last_lat = models.FloatField(null=True, blank=True)
    last_lng = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"



# Driver Profile
class DriverProfile(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, null=True, blank=True)
    license_number = models.CharField(max_length=50)

     # DriverProfile class e add koro:
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    
    vehicle_details = models.CharField(max_length=100, default="Unknown")  
    address = models.CharField(max_length=200, null=True, blank=True)
    nid_number = models.CharField(max_length=50, null=True, blank=True)
    profile_picture = models.ImageField(upload_to="profiles/", null=True, blank=True)

    current_lat = models.FloatField(null=True, blank=True)
    current_lng = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.user.username


# Ride Request
class RideRequest(models.Model):
    customer = models.ForeignKey(Account, on_delete=models.CASCADE)
    pickup_location = models.CharField(max_length=200)
    dropoff_location = models.CharField(max_length=200)
    pickup_lat = models.FloatField(null=True, blank=True)
    pickup_lng = models.FloatField(null=True, blank=True)
    dropoff_lat = models.FloatField(null=True, blank=True)
    dropoff_lng = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True) 
   
    def __str__(self):
        return f"Ride by {self.customer.username}"


# Booking
class Booking(models.Model):
    ride_request = models.OneToOneField(RideRequest, on_delete=models.CASCADE, related_name="booking")
    driver = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="bookings")
    confirmed_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[('ongoing', 'Ongoing'), ('completed', 'Completed'), ('cancelled', 'Cancelled')],
        default='ongoing'
    )

    def __str__(self):
        return f"Booking {self.id} - {self.ride_request.customer.username} with {self.driver.username}"


# Emergency Contact
class EmergencyContact(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="emergency_contact")
    phone_number = models.CharField(max_length=20) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.phone_number}"


# Emergency Alert
class EmergencyAlert(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alerts")
    contact = models.ForeignKey(EmergencyContact, on_delete=models.CASCADE)
    triggered_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[("sent", "Sent"), ("failed", "Failed")],
        default="sent"
    )

    def __str__(self):
        return f"Alert by {self.user.username} to {self.contact.phone_number} at {self.triggered_at}"

# Driver Review
class DriverReview(models.Model):
    booking = models.OneToOneField("Booking", on_delete=models.CASCADE, related_name="review")
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="driver_reviews")
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_reviews")
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])  
    feedback = models.TextField(blank=True)
    image = models.ImageField(upload_to="reviews/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.username} → {self.driver.username} ({self.rating}⭐)"


# Chat Message
class ChatMessage(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender.username}: {self.text[:20]}..."