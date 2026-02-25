#Creation de fichier sans extension Procfile
    web: gunicorn gestion_patrinoine.wsgi --log-file -


#Créationde fichier runtime.txt 
    python-3.13.0

#Rassemblage des fichiers statics en staticfiles
    python manage.py collectstatic

#
