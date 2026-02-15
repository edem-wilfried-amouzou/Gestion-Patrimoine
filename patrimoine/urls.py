from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('delete/<int:id>/', views.delete_patrimoine, name='delete_patrimoine'),
    path('update/<int:id>/', views.update_position, name='update_position'),
    path('itineraire/', views.itineraire, name='itineraire'),
]
