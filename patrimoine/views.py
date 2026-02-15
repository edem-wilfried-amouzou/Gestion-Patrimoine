from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Patrimoine
import folium
from statistics import mean
from django.http import HttpResponse, JsonResponse
import gpxpy.gpx

@login_required
def dashboard(request):

    patrimoines = Patrimoine.objects.filter(user=request.user)

    # ------------------------
    # CENTRAGE INTELLIGENT
    # ------------------------

    if patrimoines.exists():
        center_lat = mean([p.latitude for p in patrimoines])
        center_lng = mean([p.longitude for p in patrimoines])
    else:
        center_lat = 6.13
        center_lng = 1.22

    # ------------------------
    # CREATION CARTE
    # ------------------------

    map = folium.Map(location=[center_lat, center_lng], zoom_start=13)

    # ------------------------
    # MARQUEUR UTILISATEUR
    # ------------------------

    folium.Marker(
        [center_lat, center_lng],
        popup="Vous êtes ici",
        icon=folium.Icon(color="blue", icon="user")
    ).add_to(map)

    # ------------------------
    # MARKERS PATRIMOINES
    # ------------------------

    for p in patrimoines:
        folium.Marker(
            [p.latitude, p.longitude],
            popup=p.nom,
            icon=folium.Icon(color="red", icon="home")
        ).add_to(map)

    map_html = map._repr_html_()

    return render(request, 'patrimoine/dashboard.html', {
        'map': map_html,
        'patrimoines': patrimoines,
        'center_lat': center_lat,
        'center_lng': center_lng
    })


# ✅ AJOUT PATRIMOINE (AJAX)
@login_required
def add_patrimoine(request):
    
    if request.method == "POST":
        nom = request.POST.get("nom")
        lat = request.POST.get("latitude")
        lng = request.POST.get("longitude")

        try:
            Patrimoine.objects.create(
                user=request.user,
                nom=nom,
                latitude=float(lat),
                longitude=float(lng)
            )
            return JsonResponse({"status": "success", "message": "Patrimoine ajouté"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
    
    return JsonResponse({"status": "error", "message": "Méthode non autorisée"})


# ✅ EXPORT GPX 🔥
@login_required
def export_gpx(request):

    patrimoines = Patrimoine.objects.filter(user=request.user)

    gpx = gpxpy.gpx.GPX()
    track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(track)

    segment = gpxpy.gpx.GPXTrackSegment()
    track.segments.append(segment)

    for p in patrimoines:
        segment.points.append(
            gpxpy.gpx.GPXTrackPoint(p.latitude, p.longitude, name=p.nom)
        )

    response = HttpResponse(gpx.to_xml(), content_type='application/gpx+xml')
    response['Content-Disposition'] = 'attachment; filename="patrimoines.gpx"'

    return response