from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add/', views.add_patrimoine, name='add_patrimoine'),
    path('export-gpx/', views.export_gpx, name='export_gpx'),
]
