# from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
# from rest_framework_simplejwt.tokens import AccessToken
# import uuid
#
#
# class GoogleOAuthAdapter(DefaultSocialAccountAdapter):
#
#     def is_auto_signup_allowed(self, request, sociallogin):
#         return True
#
#     def populate_user(self, request, sociallogin, data):
#         user = super().populate_user(request, sociallogin, data)
#         if not user.username:
#             email = data.get('email', '')
#             base = email.split('@')[0] if email else 'user'
#             user.username = f"{base}_{uuid.uuid4().hex[:6]}"
#         return user
#
#     def pre_social_login(self, request, sociallogin):
#         """Utilisateur existant → injecter JWT immédiatement"""
#         if sociallogin.is_existing:
#             user = sociallogin.user
#             if user and user.pk:
#                 access = AccessToken.for_user(user)
#                 request.session["access_token"] = str(access)
#                 request.session["username"] = user.username
#                 request.session.save()


from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class GoogleOAuthAdapter(DefaultSocialAccountAdapter):

    def is_auto_signup_allowed(self, request, sociallogin):
        # Garde ta logique originale
        return True

    def populate_user(self, request, sociallogin, data):
        # Garde ta logique originale de génération de username
        user = super().populate_user(request, sociallogin, data)
        if not user.username:
            email = data.get('email', '')
            base = email.split('@')[0] if email else 'user'
            user.username = f"{base}_{uuid.uuid4().hex[:6]}"
        return user

    def pre_social_login(self, request, sociallogin):
        """
        MODIFIÉ : Gère maintenant la fusion automatique si l'email existe déjà,
        tout en gardant ton injection de tokens JWT.
        """

        # 1. Si le lien social existe déjà (utilisateur déjà connu de Google)
        if sociallogin.is_existing:
            self._inject_session_data(request, sociallogin.user)
            return

        # 2. CAS CRITIQUE : L'email existe déjà via inscription manuelle
        # On récupère l'email envoyé par Google
        email = sociallogin.account.extra_data.get('email')

        if email:
            try:
                # On cherche si cet utilisateur existe déjà en base
                existing_user = User.objects.get(email=email)

                # FUSION : On lie le compte Google au compte manuel existant
                # Cela évite l'erreur "Account already exists"
                sociallogin.connect(request, existing_user)

                # On prépare la session pour ton middleware
                self._inject_session_data(request, existing_user)

            except User.DoesNotExist:
                # Si l'utilisateur n'existe pas, l'Auto-signup classique se lancera
                pass

    def _inject_session_data(self, request, user):
        """
        Centralise l'injection des données dans la session pour ton middleware.
        """
        if user and user.pk:
            access = AccessToken.for_user(user)
            request.session["access_token"] = str(access)
            request.session["username"] = user.username
            # Ajout du login_time pour ton middleware de 5 minutes
            request.session["login_time"] = timezone.now().isoformat()
            request.session.save()
            print(f"--- SESSION ET TOKEN INJECTÉS POUR : {user.username} ---")