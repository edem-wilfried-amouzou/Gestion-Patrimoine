# from django.shortcuts import redirect
# from rest_framework_simplejwt.exceptions import TokenError
# from rest_framework_simplejwt.tokens import AccessToken
# from django.contrib.auth import logout
#
# PUBLIC_PATHS = ["/home/", "/api/", "/sign_in/", "/sign_up/", "/admin/"]
#
# class TokenVerificationMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response
#
#     def __call__(self, request):
#         # Autoriser les chemins publics
#         for prefix in PUBLIC_PATHS:
#             if request.path.startswith(prefix):
#                 return self.get_response(request)
#
#         # Vérifier si l'utilisateur est authentifié Django
#         # if not request.user.is_authenticated:
#         #     return redirect("sign_in")  # <--- return obligatoire
#         # Vérifier le token JWT si présent
#
#
#         token = request.session.get("access_token")
#         if token:
#             try:
#                 access = AccessToken(token)
#                 access.check_exp()
#             except TokenError:
#                 request.session.flush()
#                 logout(request)
#                 return redirect("sign_in")
#
#
#         # Vérifier si l'utilisateur est toujours actif
#         # if not request.user.is_active:
#         #     request.session.flush()
#         #     return redirect("sign_in")
#
#         return self.get_response(request)

from django.shortcuts import redirect
from django.contrib.auth import logout
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

PUBLIC_PATHS = [
    "/home/",
    "/api/",
    "/sign_in/",
    "/sign_up/",
    "/admin/",
    "/reset/",
    "/auth/google/login/",
    "/auth/google/callback/",
    "/password-reset/",
]

class TokenVerificationMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # 1️⃣ Autoriser routes publiques
        if any(request.path.startswith(path) for path in PUBLIC_PATHS):
            return self.get_response(request)

        if request.path == "/":
            return self.get_response(request)


        # 2️⃣ Vérifier token session
        token = request.session.get("access_token")

        if not token:
            logout(request)
            request.session.flush()
            return redirect("sign_in")

        # 3️⃣ Vérifier validité JWT
        try:
            AccessToken(token)
        except TokenError:
            logout(request)
            request.session.flush()
            return redirect("sign_in")

        return self.get_response(request)