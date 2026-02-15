from django.urls import path
from . import views


urlpatterns= [
    path('', views.home ,name="home" ),
    path('sign_in/', views.Sign_in, name="sign_in"),
    path('sign_up/', views.Sign_up, name="sign_up"),
    path('dashboard/', views.UserDash, name="dash")
]
