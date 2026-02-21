from django.urls import path, include
from . import views


urlpatterns= [
    path('', views.home ,name="home" ),
    path('sign_in/', views.Sign_in, name="sign_in"),
    path('sign_up/', views.Sign_up, name="sign_up"),
    path('dashboard/', views.UserDash, name="dash"),
    path('add/', views.Add, name="add"),
    path('edit/<int:patrimoine_id>/', views.edit_patrimoine, name='edit_patrimoine'),
    path('delete/<int:patrimoine_id>/', views.delete_patrimoine, name='delete_patrimoine'),
    path('export-gpx/', views.export_gpx, name='export_gpx'),
    
]
