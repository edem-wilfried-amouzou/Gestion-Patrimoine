from django.urls import path
from .views import ajouter_patrimoine

urlpatterns = [
    path('',ajouter_patrimoine,name='ajouter_patrimoine'),
]