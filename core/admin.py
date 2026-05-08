from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
	Account,
	DriverProfile,
	RideRequest,
	Booking,
	EmergencyContact,
	EmergencyAlert,
	DriverReview,
	ChatMessage,
)


@admin.register(Account)
class AccountAdmin(UserAdmin):
	model = Account
	list_display = ("username", "email", "role", "is_staff", "is_superuser")
	list_filter = ("role", "is_staff", "is_superuser", "is_active")
	search_fields = ("username", "email")
	ordering = ("username",)

	fieldsets = (
		(None, {"fields": ("username", "password")}),
		("Personal info", {"fields": ("first_name", "last_name", "email")}),
		("Roles & permissions", {"fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
		("Important dates", {"fields": ("last_login", "date_joined")}),
		("Location", {"fields": ("last_lat", "last_lng")}),
	)

	add_fieldsets = (
		(
			None,
			{
				"classes": ("wide",),
				"fields": ("username", "email", "role", "password1", "password2", "is_staff", "is_superuser"),
			},
		),
	)


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
	list_display = ("user", "full_name", "license_number", "vehicle_details")
	search_fields = ("user__username", "full_name", "license_number")


@admin.register(RideRequest)
class RideRequestAdmin(admin.ModelAdmin):
	list_display = ("id", "customer", "pickup_location", "dropoff_location", "status", "created_at")
	list_filter = ("status",)
	search_fields = ("customer__username", "pickup_location", "dropoff_location")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
	list_display = ("id", "ride_request", "driver", "status", "confirmed_at")
	list_filter = ("status",)
	search_fields = ("driver__username", "ride_request__customer__username")


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
	list_display = ("user", "phone_number", "created_at")
	search_fields = ("user__username", "phone_number")


@admin.register(EmergencyAlert)
class EmergencyAlertAdmin(admin.ModelAdmin):
	list_display = ("user", "contact", "status", "triggered_at")
	list_filter = ("status",)
	search_fields = ("user__username", "contact__phone_number")


@admin.register(DriverReview)
class DriverReviewAdmin(admin.ModelAdmin):
	list_display = ("booking", "driver", "customer", "rating", "created_at")
	list_filter = ("rating",)
	search_fields = ("driver__username", "customer__username")


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
	list_display = ("booking", "sender", "text", "created_at")
	search_fields = ("booking__id", "sender__username", "text")