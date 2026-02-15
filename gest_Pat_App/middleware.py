from django.shortcuts import redirect
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

PUBLIC_PATHS = ["/home/", "/api/", "/sign_in/", "/sign_up/", "/admin/"]

class TokenVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Autoriser les chemins publics
        for prefix in PUBLIC_PATHS:
            if request.path.startswith(prefix):
                return self.get_response(request)

        # Vérifier si l'utilisateur est authentifié Django
        # if not request.user.is_authenticated:
        #     return redirect("sign_in")  # <--- return obligatoire

        # Vérifier le token JWT si présent
        token = request.session.get("access_token")
        if token:
            try:
                AccessToken(token)
            except TokenError:
                request.session.flush()
                return redirect("sign_in")

        # Vérifier si l'utilisateur est toujours actif
        # if not request.user.is_active:
        #     request.session.flush()
        #     return redirect("sign_in")

        return self.get_response(request)
