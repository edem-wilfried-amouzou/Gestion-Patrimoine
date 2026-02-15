from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add/', views.add_patrimoine, name='add_patrimoine'),
    path('edit/<int:patrimoine_id>/', views.edit_patrimoine, name='edit_patrimoine'),
    path('delete/<int:patrimoine_id>/', views.delete_patrimoine, name='delete_patrimoine'),
    path('export-gpx/', views.export_gpx, name='export_gpx'),
]