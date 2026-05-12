from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.payments, name='payments'),
    path('pay/<int:booking_id>/', views.pay_ride, name='pay_ride'),
    path('driver/history/', views.driver_payment_history, name='driver_history'),
]
