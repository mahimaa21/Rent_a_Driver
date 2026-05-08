from django.urls import path
from . import views

urlpatterns = [

    path("", views.health_dashboard, name="health_dashboard"),
    
    path("notes/", views.notes_list, name="utilities_notes_list"),
    path("notes/create/", views.notes_create, name="utilities_notes_create"),
    path("notes/<int:note_id>/edit/", views.notes_edit, name="utilities_notes_edit"),
    path("notes/<int:note_id>/delete/", views.notes_delete, name="utilities_notes_delete"),
]