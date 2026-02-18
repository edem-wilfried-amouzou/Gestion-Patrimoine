from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from http.client import responses
from statistics import mean
import gpxpy.gpx
import requests
import folium

from .models import Patrimoine
from .forms import PatrimoineForm


def home(request):
    return render(request, 'home.html', {})

def Sign_in(request):
    print("SIGN in VIEW")

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        response = requests.post(
            "http://127.0.0.1:8000/api/sign_in/",
            json={
                "username": username,
                "password": password
            }
        )

        if response.status_code == 200:
            token = response.json().get("access_token")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
            request.session["access_token"] = str(token)
            request.session["username"] = username
            request.session.save()
            return redirect('dash')
        else:
            return render(request, 'sign_in.html', {"error": "Login invalide"})

    return render(request, "sign_in.html")


def Sign_up(request):
    print("SIGN UP VIEW")
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        pw = request.POST.get('pw')
        rp = request.POST.get('re-pw')

        if not pw or not rp:
            return render(request, "sign_up.html", {
                "error": "Tous les champs sont obligatoires"
            })

        try:
            validate_password(pw)
        except ValidationError as e:
            errors = e.messages
            redirect("sign_up")
            return render(request, "sign_up.html", {
                "error": errors
            })


        if pw == rp:
            response = requests.post(
                "http://127.0.0.1:8000/api/sign_up/",
                json={
                    "username": username,
                    "email": email,
                    "password": pw
                }
            )

            if response.status_code == 400:
                error = response.json().get("error")
                msg = str(error)
                redirect("sign_up")
                return render(request, "sign_up.html", { "error": msg})

            if response.status_code == 201:
                redirect("sign_in")
                return render(request, "sign_in.html")
        else:
            redirect("sign_up")
            return render(request, "sign_up.html", {
                "error": "Les mots de passes ne correspondent pas"
            })

    redirect("sign_up")
    return render(request, "sign_up.html")

        # else:
        #     msg="Password not valid"
        #     context = {"msg": msg}
        #     redirect("sign_in")
        #     return render(request, "sign_up.html", context)

    return render(request, "sign_up.html", context)



# @login_required
def UserDash(request):
    # Récupération des patrimoine de l'utilisateur connecté
    patrimoines = Patrimoine.objects.filter(user=request.user)

    # CENTRAGE INTELLIGENT
    if patrimoines.exists():
        center_lat = mean([p.latitude for p in patrimoines])
        center_lng = mean([p.longitude for p in patrimoines])
    else:
        center_lat = 6.13
        center_lng = 1.22

    # CREATION CARTE
    map = folium.Map(location=[center_lat, center_lng], zoom_start=13)

    # MARQUEUR UTILISATEUR
    folium.Marker(
        [center_lat, center_lng],
        popup="Vous êtes ici",
        icon=folium.Icon(color="blue", icon="user")
    ).add_to(map)

    # MARKERS PATRIMOINES
    for p in patrimoines:
        folium.Marker(
            [p.latitude, p.longitude],
            popup=p.nom,
            icon=folium.Icon(color="red", icon="home")
        ).add_to(map)

    map_html = map._repr_html_()

    return render(request, 'board.html', {
        'map': map_html,
        'patrimoines': patrimoines,
        'center_lat': center_lat,
        'center_lng': center_lng
    })


#  @login_required
# def Add(request):
#     if request.method == "POST":
#         nom = request.POST.get("nom")
#         lat = request.POST.get("latitude")
#         lng = request.POST.get("longitude")
#
#         try:
#             Patrimoine.objects.create(
#                 user=request.user,
#                 nom=nom,
#                 latitude=float(lat),
#                 longitude=float(lng)
#             )
#             return JsonResponse({"status": "success", "message": "Patrimoine ajouté"})
#         except Exception as e:
#             return JsonResponse({"status": "error", "message": str(e)})
#
#     return JsonResponse({"status": "error", "message": "Méthode non autorisée"})

def Add(request):
    form = PatrimoineForm
    carte = folium.Map(location=[14.7, -17.4],zoom_start=6)
    carte_html = carte.repr_html()
    context = {
        'form':form,
        'carte':carte_html
    }
    return render(request,'geo/ajouter.html',context)

# ÉDITION PATRIMOINE
# @login_required
def edit_patrimoine(request, patrimoine_id):
    patrimoine = get_object_or_404(Patrimoine, id=patrimoine_id, user=request.user)

    if request.method == "POST":
        nom = request.POST.get("nom")
        lat = request.POST.get("latitude")
        lng = request.POST.get("longitude")

        try:
            patrimoine.nom = nom
            patrimoine.latitude = float(lat)
            patrimoine.longitude = float(lng)
            patrimoine.save()

            return JsonResponse({"status": "success", "message": "Patrimoine modifié"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Méthode non autorisée"})


# SUPPRESSION PATRIMOINE
# @login_required
def delete_patrimoine(request, patrimoine_id):
    patrimoine = get_object_or_404(Patrimoine, id=patrimoine_id, user=request.user)

    if request.method == "POST":
        try:
            patrimoine.delete()
            return JsonResponse({"status": "success", "message": "Patrimoine supprimé"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Méthode non autorisée"})


# EXPORT GPX
# @login_required
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