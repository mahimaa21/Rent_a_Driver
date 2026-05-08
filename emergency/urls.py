from django.urls import path
from . import views

urlpatterns = [
    path("set/", views.set_contact, name="emergency_set"),
    path("get/", views.get_contact, name="emergency_get"),
    path("alert/", views.trigger_alert, name="emergency_alert"),
    path("history/", views.alert_history, name="emergency_history"),
]