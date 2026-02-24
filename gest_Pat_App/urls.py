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
    path('send-gpx-email/', views.send_gpx_email, name='send_gpx_email'),
    path('export-pdf/', views.export_pdf, name='export_pdf'),
    path('send-pdf-email/', views.send_pdf_email, name='send_pdf_email'),
    path('itinerary-to/', views.itinerary_to_patrimoine, name='itinerary_to'),
    path('itinerary-multi/', views.itinerary_multi, name='itinerary_multi'),
    path('get-patrimoines/', views.get_patrimoines_json, name='api_patrimoines'),
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('contAd', views.contAD, name='contAD')
]


    