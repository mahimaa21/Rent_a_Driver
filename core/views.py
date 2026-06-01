from django.contrib import messages
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db.models import Count, Avg, Q
from django.db import transaction, IntegrityError
import logging
from math import radians, sin, cos, sqrt, atan2
from urllib.parse import urlencode
from urllib.request import urlopen, Request
import json

from urllib3 import request

from .models import (
    Account,
    DriverProfile,
    RideRequest,
    Booking,
    EmergencyContact,
    EmergencyAlert,
    DriverReview,
    ChatMessage,
    Notification,
)
from .models import Account


def calculate_distance(lat1, lon1, lat2, lon2):
    """Return distance in kilometers between two lat/lng points."""
    if None in [lat1, lon1, lat2, lon2]:
        return None
    R = 6371  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def geocode_address(address: str):
    try:
        if not address:
            return None, None
        params = {
            "q": address,
            "format": "json",
            "limit": 1,
        }
        url = "https://nominatim.openstreetmap.org/search?" + urlencode(params)
        req = Request(url, headers={
            "User-Agent": "RentADriver/1.0 (education; contact: example@example.com)",
        })
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list) and data:
                lat = float(data[0].get("lat"))
                lon = float(data[0].get("lon"))
                return lat, lon
    except Exception:
        pass
    return None, None


def home_view(request):
    return render(request, "index.html")


def register_view(request):
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = (request.POST.get("password") or "").strip()
        role = request.POST.get("role")
        if not username or not password or role not in ["customer", "driver"]:
            messages.error(request, "Please fill all fields correctly.")
            return redirect("register")
        if Account.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("register")
        user = Account.objects.create_user(username=username, password=password, role=role)
        login(request, user)
        messages.success(request, "Registration successful!")
        # If driver, require profile completion first
        if role == "driver":
            return redirect("driver_profile")
        return redirect("customer_dashboard")
    return render(request, "register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, "Logged in successfully.")
            return redirect("driver_dashboard" if user.role == "driver" else "customer_dashboard")
        messages.error(request, "Invalid credentials.")
        return redirect("login")
    return render(request, "login.html")


def logout_view(request):
    logout(request)
    messages.info(request, "Logged out.")
    return redirect("home")

# DRIVER PROFILE 
@login_required
def driver_profile_view(request):
    if request.user.role != "driver":
        return HttpResponseForbidden("Only drivers can create a profile")
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        license_number = request.POST.get("license")
        # POST block e add koro (license_number er pashe):
        phone_number = request.POST.get("phone_number")
        vehicle_details = request.POST.get("vehicle")
        nid_number = request.POST.get("nid_number")
        address = request.POST.get("address")
        profile_picture = request.FILES.get("profile_picture")
        lat = request.POST.get("lat")
        lng = request.POST.get("lng")
        profile, _ = DriverProfile.objects.get_or_create(user=request.user)
        if full_name:
            profile.full_name = full_name
        profile.license_number = license_number
        profile.vehicle_details = vehicle_details
        if nid_number:
            profile.nid_number = nid_number
        if address is not None:
            profile.address = address
        if phone_number:
            profile.phone_number = phone_number
        if profile_picture:
            profile.profile_picture = profile_picture
       # Jodi latitude ar longitude deya thake tahole oigulo use hobe.Ar jodi na thake, tahole deya address theke location ber kora hobe.
        lat_val = float(lat) if lat else None
        lng_val = float(lng) if lng else None

        if lat_val is None or lng_val is None:
            # Jodi address deya thake tahole sei address diye coordinates ber korar try kore"
            if address:
                g_lat, g_lng = geocode_address(address)
                if lat_val is None:
                    lat_val = g_lat
                if lng_val is None:
                    lng_val = g_lng
                if g_lat is None or g_lng is None:
                    messages.info(request, "Could not determine coordinates from address; you can use 'Use my location' or enter coordinates manually.")

        profile.current_lat = lat_val
        profile.current_lng = lng_val
        profile.save()
        messages.success(request, "Profile saved.")
        return redirect("driver_dashboard")
    try:
        profile = DriverProfile.objects.get(user=request.user)
    except DriverProfile.DoesNotExist:
        profile = None
    return render(request, "driver_profile.html", {"profile": profile})


@login_required
def delete_profile_picture(request):
    if request.user.role != "driver":
        return HttpResponseForbidden("Only drivers can modify a driver profile")
    if request.method != "POST":
        return redirect("driver_profile")
    try:
        profile = DriverProfile.objects.get(user=request.user)
        if profile.profile_picture:
            profile.profile_picture.delete(save=False)
            profile.profile_picture = None
            profile.save(update_fields=["profile_picture"])
            messages.info(request, "Profile picture removed.")
        else:
            messages.info(request, "No profile picture to remove.")
    except DriverProfile.DoesNotExist:
        messages.error(request, "Profile not found.")
    return redirect("driver_profile")


# RIDE REQUEST

@login_required
def create_ride_request_view(request):
    """Dedicated page for creating a new ride request."""
    if request.user.role != "customer":
        return redirect("driver_dashboard")
    if request.method == "POST":
        pickup = request.POST.get("pickup")
        dropoff = request.POST.get("dropoff")
        car = request.POST.get("carName")
        RideRequest.objects.create(
            customer=request.user,
            pickup_location=pickup,
            dropoff_location=dropoff,
        )
        messages.success(request, "Ride request created successfully!")
        return redirect("customer_dashboard")
    return render(request, "create_ride_request.html")


@login_required
def all_ride_requests_view(request):
    """Dedicated page showing all ride requests for the customer."""
    if request.user.role != "customer":
        return redirect("driver_dashboard")
    rides = RideRequest.objects.filter(customer=request.user).order_by("-created_at")
    customer_bookings = Booking.objects.filter(ride_request__customer=request.user).order_by("-confirmed_at")
    
    # Get accepted ride info
    accepted_ride_info = None
    for ride in rides:
        if ride.status == "accepted":
            try:
                booking = ride.booking
                driver_profile = DriverProfile.objects.get(user=booking.driver)
                accepted_ride_info = {
                    "ride": ride,
                    "driver_name": driver_profile.full_name or booking.driver.username,
                    "driver_phone": driver_profile.phone_number,
                    "driver_picture": driver_profile.profile_picture,
                    "driver_lat": driver_profile.current_lat,
                    "driver_lng": driver_profile.current_lng,
                }
                break
            except:
                pass
    
    return render(request, "all_ride_requests.html", {
        "rides": rides,
        "customer_bookings": customer_bookings,
        "accepted_ride_info": accepted_ride_info,
    })


@login_required
def all_reviews_view(request):
    """Dedicated page showing all reviews for the customer."""
    if request.user.role != "customer":
        return redirect("driver_dashboard")
    customer_bookings = Booking.objects.filter(
        ride_request__customer=request.user,
        status='completed'
    ).order_by("-confirmed_at")
    
    return render(request, "all_reviews.html", {
        "customer_bookings": customer_bookings,
    })


@login_required
def customer_dashboard(request):
    if request.user.role != "customer":
        return redirect("driver_dashboard")
    rides = RideRequest.objects.filter(customer=request.user).order_by("-created_at")
    customer_bookings = Booking.objects.filter(ride_request__customer=request.user).order_by("-confirmed_at")

    # rides query er niche add koro:

    accepted_ride_info = None
    for ride in rides:
        if ride.status == "accepted":
            try:
                booking = ride.booking
                driver_profile = DriverProfile.objects.get(user=booking.driver)
                accepted_ride_info = {
                    "ride": ride,
                    "driver_name": driver_profile.full_name or booking.driver.username,
                    "driver_phone": driver_profile.phone_number,
                    "driver_picture": driver_profile.profile_picture,
                    "driver_lat": driver_profile.current_lat,
                    "driver_lng": driver_profile.current_lng,
                }
            except:
                pass

    # Build nearby drivers list based on customer's last known location
    nearby_list = []
    lat0 = request.user.last_lat
    lng0 = request.user.last_lng
    drivers = DriverProfile.objects.select_related("user").all()
    for d in drivers:
        if d.current_lat is None or d.current_lng is None:
            continue
        dist = None
        if lat0 is not None and lng0 is not None:
            dist = calculate_distance(lat0, lng0, d.current_lat, d.current_lng)
        nearby_list.append({
            "user": d.user,
            "vehicle_details": d.vehicle_details,
            "distance_km": round(dist, 2) if dist is not None else None,
        })

    # Jodi distance thake tahole distance er upor vitti kore sort kore ar  10 km er vitore ja ase oigula filter kore"
    if any(item["distance_km"] is not None for item in nearby_list):
        filtered = [item for item in nearby_list if item["distance_km"] is not None and item["distance_km"] <= 10]
        if not filtered:
            filtered = [item for item in nearby_list if item["distance_km"] is not None]
        filtered.sort(key=lambda x: x["distance_km"])
        nearby_list = filtered[:10]
    else:
        # kono location nai
        nearby_list = nearby_list[:10]

    return render(request, "customer_dashboard.html", {
        "rides": rides,
        "nearby_drivers": nearby_list,
        "customer_bookings": customer_bookings,
        "accepted_ride_info": accepted_ride_info,
    })


# BOOKING 

@login_required
def create_booking(request, ride_request_id):
    if request.user.role != "driver":
        return HttpResponseForbidden("Only drivers can accept bookings")
    ride = get_object_or_404(RideRequest, id=ride_request_id, status="pending")
    ride.status = "accepted"
    ride.save()
    booking = Booking.objects.create(ride_request=ride, driver=request.user)
    
    # Create notification for customer
    create_notification(
        user=ride.customer,
        notification_type='ride_accepted',
        title='🚗 Ride Accepted!',
        message=f'Driver {request.user.username} has accepted your ride request from {ride.pickup_location} to {ride.dropoff_location}.',
        ride_request=ride
    )
    
    messages.success(request, "Booking created.")
    return redirect("driver_dashboard")


@login_required
def list_my_bookings(request):
    if request.user.role == "driver":
        bookings = Booking.objects.filter(driver=request.user)
    else:
        bookings = Booking.objects.filter(ride_request__customer=request.user)
    return render(request, "driver_dashboard.html", {"bookings": bookings})


@login_required
def update_booking_status(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, driver=request.user)
    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in ["completed", "cancelled"]:
            booking.status = new_status
            booking.save()
            booking.ride_request.status = ("completed" if new_status == "completed" else "cancelled")
            booking.ride_request.save()
            
            # Create notification for customer
            if new_status == "completed":
                create_notification(
                    user=booking.ride_request.customer,
                    notification_type='ride_completed',
                    title='✅ Ride Completed!',
                    message=f'Your ride from {booking.ride_request.pickup_location} to {booking.ride_request.dropoff_location} has been completed. Please make payment.',
                    ride_request=booking.ride_request
                )
            elif new_status == "cancelled":
                create_notification(
                    user=booking.ride_request.customer,
                    notification_type='ride_cancelled',
                    title='❌ Ride Cancelled',
                    message=f'Your ride from {booking.ride_request.pickup_location} to {booking.ride_request.dropoff_location} has been cancelled by the driver.',
                    ride_request=booking.ride_request
                )
            
            messages.success(request, f"Booking marked as {new_status}.")
    return redirect("driver_dashboard")

# CANCEL RIDE 

@login_required
def cancel_ride_request(request, ride_request_id):
    ride = get_object_or_404(RideRequest, id=ride_request_id)

    #ride je create koreche(customer) ba je driver ke assign kora hoyeche shei driver cancel korte parbe."
    is_customer = request.user == ride.customer
    is_assigned_driver = False
    try:
        booking = ride.booking
        is_assigned_driver = request.user.role == "driver" and booking.driver_id == request.user.id
    except Booking.DoesNotExist:
        booking = None

    if not (is_customer or is_assigned_driver):
        return HttpResponseForbidden("You are not allowed to cancel this ride")

    # Do not alter finalized rides
    if ride.status in ["completed", "cancelled"]:
        messages.info(request, "This ride is already finalized.")
        return redirect("driver_dashboard" if request.user.role == "driver" else "customer_dashboard")

    # Cancel linked booking if present and not finalized
    if booking and booking.status not in ["completed", "cancelled"]:
        booking.status = "cancelled"
        booking.save(update_fields=["status"])

    # Mark ride cancelled
    ride.status = "cancelled"
    ride.save(update_fields=["status"])

    messages.success(request, "Ride cancelled.")
    return redirect("driver_dashboard" if request.user.role == "driver" else "customer_dashboard")


@login_required
def edit_ride_request(request, ride_request_id):
    """Allow a customer to edit their own pending ride's pickup/dropoff."""
    ride = get_object_or_404(RideRequest, id=ride_request_id, customer=request.user)
    if ride.status != "pending":
        messages.info(request, "Only pending rides can be edited.")
        return redirect("customer_dashboard")
    if request.method == "POST":
        pickup = (request.POST.get("pickup") or "").strip()
        dropoff = (request.POST.get("dropoff") or "").strip()
        if not pickup or not dropoff:
            messages.error(request, "Both pickup and dropoff are required.")
            return redirect("edit_ride_request", ride_request_id=ride.id)
        ride.pickup_location = pickup
        ride.dropoff_location = dropoff
        ride.save(update_fields=["pickup_location", "dropoff_location"])
        messages.success(request, "Ride updated.")
        return redirect("customer_dashboard")
    return render(request, "ride_edit.html", {"ride": ride})


# ===============================================================
# ================ DRIVER REVIEW ================================
# ===============================================================

@login_required
def create_review(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == "POST" and request.user.role == "customer" and booking.ride_request.customer == request.user and booking.status == "completed" and not DriverReview.objects.filter(booking=booking).exists():
        rating = int(request.POST.get("rating", 0))
        feedback = (request.POST.get("feedback") or "").strip()
        image_file = request.FILES.get("image")
        DriverReview.objects.create(
            booking=booking,
            driver=booking.driver,
            customer=request.user,
            rating=rating,
            feedback=feedback,
            image=image_file if image_file else None,
        )
        messages.success(request, "Review submitted.")
    return redirect("customer_dashboard")


@login_required
def delete_review(request, review_id):
    review = get_object_or_404(DriverReview, id=review_id)
    if request.user != review.customer:
        return HttpResponseForbidden("You can only delete your own review")
    if request.method == "POST":
        review.delete()
        messages.info(request, "Review deleted.")
    return redirect("customer_dashboard")


def list_driver_reviews(request, driver_id):
    reviews = DriverReview.objects.filter(driver_id=driver_id).order_by("-created_at")
    return render(request, "driver_dashboard.html", {"driver_reviews": reviews})


# ===============================================================
# ================ SUGGEST DRIVERS ===============================
# ===============================================================

@login_required
def suggest_drivers(request, ride_request_id):
    try:
        ride = RideRequest.objects.get(id=ride_request_id, status="pending")
    except RideRequest.DoesNotExist:
        messages.error(request, "Ride not found.")
        return redirect("customer_dashboard")

    if not ride.pickup_lat or not ride.pickup_lng:
        messages.error(request, "Ride missing coordinates.")
        return redirect("customer_dashboard")

    drivers = DriverProfile.objects.all()
    driver_distances = []
    for d in drivers:
        if d.current_lat and d.current_lng:
            distance = calculate_distance(ride.pickup_lat, ride.pickup_lng, d.current_lat, d.current_lng)
            driver_distances.append({
                "driver_id": d.user.id,
                "username": d.user.username,
                "vehicle": d.vehicle_details,
                "distance_km": round(distance, 2),
            })
    driver_distances.sort(key=lambda x: x["distance_km"])
    request.session["suggested_drivers"] = driver_distances[:5]
    return redirect("customer_dashboard")


# ===============================================================
# ================ NEARBY SYSTEM ================================
# ===============================================================

def nearby_drivers(request):
    """Public endpoint — show up to 10 nearby drivers (within 10 km)."""
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")

    drivers = DriverProfile.objects.select_related("user").all()
    results = []

    for d in drivers:
        if d.current_lat and d.current_lng:
            if lat and lng:
                distance = calculate_distance(float(lat), float(lng), d.current_lat, d.current_lng)
                if distance > 10:
                    continue
                distance_str = round(distance, 2)
            else:
                distance_str = "N/A"
            results.append({
                "username": d.user.username,
                "vehicle": d.vehicle_details,
                "distance_km": distance_str,
            })

    results = sorted(results, key=lambda x: x["distance_km"] if isinstance(x["distance_km"], (int, float)) else 9999)
    context = {"nearby": results[:10]}
    return render(request, "customer_dashboard.html", context)


@login_required
def nearby_rides(request):
    """Authenticated endpoint — returns pending rides within 10 km of driver."""
    user = request.user
    if user.role != "driver":
        return HttpResponseForbidden("Only drivers can view rides")

    try:
        driver = DriverProfile.objects.get(user=user)
    except DriverProfile.DoesNotExist:
        messages.error(request, "Driver profile not found.")
        return redirect("driver_profile")

    if not driver.current_lat or not driver.current_lng:
        messages.error(request, "Driver location not set.")
        return redirect("driver_profile")

    rides = RideRequest.objects.filter(status="pending")
    nearby = []

    for r in rides:
        if not r.pickup_lat or not r.pickup_lng:
            continue
        distance = calculate_distance(driver.current_lat, driver.current_lng, r.pickup_lat, r.pickup_lng)
        if distance <= 10:
            nearby.append({
                "id": r.id,
                "pickup_location": r.pickup_location,
                "dropoff_location": r.dropoff_location,
                "distance_km": round(distance, 2),
            })
    nearby = sorted(nearby, key=lambda x: x["distance_km"])
    request.session["nearby_rides"] = nearby[:10]
    return redirect("driver_dashboard")


@login_required
def list_available_rides(request):
    """Show only unbooked pending rides to drivers."""
    if request.user.role != "driver":
        return HttpResponseForbidden("Only drivers can view available rides")

    # ✅ Exclude rides that already have a booking
    rides = (
        RideRequest.objects.filter(status="pending")
        .exclude(booking__isnull=False)
        .order_by("-created_at")
    )
    return render(request, "driver_dashboard.html", {"available_rides": rides})

# ===============================================================
# ================ LEADERBOARD =================================
# ===============================================================

@login_required
def driver_leaderboard(request):
    drivers = (
        Account.objects.filter(role="driver")
        .annotate(
            total_completed=Count("bookings", filter=Q(bookings__status="completed")),
            avg_rating=Avg("driver_reviews__rating")
        )
        .order_by("-total_completed", "-avg_rating")[:10]
    )
    leaderboard = [
        {
            "username": d.username,
            "total_completed": d.total_completed or 0,
            "avg_rating": round(d.avg_rating or 0, 2),
        }
        for d in drivers
    ]
    total_drivers = Account.objects.filter(role="driver").count()
    total_rides = Booking.objects.filter(status="completed").count()
    avg_rating_overall = DriverReview.objects.aggregate(avg=Avg("rating"))[["avg"]] if False else DriverReview.objects.aggregate(avg=Avg("rating"))["avg"]
    context = {
        "leaderboard": leaderboard,
        "total_drivers": total_drivers,
        "total_rides": total_rides,
        "avg_rating": round(avg_rating_overall or 0, 2) if avg_rating_overall else 0.0,
    }
    return render(request, "leaderboard.html", context)


def driver_leaderboard_view(request):
    # wrapper to allow GET render without requiring auth for display
    drivers = (
        Account.objects.filter(role="driver")
        .annotate(
            total_completed=Count("bookings", filter=Q(bookings__status="completed")),
            avg_rating=Avg("driver_reviews__rating")
        )
        .order_by("-total_completed", "-avg_rating")[:10]
    )
    leaderboard = [
        {
            "username": d.username,
            "total_completed": d.total_completed or 0,
            "avg_rating": round(d.avg_rating or 0, 2),
        }
        for d in drivers
    ]
    total_drivers = Account.objects.filter(role="driver").count()
    total_rides = Booking.objects.filter(status="completed").count()
    avg_rating_overall = DriverReview.objects.aggregate(avg=Avg("rating"))[["avg"]] if False else DriverReview.objects.aggregate(avg=Avg("rating"))["avg"]
    context = {
        "leaderboard": leaderboard,
        "total_drivers": total_drivers,
        "total_rides": total_rides,
        "avg_rating": round(avg_rating_overall or 0, 2) if avg_rating_overall else 0.0,
    }
    return render(request, "leaderboard.html", context)


# ===============================================================
# ================ BOOKING CHAT ================================
# ===============================================================

@login_required
def chat_room(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    user = request.user
    # Guard: allow only booking's customer or assigned driver
    if booking.ride_request.customer != user and booking.driver != user:
        return HttpResponseForbidden("You are not allowed to view this chat.")
    # Hide chat if booking completed or cancelled
    if booking.status in ["completed", "cancelled"]:
        messages.info(request, "Chat is unavailable for finalized rides.")
        return redirect("driver_dashboard" if user.role == "driver" else "customer_dashboard")

    if request.method == "POST":
        text = (request.POST.get("text") or "").strip()
        if text:
            ChatMessage.objects.create(booking=booking, sender=user, text=text)
            return redirect("chat_room", booking_id=booking.id)
        else:
            messages.error(request, "Message cannot be empty.")

    messages_list = booking.messages.select_related("sender").all()
    return render(request, "chat_room.html", {
        "booking": booking,
        "messages_list": messages_list,
        "is_driver": booking.driver == user,
        "is_customer": booking.ride_request.customer == user,
    })


# ===============================================================
# ================ EMERGENCY SYSTEM =============================
# ===============================================================

@login_required
def emergency_view(request):
    # Show current contact and recent alert history in one page
    contact = None
    try:
        contact = request.user.emergency_contact
    except EmergencyContact.DoesNotExist:
        contact = None

    alerts = EmergencyAlert.objects.filter(user=request.user).order_by("-triggered_at")[:20]
    return render(request, "emergency.html", {"contact": contact, "alerts": alerts})


@login_required
def set_emergency_contact(request):
    if request.method == "POST":
        phone = request.POST.get("phone_number")
        if phone:
            contact, _ = EmergencyContact.objects.update_or_create(
                user=request.user, defaults={"phone_number": phone}
            )
            messages.success(request, "Emergency contact saved.")
    return redirect("emergency")


@login_required
def get_emergency_contact(request):
    try:
        contact = request.user.emergency_contact
    except EmergencyContact.DoesNotExist:
        contact = None
    return render(request, "emergency.html", {"contact": contact})


@login_required
def trigger_alert(request):
    try:
        contact = request.user.emergency_contact
        EmergencyAlert.objects.create(user=request.user, contact=contact, status="sent")
        messages.success(request, f"Emergency alert sent to {contact.phone_number}.")
    except EmergencyContact.DoesNotExist:
        messages.error(request, "No emergency contact set.")
    return redirect("emergency")


@login_required
def list_alerts(request):
    alerts = EmergencyAlert.objects.filter(user=request.user).order_by("-triggered_at")
    return render(request, "emergency.html", {"alerts": alerts})


@login_required
def delete_emergency_contact(request):
    if request.method != "POST":
        return redirect("emergency")
    try:
        contact = request.user.emergency_contact
        phone = contact.phone_number
        contact.delete()
        messages.info(request, f"Emergency contact {phone} deleted.")
    except EmergencyContact.DoesNotExist:
        messages.warning(request, "No emergency contact to delete.")
    return redirect("emergency")


# ===============================================================
# ================ LOCATION UPDATES =============================
# ===============================================================

def update_location(request):
    """Save the user's latest latitude and longitude."""
    lat = request.POST.get("lat") or request.GET.get("lat")
    lng = request.POST.get("lng") or request.GET.get("lng")
    next_url = request.POST.get("next") or request.GET.get("next") or request.META.get("HTTP_REFERER")

    if not lat or not lng:
        messages.error(request, "Missing coordinates.")
        return redirect(next_url or "home")

    try:
        lat = float(lat)
        lng = float(lng)
        if request.user.is_authenticated:
            # ✅ Always update Account fields
            request.user.last_lat = lat
            request.user.last_lng = lng
            request.user.save(update_fields=["last_lat", "last_lng"])

            # ✅ If driver, also update DriverProfile
            if request.user.role == "driver":
                driver_profile, _ = DriverProfile.objects.get_or_create(user=request.user)
                driver_profile.current_lat = lat
                driver_profile.current_lng = lng
                driver_profile.save(update_fields=["current_lat", "current_lng"])

            msg = "Authenticated user location updated"
        else:
            msg = "Anonymous location received (not saved)"

        messages.info(request, msg)
        return redirect(next_url or "home")
    except Exception as e:
        messages.error(request, str(e))
        return redirect(next_url or "home")


@login_required
def driver_dashboard(request):
    if request.user.role != "driver":
        return redirect("customer_dashboard")
    # Ensure driver has completed required profile fields
    try:
        profile = DriverProfile.objects.get(user=request.user)
        if not profile.nid_number or not profile.license_number:
            messages.info(request, "Please complete your driver profile before accessing the dashboard.")
            return redirect("driver_profile")
    except DriverProfile.DoesNotExist:
        messages.info(request, "Please complete your driver profile before accessing the dashboard.")
        return redirect("driver_profile")

    bookings = Booking.objects.filter(driver=request.user).order_by("-confirmed_at").select_related("ride_request", "ride_request__customer").prefetch_related("payment")
    total_completed = bookings.filter(status="completed").count()
    ongoing_bookings = [b for b in bookings if b.status == "ongoing"]
    total_ongoing = len(ongoing_bookings)
    available = (
        RideRequest.objects.filter(status="pending")
        .exclude(booking__isnull=False)
        .order_by("-created_at")[:20]
    )
    reviews = DriverReview.objects.filter(driver=request.user).order_by("-created_at")
    avg_rating = reviews.aggregate(avg=Avg("rating"))["avg"]

    return render(request, "driver_dashboard.html", {
        "bookings": bookings,
        "ongoing_bookings": ongoing_bookings,
        "available_rides": available,
        "reviews": reviews,
        "avg_rating": round(avg_rating or 0, 2) if avg_rating else None,
        "total_completed": total_completed,
        "total_ongoing": total_ongoing,
    })



# ============================================
# NOTIFICATION VIEWS
# ============================================

@login_required
def get_notifications(request):
    """API endpoint to get user notifications"""
    from django.http import JsonResponse
    
    try:
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:10]
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        
        notifications_data = [{
            'id': n.id,
            'type': n.notification_type,
            'title': n.title,
            'message': n.message,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%b %d, %Y · %H:%M'),
            'ride_id': n.ride_request.id if n.ride_request else None,
        } for n in notifications]
        
        return JsonResponse({
            'notifications': notifications_data,
            'unread_count': unread_count
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'notifications': [],
            'unread_count': 0
        }, status=500)


@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    from django.http import JsonResponse
    
    if request.method == 'POST':
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False}, status=400)


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    from django.http import JsonResponse
    
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False}, status=400)


def create_notification(user, notification_type, title, message, ride_request=None):
    """Helper function to create notifications"""
    Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        ride_request=ride_request
    )



@login_required
def driver_reviews_view(request):
    """Dedicated page showing all reviews for the driver"""
    if request.user.role != "driver":
        return HttpResponseForbidden("Only drivers can view this page")
    
    # Get all reviews for this driver
    reviews = DriverReview.objects.filter(driver=request.user).order_by('-created_at')
    
    # Calculate statistics
    total_reviews = reviews.count()
    if total_reviews > 0:
        avg_rating = sum(r.rating for r in reviews) / total_reviews
        rating_distribution = {}
        for rating in [5, 4, 3, 2, 1]:
            count = reviews.filter(rating=rating).count()
            percentage = (count / total_reviews * 100) if total_reviews > 0 else 0
            rating_distribution[rating] = {
                'count': count,
                'percentage': round(percentage, 1)
            }
    else:
        avg_rating = 0
        rating_distribution = {
            5: {'count': 0, 'percentage': 0},
            4: {'count': 0, 'percentage': 0},
            3: {'count': 0, 'percentage': 0},
            2: {'count': 0, 'percentage': 0},
            1: {'count': 0, 'percentage': 0},
        }
    
    context = {
        'reviews': reviews,
        'total_reviews': total_reviews,
        'avg_rating': round(avg_rating, 1) if avg_rating else 0,
        'rating_distribution': rating_distribution,
    }
    
    return render(request, 'driver_reviews.html', context)