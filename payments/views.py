from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect

from core.models import Booking
from .models import Payment


def _unpaid_bookings_for(user):
    """
    Return Booking queryset for a customer that are accepted/completed
    but have no Payment record yet.
    Avoids cross-app reverse-relation JOIN by fetching paid IDs separately.
    """
    paid_ids = set(
        Payment.objects.filter(
            booking__ride_request__customer=user
        ).values_list('booking_id', flat=True)
    )
    return (
        Booking.objects.filter(
            ride_request__customer=user,
            status__in=['ongoing', 'completed'],
        )
        .exclude(id__in=paid_ids)
        .select_related('ride_request', 'driver', 'driver__driverprofile')
        .order_by('-confirmed_at')
    )


@login_required
def payments(request):
    if request.user.role != 'customer':
        return HttpResponseForbidden("Only customers can access payments.")

    pending_bookings = _unpaid_bookings_for(request.user)

    paid_payments = (
        Payment.objects.filter(booking__ride_request__customer=request.user)
        .select_related(
            'booking', 'booking__ride_request',
            'booking__driver', 'booking__driver__driverprofile',
        )
        .order_by('-paid_at')
    )

    return render(request, 'payments.html', {
        'bookings': pending_bookings,
        'paid_payments': paid_payments,
    })


@login_required
def pay_ride(request, booking_id):
    if request.user.role != 'customer':
        return HttpResponseForbidden("Only customers can pay.")

    # Make sure this booking belongs to the customer and has no payment yet
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        ride_request__customer=request.user,
        status__in=['ongoing', 'completed'],
    )

    # Block if already paid
    if Payment.objects.filter(booking=booking).exists():
        messages.error(request, 'This ride has already been paid.')
        return redirect('payments:payments')

    if request.method == 'POST':
        method = request.POST.get('method')
        account_number = (request.POST.get('account_number') or '').strip()
        amount_raw = (request.POST.get('amount') or '').strip()

        if method not in ('bkash', 'nagad', 'bank'):
            messages.error(request, 'Please select a valid payment method.')
            return redirect('payments:payments')
        if not account_number:
            messages.error(request, 'Please enter your account number.')
            return redirect('payments:payments')
        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messages.error(request, 'Please enter a valid amount.')
            return redirect('payments:payments')

        Payment.objects.create(
            booking=booking,
            method=method,
            account_number=account_number,
            amount=amount,
        )
        booking.status = 'completed'
        booking.save()
        booking.ride_request.status = 'completed'
        booking.ride_request.save()

        label = {'bkash': 'bKash', 'nagad': 'Nagad', 'bank': 'Bank Transfer'}[method]
        messages.success(request, f'Payment of ৳{amount:.2f} via {label} was successful!')

    return redirect('payments:payments')


@login_required
def driver_payment_history(request):
    if request.user.role != 'driver':
        return HttpResponseForbidden("Only drivers can view this page.")
    bookings = (
        Booking.objects.filter(driver=request.user)
        .select_related('ride_request', 'ride_request__customer')
        .prefetch_related('payment')
        .order_by('-confirmed_at')
    )
    
    # Calculate stats
    total_rides = bookings.count()
    paid_rides = sum(1 for b in bookings if hasattr(b, 'payment'))
    unpaid_rides = total_rides - paid_rides
    total_earnings = sum(b.payment.amount for b in bookings if hasattr(b, 'payment'))
    
    return render(request, 'driver_payment_history.html', {
        'bookings': bookings,
        'total_rides': total_rides,
        'paid_rides': paid_rides,
        'unpaid_rides': unpaid_rides,
        'total_earnings': total_earnings,
    })


@login_required
def transaction_history(request):
    """Dedicated page for customer transaction history."""
    if request.user.role != 'customer':
        return HttpResponseForbidden("Only customers can access transaction history.")

    paid_payments = (
        Payment.objects.filter(booking__ride_request__customer=request.user)
        .select_related(
            'booking', 'booking__ride_request',
            'booking__driver', 'booking__driver__driverprofile',
        )
        .order_by('-paid_at')
    )

    return render(request, 'transaction_history.html', {
        'paid_payments': paid_payments,
    })