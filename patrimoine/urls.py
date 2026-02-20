from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add-patrimoine/', views.add_patrimoine, name='add_patrimoine'),
    path('edit-patrimoine/<int:patrimoine_id>/', views.edit_patrimoine, name='edit_patrimoine'),
    path('delete-patrimoine/<int:patrimoine_id>/', views.delete_patrimoine, name='delete_patrimoine'),
    path('export-gpx/', views.export_gpx, name='export_gpx'),
    path('export-pdf/', views.export_pdf, name='export_pdf'),
    path('itinerary-to/', views.itinerary_to_patrimoine, name='itinerary_to'),
    path('itinerary-multi/', views.itinerary_multi, name='itinerary_multi'),
    path('api/patrimoines/', views.get_patrimoines_json, name='api_patrimoines'),
]