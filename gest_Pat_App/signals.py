from allauth.socialaccount.signals import social_account_added
from django.dispatch import receiver
from rest_framework_simplejwt.tokens import AccessToken


@receiver(social_account_added)
def inject_jwt_new_google_user(sender, request, sociallogin, **kwargs):
    """Nouvel utilisateur Google → injecter JWT après création du compte"""
    user = sociallogin.user
    if user and user.pk:
        access = AccessToken.for_user(user)
        request.session["access_token"] = str(access)
        request.session["username"] = user.username
        request.session.save()