from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.payments, name='payments'),
    path('pay/<int:booking_id>/', views.pay_ride, name='pay_ride'),
    path('transactions/', views.transaction_history, name='transaction_history'),
    path('driver/history/', views.driver_payment_history, name='driver_history'),
]
