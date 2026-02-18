from django import forms
from .models import patrimoine

Villes = [
    ("Lome", "Lomé"),
    ("Kara", "Kara"),
    ("Sokode", "Sokodé"),
    ("Atakpame", "Atakpamé"),
    ("Kpalime", "Kpalimé"),
    ("Aneho", "Aného"),
    ("Tsevie", "Tsévié"),
    ("Dapaong", "Dapaong"),
    ("Bassar", "Bassar"),
    ("Notse", "Notsé"),
    ("Badou", "Badou"),
]

class patrimoineForm(forms.ModelForm):
    ville = forms.ChoiceField(choices=Villes,required=False,label="ville")

    class Meta:
        model = patrimoine
        fields = ['ville','nom','latitude', 'longitude']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control'}),
        }