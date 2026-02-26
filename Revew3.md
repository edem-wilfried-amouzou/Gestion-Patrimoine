#Changement de nos gest_Pat_App sign_in 
```
def Sign_up(request):
    print("SIGN UP VIEW")
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        pw = request.POST.get('pw')
        rp = request.POST.get('re-pw')

        if not pw or not rp:
            return render(request, "sign_up.html", {
                "error": "Tous les champs sont obligatoires"
            })

        try:
            validate_password(pw)
        except ValidationError as e:
            errors = e.messages
            redirect("sign_up")
            return render(request, "sign_up.html", {
                "error": errors
            })


        if pw == rp:
            response = requests.post(
                request.build_absolute_uri("/api/sign_up/"),
                json={
                                "username": username,
                                "email": email,
                                "password": pw
                            }
            )

            if response.status_code == 400:
                error = response.json().get("error")
                msg = str(error)
                redirect("sign_up")
                return render(request, "sign_up.html", { "error": msg})

            if response.status_code == 201:
                redirect("sign_in")
                return render(request, "sign_in.html")
        else:
            redirect("sign_up")
            return render(request, "sign_up.html", {
                "error": "Les mots de passes ne correspondent pas"
            })

    redirect("sign_up")
    return render(request, "sign_up.html")

        # else:
        #     msg="Password not valid"
        #     context = {"msg": msg}
        #     redirect("sign_in")
        #     return render(request, "sign_up.html", context)

    return render(request, "sign_up.html", context)

```

#Changement de nos gest_Pat_App sign_up



def Sign_up(request):
    print("SIGN UP VIEW")

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        pw = request.POST.get('pw')
        rp = request.POST.get('re-pw')

        if not username or not email or not pw or not rp:
            return render(request, "sign_up.html", {
                "error": "Tous les champs sont obligatoires"
            })

        if pw != rp:
            return render(request, "sign_up.html", {
                "error": "Les mots de passe ne correspondent pas"
            })

        try:
            validate_password(pw)
        except ValidationError as e:
            return render(request, "sign_up.html", {
                "error": e.messages[0]
            })

        if User.objects.filter(username=username).exists():
            return render(request, "sign_up.html", {
                "error": "Utilisateur déjà existant"
            })

        # Création directe (sans API)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=pw
        )
        user.save()

        return redirect("sign_in")

    return render(request, "sign_up.html")


