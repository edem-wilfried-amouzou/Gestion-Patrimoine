# Middleware for JWT token verification
from django.shortcuts import redirect
from django.contrib.auth import logout
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

PUBLIC_PATHS = ["/home/","/", "/api/", "/sign_in/", "/sign_up/", "/admin/"]


class TokenVerificationMiddleware:
    """
    Middleware to verify JWT tokens from session.
    Allows public paths without authentication.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Allow public paths
        for prefix in PUBLIC_PATHS:
            if request.path.startswith(prefix):
                return self.get_response(request)

        # Check if token exists in session
        token = request.session.get("access_token")
        if not token:
            # No token, redirect to login
            logout(request)
            request.session.flush()
            return redirect("sign_in")

        # Verify token expiration
        try:
            AccessToken(token)
        except TokenError:
            # Token expired or invalid
            logout(request)
            request.session.flush()
            return redirect("sign_in")

        return self.get_response(request)
