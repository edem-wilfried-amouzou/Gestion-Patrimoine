from django.urls import path
from . import views
from .views import secureImageView

urlpatterns = [
    path('sign_up/', views.RegisterAPI.as_view(), name='sign_up'),
    path('sign_in/', views.LoginAPI.as_view(), name='sign_in'),
    path('image/<int:pk>/', secureImageView.as_view(), name='secure-image'),
]