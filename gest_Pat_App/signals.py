import random
import string
from string import digits

from allauth.socialaccount.signals import social_account_added
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.dispatch import receiver
from django.http import request
from django.template.defaultfilters import default
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from jwt.utils import force_bytes
from rest_framework_simplejwt.tokens import AccessToken
from django.utils import timezone

from gest_Pat_App.views import password_reset_confirm


def generer_pw(lenght=10):
    caracters = (string.ascii_uppercase +
                 string.ascii_lowercase +
                 digits +
                 "!@#$%&*")
    return "".join(random.choices(caracters, k=lenght))


@receiver(social_account_added)
def inject_jwt_new_google_user(sender, request, sociallogin, **kwargs):
    user = sociallogin.user
    if user and user.pk:
        pw = generer_pw()
        user.set_password(pw)
        user.save()

        #lien de renitialisation
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = request.build_absolute_url(
            reverse("password_reset_confirm", kwargs={
                "uidb64" : uid,
                "token" : token
                }
            )
        )

        try:
            send_mail(
                subject="Bienvenus sur Gestion Patrinoine - Vos identifiants",
                message=f"""
                Bonjour {user.username},

                Votre vous etre inscrit sur Gestion Patrimoine.

                Voici vos identifiants pour vous connecter sans Google :

                Nom d'utilisateur : {user.username}
                Mot de passe : {pw}

                Pour modifier votre mot de passe, cliquez ici :
                {reset_link}

                Ce lien expire dans 1 heure.

                À bientôt sur Gestion Patrimoine.
                """,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Erreur envoi mail : {e}")


        access = AccessToken.for_user(user)
        request.session["access_token"] = str(access)
        request.session["username"] = user.username
        request.session["login_time"] = timezone.now().isoformat()  # ✅ Ajouter
        request.session.save()

