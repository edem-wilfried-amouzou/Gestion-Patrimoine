from http.client import responses
import requests
from django.shortcuts import render
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


# @login_required(login_url='sign_in')
def UserDash(request):
    return render(request, 'board.html')

def Sign_in(request):

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        response = requests.post(
            "http://127.0.0.1:8000/api/sign_in/",
            json={
                "username": username,
                "password": password
            }
        )

        if response.status_code == 200:
            token = response.json().get("access_token")
            request.session["access_token"] = str(token)
            request.session["username"]= username
            request.session.save()
            return redirect('dash')
        else:
            return render(request, 'sign_in.html', {"error": "Login invalide"})

    return render(request, "sign_in.html")


def Sign_up(request):
    return render(request, "sign_up.html", {})

def home(request):
    return render(request, 'home.html', {})