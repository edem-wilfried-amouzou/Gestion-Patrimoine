from django import forms
from .models import Patrimoine

class PatrimoineForm(forms.ModelForm):
    class Meta:
        model = Patrimoine
        fields = ['nom','latitude', 'longitude']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control'}),
        }