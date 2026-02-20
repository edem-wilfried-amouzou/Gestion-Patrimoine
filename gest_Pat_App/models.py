from django.db import models
from django.contrib.auth.models import User

class Patrimoine(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nom = models.CharField(max_length=200, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    ville = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_update = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Patrimoine'
        verbose_name_plural = 'Patrimoines'
        db_table = 'patrmoine'

    def __str__(self):
        return self.nom


class SignInAttempt(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    attempt = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.attempt} attempts"