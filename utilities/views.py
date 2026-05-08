from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Note

def health_dashboard(request):
    """Server-rendered health page without any JS fetching."""
    recent_notes = None
    if request.user.is_authenticated:
        
        recent_notes = Note.objects.filter(user=request.user).order_by("-updated_at")[:5]
    context = {
        "status": "ok",
        "database": "connected",
        "app_name": "Rent a Driver",
        "version": "1.0.0",
        "debug": settings.DEBUG,
        "timezone_name": settings.TIME_ZONE,
        "installed_apps": [app for app in settings.INSTALLED_APPS if app.startswith("core") or app in ["emergency", "utilities"]],
        "recent_notes": recent_notes,
    }
    return render(request, "health.html", context)




@login_required
def notes_list(request):
    
    notes = Note.objects.filter(user=request.user).order_by("-updated_at")
    return render(request, "utilities_notes_list.html", {"notes": notes})


@login_required
def notes_create(request):
    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        body = (request.POST.get("body") or "").strip()
        if not title:
            messages.error(request, "Title is required.")
            return redirect("utilities_notes_create")
        Note.objects.create(title=title, body=body, user=request.user)
        messages.success(request, "Note created.")
        return redirect("utilities_notes_list")
    return render(request, "utilities_notes_form.html")


@login_required
def notes_edit(request, note_id):
    note = get_object_or_404(Note, id=note_id, user=request.user)
    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        body = (request.POST.get("body") or "").strip()
        if not title:
            messages.error(request, "Title is required.")
            return redirect("utilities_notes_edit", note_id=note.id)
        note.title = title
        note.body = body
        note.save()
        messages.success(request, "Note updated.")
        return redirect("utilities_notes_list")
    return render(request, "utilities_notes_form.html", {"note": note})


@login_required
def notes_delete(request, note_id):
    if request.method != "POST":
        return redirect("utilities_notes_list")
    note = get_object_or_404(Note, id=note_id, user=request.user)
    note.delete()
    messages.info(request, "Note deleted.")
    return redirect("utilities_notes_list")