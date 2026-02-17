from django.shortcuts import render
from .formulaire import patrimoineForm
import folium

# Create your views here.

def ajouter_patrimoine(request):
    form = patrimoineForm
    carte = folium.Map(location=[14.7, -17.4],zoom_start=6)
    carte_html = carte._repr_html_()
    context = {
        'form':form,
        'carte':carte_html
    }
    return render(request,'geo/ajouter.html',context)
