from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login
from rest_framework_simplejwt.tokens import AccessToken


class RegisterAPI(APIView):
    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        pw = request.data.get("password")

        if User.objects.filter(username=username).exists():
            return Response({
                "error":"User already exists",            
                 }, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.create_user(username=username, password=pw,  email=email)
        user.save()

        return Response({
            "message":"User created successfully"
        }, status=status.HTTP_201_CREATED)
    
    
class LoginAPI(APIView):
    def post(self, request):
        username = request.data.get("username")
        pw = request.data.get("password")
        # print("DATA RECEIVED:", request.data)

        user = authenticate(request, username=username, password=pw)
        if user is not None:
            # login(request, user)
            access = AccessToken.for_user(user)
            return Response({
                "message":"User logged in successfully",
                "access_token": str(access)
            }, status=status.HTTP_200_OK)
        else:
            try:
                user_t = User.objects.get(username=username)
            except User.DoesNotExist:
                user_t = None

            if user_t == None:
                return Response({
                    "error":"Invalid username"
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "error": "Invalid password"
            }, status=status.HTTP_401_UNAUTHORIZED)