from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class patrimoine(models.Model):
    nom = models.CharField(max_length=200)
    ville = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    date_ajout = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom
