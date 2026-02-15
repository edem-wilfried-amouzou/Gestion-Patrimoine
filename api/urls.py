from django.urls import path
from . import views

urlpatterns = [
    path('sign_up/', views.RegisterAPI.as_view(), name='sign_up'),
    path('sign_in/', views.LoginAPI.as_view(), name='sign_in'),
]