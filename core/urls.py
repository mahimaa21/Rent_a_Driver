from django.urls import path
from . import views

urlpatterns = [
  # ---------- AUTH (session-based) ----------
  path("register/", views.register_view, name="register"),
  path("login/", views.login_view, name="login"),
  path("logout/", views.logout_view, name="logout"),

  # ---------- DRIVER PROFILE ----------
  path("driver/profile/", views.driver_profile_view, name="driver_profile"),
  path("driver/profile/delete-picture/", views.delete_profile_picture, name="delete_profile_picture"),

  # ---------- RIDE REQUEST ----------
  path("customer/dashboard/", views.customer_dashboard, name="customer_dashboard"),
  path("rides/cancel/<int:ride_request_id>/", views.cancel_ride_request, name="cancel_ride_request"),
  path("rides/edit/<int:ride_request_id>/", views.edit_ride_request, name="edit_ride_request"),
  path("rides/suggest/<int:ride_request_id>/", views.suggest_drivers, name="suggest_drivers"),

  # ---------- BOOKING ----------
  path("booking/create/<int:ride_request_id>/", views.create_booking, name="create_booking"),
  path("bookings/", views.list_my_bookings, name="list_my_bookings"),
  path("booking/<int:booking_id>/status/", views.update_booking_status, name="update_booking_status"),
  path("chat/<int:booking_id>/", views.chat_room, name="chat_room"),

    # ---------- NEARBY FEATURES ----------
  path("drivers/nearby/", views.nearby_drivers, name="nearby_drivers"),  # 🌍 customer → see nearby drivers
  path("driver/nearby/", views.nearby_rides, name="nearby_rides"),
  path("driver/rides/available/", views.list_available_rides, name="list_available_rides"),

  # ---------- REVIEWS ----------
  path("reviews/create/<int:booking_id>/", views.create_review, name="create_review"),
  path("reviews/delete/<int:review_id>/", views.delete_review, name="delete_review"),
  path("reviews/driver/<int:driver_id>/", views.list_driver_reviews, name="list_driver_reviews"),

  # ---------- LEADERBOARD ----------
  path("leaderboard/", views.driver_leaderboard_view, name="leaderboard"),

  # ---------- EMERGENCY ----------
  path("emergency/", views.emergency_view, name="emergency"),
  path("emergency/set/", views.set_emergency_contact, name="set_emergency_contact"),
  path("emergency/delete/", views.delete_emergency_contact, name="delete_emergency_contact"),
  path("emergency/alert/", views.trigger_alert, name="trigger_alert"),

  # ---------- USER LOCATION ----------
  path("user/update-location/", views.update_location, name="update_location"),
]
urlpatterns += [
  path("", views.home_view, name="home"),
  path("driver/dashboard/", views.driver_dashboard, name="driver_dashboard"),
]