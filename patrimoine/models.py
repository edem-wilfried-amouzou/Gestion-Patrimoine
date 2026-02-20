from django.db import models
from django.contrib.auth.models import User

class Patrimoine(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    photo = models.ImageField(upload_to='patrimoines/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.nom