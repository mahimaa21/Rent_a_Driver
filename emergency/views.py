from django.shortcuts import redirect

# Emergency views core.views e rakha hoyeche
# Purono link gula kaj korar jonno  redirect deya hoyeche

def set_contact(request):
    return redirect("set_emergency_contact")


def get_contact(request):
    return redirect("emergency")


def trigger_alert(request):
    return redirect("trigger_alert")


def alert_history(request):
    return redirect("emergency")