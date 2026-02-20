from django.urls import path
from . import views


urlpatterns= [
    path('', views.home ,name="home" ),
    path('sign_in/', views.Sign_in, name="sign_in"),
    path('sign_up/', views.Sign_up, name="sign_up"),
    path('logout/', views.logout_view, name="logout"),
    path('dashboard/', views.UserDash, name="dash"),
    path('add/', views.Add, name="add"),
    path('edit-patrimoine/<int:patrimoine_id>/', views.edit_patrimoine, name='edit_patrimoine'),
    path('delete-patrimoine/<int:patrimoine_id>/', views.delete_patrimoine, name='delete_patrimoine'),
    path('export-gpx/', views.export_gpx, name='export_gpx'),
    path('export-pdf/', views.export_pdf, name='export_pdf'),
    path('itinerary-to/', views.itinerary_to_patrimoine, name='itinerary_to'),
    path('get-patrimoines/', views.get_patrimoines_json, name='api_patrimoines'),
]


    