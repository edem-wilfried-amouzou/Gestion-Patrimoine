#Changement de la requete de démande de sign_up 
```
 response = requests.post(
                "http://127.0.0.1:8000/api/sign_up/",
                json={
                    "username": username,
                    "email": email,
                    "password": pw
                }
            )
```
Par

``` 
response = requests.post(
    request.build_absolute_uri("/api/sign_up/"),
    json={
                    "username": username,
                    "email": email,
                    "password": pw
                }
)
```
#De même que pour sign_in 
```
response = requests.post(
            "http://127.0.0.1:8000/api/sign_in/",
            json={"username": username, "password": password}
        )
```

Devient
``` 
response = requests.post(
    request.build_absolute_uri("/api/sign_up/"),
    json={"username": username, "password": password}
)
```