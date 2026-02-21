from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse, Http404
from gest_Pat_App.models import ImagePatrimoine


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

    def get(self, request):
        return Response(
            {"message": "Use POST method to login"},
            status=status.HTTP_200_OK
        )

    def post(self, request):
        username = request.data.get("username")
        pw = request.data.get("password")

        user = authenticate(request, username=username, password=pw)

        if user is not None:
            access = AccessToken.for_user(user)
            return Response({
                "message": "User logged in successfully",
                "access_token": str(access)
            }, status=status.HTTP_200_OK)

        return Response({
            "error": "Invalid username or password"
        }, status=status.HTTP_400_BAD_REQUEST)
        

class secureImageView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request,pk):
        try:
            image = ImagePatrimoine.objects.get(pk=pk)
        except ImagePatrimoine.DoesNotExist:
            raise Http404("Image non trouvée")
            #if image.patrmoine.user != request.user:
            #   raise Http404("Accès interdit")
        return FileResponse(open(image.image_originale.path,'rb'))
    
        