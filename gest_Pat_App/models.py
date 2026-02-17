from django.db import models
from django.contrib.auth.models import User

class Patrimoine(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nom = models.CharField(max_length=200, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    ville = models.CharField(max_length=100)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_update = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Patrimoine'
        verbose_name_plural = 'Patrimoines'
        db_table = 'patrmoine'

    def __str__(self):
        return self.nom

    '''
    - l'ecran d'aceuil (nella)
    - le login (paul) 
    - le sign up (obed)
    - la de lutilisateur avec la carte portant les patrimoines (peniel)
    - la page d'ajoute ( alexis)
    - api token
    - api connexion
    
    '''

'''
- IL I
'''