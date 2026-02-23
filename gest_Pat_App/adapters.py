from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from rest_framework_simplejwt.tokens import AccessToken
import uuid


class GoogleOAuthAdapter(DefaultSocialAccountAdapter):

    def is_auto_signup_allowed(self, request, sociallogin):
        return True

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        if not user.username:
            email = data.get('email', '')
            base = email.split('@')[0] if email else 'user'
            user.username = f"{base}_{uuid.uuid4().hex[:6]}"
        return user

    def pre_social_login(self, request, sociallogin):
        """Utilisateur existant → injecter JWT immédiatement"""
        if sociallogin.is_existing:
            user = sociallogin.user
            if user and user.pk:
                access = AccessToken.for_user(user)
                request.session["access_token"] = str(access)
                request.session["username"] = user.username
                request.session.save()