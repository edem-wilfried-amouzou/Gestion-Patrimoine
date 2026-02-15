from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Patrimoine
import folium

@login_required
def dashboard(request):

    if request.method == "POST":
        nom = request.POST.get("nom")
        lat = request.POST.get("latitude")
        lng = request.POST.get("longitude")

        Patrimoine.objects.create(
            user=request.user,
            nom=nom,
            latitude=lat,
            longitude=lng
        )

        return redirect('dashboard')

    map = folium.Map(location=[6.13, 1.22], zoom_start=13)

    patrimoines = Patrimoine.objects.filter(user=request.user)

    for p in patrimoines:
        folium.Marker(
            [p.latitude, p.longitude],
            popup=f"""
                <b>{p.nom}</b><br>
                <button onclick="deletePatrimoine({p.id})">❌ Supprimer</button>
            """,
            tooltip=p.nom
        ).add_to(map)

    map_html = map._repr_html_()

    return render(request, 'patrimoine/dashboard.html', {
        'map': map_html,
        'patrimoines': patrimoines
    })


@login_required
def delete_patrimoine(request, id):
    Patrimoine.objects.filter(id=id, user=request.user).delete()
    return JsonResponse({"status": "ok"})


@login_required
def update_position(request, id):

    if request.method == "POST":
        lat = request.POST.get("latitude")
        lng = request.POST.get("longitude")

        p = Patrimoine.objects.get(id=id, user=request.user)
        p.latitude = lat
        p.longitude = lng
        p.save()

    return JsonResponse({"status": "ok"})


@login_required
def itineraire(request):

    patrimoines = Patrimoine.objects.filter(user=request.user)

    map = folium.Map(location=[6.13, 1.22], zoom_start=13)

    points = []

    for p in patrimoines:
        points.append([p.latitude, p.longitude])

        folium.Marker(
    [p.latitude, p.longitude],
    popup=f"""
        <b>{p.nom}</b><br>
        <button onclick="deletePatrimoine({p.id})">❌ Supprimer</button>
    """,
    tooltip=p.nom,
).add_to(map)


    if len(points) >= 2:
        folium.PolyLine(points).add_to(map)

    map.fit_bounds(points) 
    map_html = map._repr_html_()

    return render(request, 'patrimoine/dashboard.html', {
        'map': map_html,
        'patrimoines': patrimoines
    })
