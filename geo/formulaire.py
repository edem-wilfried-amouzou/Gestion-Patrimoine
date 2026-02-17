from django import forms
from .models import patrimoine

class patrimoineForm(forms.ModelForm):
    class Meta:
        model = patrimoine
        fields = ['nom','latitude', 'longitude']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control'}),
        }