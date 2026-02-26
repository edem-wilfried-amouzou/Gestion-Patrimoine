# Objectif : Supprimer les appels http recursifs internes

    Ces appels (request.post()) créent des loop occupant la mémoire et en mode free sur render. Nous devons éviter ceci au maximumm
    Solution 1 : Séparer l'api du projet et le mettre en module.
    Solution 2 : Garder mais ne pas l'utiliser en faisant la vérification simple par User.Objects.filter

    Dans mon cas : Moi daniel j'ai opté pour le 2

# Changement de nos gest_Pat_App sign_in

```
def Sign_in(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not user.is_active:
                return render(request, 'sign_in.html', {"error": "Compte bloqué, contactez l'administrateur."})

            # Reset tentatives
            attempt, created = SignInAttempt.objects.get_or_create(user=user)
            attempt.attempt = 0
            attempt.save()

            # Générer JWT directement sans appel HTTP
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            login(request, user)
            request.session["access_token"] = access_token
            request.session["username"] = username
            request.session.save()
            return redirect('dash')

        else:
            # Vérifier si username existe
            try:
                user_obj = User.objects.get(username=username)
                attempt, created = SignInAttempt.objects.get_or_create(user=user_obj)
                attempt.attempt += 1
                attempt.save()

                essais_restants = MAX_ATTEMPTS - attempt.attempt
                if essais_restants <= 0:
                    user_obj.is_active = False
                    user_obj.save()
                    return render(request, 'sign_in.html',
                                  {"error": "Votre compte est bloqué, contactez l'administrateur."})
                else:
                    return render(request, 'sign_in.html',
                                  {"error": f"Login incorrect. {essais_restants} essais restants."})
            except User.DoesNotExist:
                return render(request, 'sign_in.html', {"error": "Login invalide."})

    return render(request, "sign_in.html")
```

# Changement de nos gest_Pat_App sign_up

def Sign_up(request):
if request.method == 'POST':
username = request.POST.get('username')
email = request.POST.get('email')
pw = request.POST.get('pw')
rp = request.POST.get('re-pw')

        if not all([username, email, pw, rp]):
            return render(request, "sign_up.html", {"error": "Tous les champs sont obligatoires"})

        try:
            validate_password(pw)
        except ValidationError as e:
            return render(request, "sign_up.html", {"error": e.messages})

        if pw != rp:
            return render(request, "sign_up.html", {"error": "Les mots de passe ne correspondent pas"})

        if User.objects.filter(username=username).exists():
            return render(request, "sign_up.html", {"error": "Ce nom d'utilisateur existe déjà"})

        if User.objects.filter(email=email).exists():
            return render(request, "sign_up.html", {"error": "Cet email est déjà utilisé"})

        User.objects.create_user(username=username, email=email, password=pw)
        return render(request, "sign_in.html")

    return render(request, "sign_up.html")
