from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse, FileResponse
from django.contrib.auth.models import User
from django.core.mail import send_mail, EmailMessage
from datetime import timedelta
from http.client import responses
from django.utils import timezone
from .models import SignInAttempt, Patrimoine
from statistics import mean
import gpxpy.gpx
import requests
import folium
import random
from django.conf import settings
from .forms import PatrimoineForm
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from io import BytesIO
import requests
import json
import os
from django.conf import settings
from PIL import Image as PILImage
from datetime import datetime

from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError



def home(request):
    return render(request, 'home.html', {})

#---------------------------------------Sign_in---------------------------------------------------

MAX_ATTEMPTS = 3

def Sign_in(request):
    print("SIGN in VIEW")

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Appel API
        response = requests.post(
            "https://gestion-patrimoine-b3hj.onrender.com/api/sign_in/",
            json={"username": username, "password": password}
        )

        # Tenter d'authentifier l'utilisateur localement
        user = authenticate(request, username=username, password=password)

        if response.status_code == 200 and user is not None:
            # Login OK
            if not user.is_active:
                return render(request, 'sign_in.html', {"error": "Compte bloqué, contactez l'administrateur."})

            # Reset tentatives
            attempt, created = SignInAttempt.objects.get_or_create(user=user)
            attempt.attempt = 0
            attempt.save()

            login(request, user)
            request.session["access_token"] = response.json().get("access_token")
            request.session["username"] = username
            request.session["login_time"] = timezone.now().isoformat()  # ✅ Ajouter
            request.session.save()
            return redirect('dash')

        elif response.status_code == 401:
            # username correct, password incorrect
            try:
                user_obj = User.objects.get(username=username)
                attempt, created = SignInAttempt.objects.get_or_create(user=user_obj)
                attempt.attempt += 1
                attempt.save()
                essais_restants = MAX_ATTEMPTS - attempt.attempt

                if essais_restants <= 0:
                    attempt.attempt=0
                    attempt.save()
                    # Blocage du compte
                    user_obj.is_active = False
                    user_obj.save()
                    admin_emails = list(User.objects.filter(is_superuser=True).values_list('email', flat=True))
                    print(admin_emails)
                    if admin_emails:
                        try:
                            email = EmailMessage(
                                subject=f'ALERTE : Utilisateur {user_obj.username} bloqué',                                body=f"Suite a 3 tentetives echoue, l'utilisateur a ete bloque",
                                from_email=settings.EMAIL_HOST_USER,
                                to=admin_emails
                            )
                            email.send(fail_silently=False)
                            print(f"Notification envoyée aux admins : {admin_emails}")

                        except Exception as e:
                            print(f"Erreur notification admin : {e}")
                    return render(request, 'sign_in.html',
                                  {"error": "Votre compte est bloqué, contactez l'administrateur.",
                                   "blocked": 1})
                else:
                    return render(request, 'sign_in.html',
                                  {"error": f"Login incorrect. {essais_restants} essais restants."})
            except User.DoesNotExist:
                # Le username n'existe pas, mais on le gère côté API
                return render(request, 'sign_in.html', {"error": "Login invalide."})

        elif response.status_code == 400:
            # username invalide
            return render(request, 'sign_in.html', {"error": "Login invalide."})

        else:
            return render(request, 'sign_in.html', {"error": "Erreur de connexion, réessayez."})

    return render(request, "sign_in.html")

# ---------------------------------Sign_up---------------------------------------------------

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
                "https://gestion-patrimoine-b3hj.onrender.com/api/sign_up/",
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
                subject = "Bienvenue sur Gestion Patrimoine !"
                message = f"""
                        Bonjour {username},

                        Merci de vous être inscrit sur notre plateforme Gestion Patrimoine.
                        Votre compte a été créé avec succès.

                        Vous pouvez maintenant vous connecter en utilisant votre nom d'utilisateur : {username}

                        Lien de connexion : {request.build_absolute_uri('/sign_in/')}

                        À bientôt !
                        L'équipe de Gestion Patrimoine.
                        """
                try:
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],  # L'email saisi dans le formulaire
                        fail_silently=False,
                    )
                except Exception as e:
                    print(f"Erreur envoi mail inscription : {e}")
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

# -----------------------------------------logout---------------------------------------------------

def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('home')

# ------------------------------------------Dashboard---------------------------------------------------

# @login_required
def UserDash(request):
    patrimoines = Patrimoine.objects.filter(user=request.user).order_by('nom')
    others_patrimoines = Patrimoine.objects.exclude(user=request.user)\
                                          .select_related('user')\
                                          .order_by('nom')

    all_points = list(patrimoines) + list(others_patrimoines)

    if all_points:
        lats = [p.latitude for p in all_points]
        lngs = [p.longitude for p in all_points]

        bounds = {
            "min_lat": min(lats),
            "max_lat": max(lats),
            "min_lng": min(lngs),
            "max_lng": max(lngs),
        }

        center_lat = sum(lats) / len(lats)
        center_lng = sum(lngs) / len(lngs)

    else:
        bounds = None
        center_lat = 6.1319
        center_lng = 1.2228

    # JSON mes patrimoines
    patrimoines_json = []
    for p in patrimoines:
        patrimoines_json.append({
            'id': p.id,
            'nom': p.nom,
            'lat': float(p.latitude),
            'lng': float(p.longitude),
            'description': p.description or '',
            'photo_url': p.photo.url if p.photo else '',
        })

    # JSON autres patrimoines
    others_json = []
    for p in others_patrimoines:
        others_json.append({
            'id': p.id,
            'nom': p.nom,
            'lat': float(p.latitude),
            'lng': float(p.longitude),
            'description': p.description or '',
            'photo_url': p.photo.url if p.photo else '',
            'owner_username': p.user.username,
            'owner_id': p.user.id,
        })

    return render(request, 'board.html', {
        'patrimoines': patrimoines,
        'patrimoines_json': json.dumps(patrimoines_json),
        'others_patrimoines_json': json.dumps(others_json),
        'center_lat': center_lat,
        'center_lng': center_lng,
        'bounds_json': json.dumps(bounds),
    })



# ---------------------------------------------------------Add---------------------------------------------------

def Add(request):
    if request.method == "POST":
        form = PatrimoineForm(request.POST, request.FILES)
        if form.is_valid():
            patrimoine = form.save(commit=False)
            patrimoine.user = request.user

            patrimoine.save()
            return redirect('dash')
        else:
            # Si le formulaire n'est pas valide, réafficher avec erreurs
            carte = folium.Map(location=[14.7, -17.4], zoom_start=6)
            carte_html = carte._repr_html_()
            context = {
                'form': form,
                'carte': carte_html
            }
            return render(request, 'add.html', context)
    
    # GET request - afficher le formulaire vide
    form = PatrimoineForm()
    carte = folium.Map(location=[14.7, -17.4], zoom_start=6)
    carte_html = carte._repr_html_()
    context = {
        'form': form,
        'carte': carte_html
    }
    return render(request, 'add.html', context)

# def Add(request):
#     form = PatrimoineForm
#     carte = folium.Map(location=[14.7, -17.4],zoom_start=6)
#     carte_html = carte.repr_html()
#     context = {
#         'form':form,
#         'carte':carte_html
#     }
#     return render(request,'geo/ajouter.html',context)


# -----------------------------------------Edit---------------------------------------------------
# @login_required
def edit_patrimoine(request, patrimoine_id):
    patrimoine = get_object_or_404(Patrimoine, id=patrimoine_id, user=request.user)

    if request.method == "POST":
        try:
            nom = request.POST.get("nom")
            lat = request.POST.get("latitude")
            lng = request.POST.get("longitude")
            description = request.POST.get("description", "")
            photo = request.FILES.get("photo")

            if not nom:
                return JsonResponse({"status": "error", "message": "Le nom est requis"})

            patrimoine.nom = nom
            patrimoine.description = description

            if lat and lng:
                patrimoine.latitude = float(lat)
                patrimoine.longitude = float(lng)

            if photo:
                if patrimoine.photo:
                    try:
                        if os.path.isfile(patrimoine.photo.path):
                            os.remove(patrimoine.photo.path)
                    except Exception:
                        pass
                patrimoine.photo = photo

            patrimoine.save()

            return JsonResponse({
                "status": "success",
                "message": "Patrimoine modifié avec succès",
                "patrimoine": {
                    "id": patrimoine.id,
                    "nom": patrimoine.nom,
                    "lat": float(patrimoine.latitude),
                    "lng": float(patrimoine.longitude),
                    "description": patrimoine.description,
                    "photo_url": patrimoine.photo.url if patrimoine.photo else ""
                }
            })
        except ValueError:
            return JsonResponse({"status": "error", "message": "Coordonnées invalides"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Méthode non autorisée"})


# ---------------------------------------------------------Delete---------------------------------------------------
# @login_required
def delete_patrimoine(request, patrimoine_id):
    patrimoine = get_object_or_404(Patrimoine, id=patrimoine_id, user=request.user)

    if request.method == "POST":
        try:
            if patrimoine.photo:
                try:
                    if os.path.isfile(patrimoine.photo.path):
                        os.remove(patrimoine.photo.path)
                except Exception:
                    pass
            patrimoine.delete()
            return JsonResponse({"status": "success", "message": "Patrimoine supprimé avec succès"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Méthode non autorisée"})


# ---------------------------------------------Export GPX---------------------------------------------------

# @login_required
def export_gpx(request):
    patrimoines = Patrimoine.objects.filter(user=request.user)

    if not patrimoines.exists():
        return HttpResponse("Aucun patrimoine à exporter", status=404)

    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    for p in patrimoines:
        gpx_segment.points.append(
        gpxpy.gpx.GPXTrackPoint(
            latitude=p.latitude,
            longitude=p.longitude,
            elevation=0
        )
    )


    gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(
        latitude=p.latitude,
        longitude=p.longitude,
        elevation=0,
        name=p.nom,
        description=p.description
    ))


    response = HttpResponse(gpx.to_xml(), content_type='application/gpx+xml')
    response['Content-Disposition'] = f'attachment; filename="patrimoines_{request.user.username}.gpx"'
    return response


def send_gpx_email(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Authentification requise'}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8'))
        recipient = data.get('email')
    except Exception:
        recipient = request.POST.get('email')

    if not recipient:
        return JsonResponse({'status': 'error', 'message': "Adresse e-mail manquante"}, status=400)

    patrimoines = Patrimoine.objects.filter(user=request.user)
    if not patrimoines.exists():
        return JsonResponse({'status': 'error', 'message': "Aucun patrimoine à exporter"}, status=404)

    # Générer GPX
    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    for p in patrimoines:
        gpx_segment.points.append(
            gpxpy.gpx.GPXTrackPoint(latitude=p.latitude, longitude=p.longitude, elevation=0)
        )

        gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(
            latitude=p.latitude,
            longitude=p.longitude,
            elevation=0,
            name=p.nom,
            description=p.description
        ))

    gpx_bytes = gpx.to_xml().encode('utf-8')
    filename = f'patrimoines_{request.user.username}.gpx'

    try:
        email = EmailMessage(
            subject=f'GPX - Patrimoines de {request.user.username}',
            body=f'Veuillez trouver en pièce jointe le fichier GPX contenant vos patrimoines.',
            from_email=settings.EMAIL_HOST_USER,
            to=[recipient]
        )
        email.attach(filename, gpx_bytes, 'application/gpx+xml')
        email.send(fail_silently=False)
        return JsonResponse({'status': 'success', 'message': 'E-mail envoyé'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


# ---------------------------------------------compress_image_for_pdf---------------------------------------------------

def compress_image_for_pdf(image_path, max_width_cm=10, max_height_cm=7, max_kb=300):
    try:
        with PILImage.open(image_path) as img:
            if img.mode in ('RGBA', 'P', 'LA'):
                background = PILImage.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            max_w_px = int(max_width_cm * 28.35 * 2)
            max_h_px = int(max_height_cm * 28.35 * 2)
            img.thumbnail((max_w_px, max_h_px), PILImage.LANCZOS)

            output = BytesIO()
            quality = 75
            img.save(output, format='JPEG', quality=quality, optimize=True, progressive=True)

            while output.tell() > max_kb * 1024 and quality > 30:
                quality -= 10
                output = BytesIO()
                img.save(output, format='JPEG', quality=quality, optimize=True, progressive=True)

            output.seek(0)
            return output, img.size
    except Exception as e:
        print(f"Erreur compression image: {e}")
        return None, None
    
# ----------------------------------------------Export PDF---------------------------------------------------
def export_pdf(request):
    patrimoines = Patrimoine.objects.filter(user=request.user).order_by('nom')
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    BLUE       = colors.HexColor('#0047cc')
    BLUE_LIGHT = colors.HexColor('#eef5ff')
    BLUE_MID   = colors.HexColor('#0066ff')
    SLATE      = colors.HexColor('#475569')
    SLATE_DARK = colors.HexColor('#1e293b')
    WHITE      = colors.white
    GREY_LINE  = colors.HexColor('#e2e8f0')

    styles = getSampleStyleSheet()

    style_cover_title = ParagraphStyle('CoverTitle', fontName='Helvetica-Bold', fontSize=28, textColor=WHITE, alignment=TA_CENTER, spaceAfter=6)
    style_cover_sub   = ParagraphStyle('CoverSub', fontName='Helvetica', fontSize=13, textColor=colors.HexColor('#bcd6ff'), alignment=TA_CENTER, spaceAfter=4)
    style_cover_date  = ParagraphStyle('CoverDate', fontName='Helvetica', fontSize=10, textColor=colors.HexColor('#8ebcff'), alignment=TA_CENTER)
    style_section_title = ParagraphStyle('SectionTitle', fontName='Helvetica-Bold', fontSize=14, textColor=BLUE, spaceBefore=10, spaceAfter=4)
    style_card_title  = ParagraphStyle('CardTitle', fontName='Helvetica-Bold', fontSize=11, textColor=SLATE_DARK, spaceAfter=3)
    style_label       = ParagraphStyle('Label', fontName='Helvetica-Bold', fontSize=8, textColor=BLUE_MID, spaceAfter=1)
    style_value       = ParagraphStyle('Value', fontName='Helvetica', fontSize=9, textColor=SLATE, spaceAfter=4, leading=13)
    style_footer      = ParagraphStyle('Footer', fontName='Helvetica', fontSize=8, textColor=colors.HexColor('#94a3b8'), alignment=TA_CENTER)
    style_no_data     = ParagraphStyle('NoData', fontName='Helvetica-Oblique', fontSize=10, textColor=colors.HexColor('#94a3b8'), alignment=TA_CENTER, spaceAfter=20)

    elements = []
    page_w = A4[0] - 3 * cm

    cover_data = [[Paragraph("Gestion Patrimoine", style_cover_title)]]
    cover_table = Table(cover_data, colWidths=[page_w])
    cover_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BLUE),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 40),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 40),
    ]))
    elements.append(cover_table)
    elements.append(Spacer(1, 14))

    sub_data = [
        [Paragraph(f"Rapport de patrimoine · {request.user.username}", style_cover_sub)],
        [Paragraph(f"Généré le {datetime.now().strftime('%d %B %Y à %H:%M')}", style_cover_date)],
        [Paragraph(f"{patrimoines.count()} site(s) enregistré(s)", style_cover_date)],
    ]
    sub_table = Table(sub_data, colWidths=[page_w])
    sub_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(sub_table)
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width=page_w, thickness=1, color=GREY_LINE))
    elements.append(Spacer(1, 20))

    if not patrimoines.exists():
        elements.append(Paragraph("Aucun patrimoine enregistré.", style_no_data))
        doc.build(elements)
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="patrimoines_{request.user.username}.pdf"'
        return response

    elements.append(Paragraph("Résumé", style_section_title))
    elements.append(Spacer(1, 6))

    nb_photos = sum(1 for p in patrimoines if p.photo)
    summary_data = [
        ['Sites totaux', 'Avec photo', 'Sans photo'],
        [str(patrimoines.count()), str(nb_photos), str(patrimoines.count() - nb_photos)],
    ]
    summary_table = Table(summary_data, colWidths=[page_w / 3] * 3)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, 1), BLUE_LIGHT),
        ('TEXTCOLOR', (0, 1), (-1, 1), SLATE_DARK),
        ('GRID', (0, 0), (-1, -1), 0.5, GREY_LINE),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 24))
    elements.append(HRFlowable(width=page_w, thickness=1, color=GREY_LINE))
    elements.append(Spacer(1, 16))

    elements.append(Paragraph("Fiches des sites", style_section_title))
    elements.append(Spacer(1, 8))

    col_w = (page_w - 0.5 * cm) / 2
    patrimoine_list = list(patrimoines)
    pairs = [patrimoine_list[i:i+2] for i in range(0, len(patrimoine_list), 2)]

    for pair in pairs:
        row_cells = []

        for p in pair:
            cell_content = []
            idx = patrimoine_list.index(p) + 1
            cell_content.append(Paragraph(f"{idx}. {p.nom}", style_card_title))
            cell_content.append(Paragraph("Coordonnées", style_label))
            cell_content.append(Paragraph(f"{p.latitude:.5f}, {p.longitude:.5f}", style_value))
            cell_content.append(Paragraph("Description", style_label))
            desc = (p.description or "Aucune description")
            if len(desc) > 200:
                desc = desc[:197] + "..."
            cell_content.append(Paragraph(desc, style_value))

            if p.photo and hasattr(p.photo, 'path') and os.path.exists(p.photo.path):
                compressed, size = compress_image_for_pdf(p.photo.path, max_width_cm=col_w / cm - 0.6, max_height_cm=5, max_kb=250)
                if compressed:
                    if size:
                        ratio = size[0] / size[1]
                        img_w = min(col_w - 0.5 * cm, 9 * cm)
                        img_h = img_w / ratio
                        if img_h > 5 * cm:
                            img_h = 5 * cm
                            img_w = img_h * ratio
                    else:
                        img_w, img_h = 7 * cm, 5 * cm
                    try:
                        rl_img = RLImage(compressed, width=img_w, height=img_h)
                        cell_content.append(Spacer(1, 4))
                        cell_content.append(rl_img)
                    except Exception:
                        cell_content.append(Paragraph("(Photo non disponible)", style_value))
                else:
                    cell_content.append(Paragraph("(Photo non disponible)", style_value))
            else:
                cell_content.append(Paragraph("Aucune photo", style_value))

            row_cells.append(cell_content)

        if len(row_cells) == 1:
            row_cells.append([Paragraph("", style_value)])

        def make_card(content_list):
            inner_data = [[item] for item in content_list]
            inner = Table(inner_data, colWidths=[col_w - 0.4 * cm])
            inner.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ]))
            return inner

        left_card  = make_card(row_cells[0])
        right_card = make_card(row_cells[1])

        row_table = Table([[left_card, right_card]], colWidths=[col_w, col_w], hAlign='LEFT')
        row_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), BLUE_LIGHT),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (0, 0), 0.8, BLUE_MID),
            ('BOX', (1, 0), (1, 0), 0.8, GREY_LINE),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        elements.append(row_table)
        elements.append(Spacer(1, 10))

    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width=page_w, thickness=1, color=GREY_LINE))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        f"Gestion Patrimoine · {request.user.username} · {datetime.now().strftime('%d/%m/%Y')}",
        style_footer
    ))

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="patrimoines_{request.user.username}.pdf"'
    return response


def send_pdf_email(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Authentification requise'}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8'))
        recipient = data.get('email')
    except Exception:
        recipient = request.POST.get('email')

    if not recipient:
        return JsonResponse({'status': 'error', 'message': "Adresse e-mail manquante"}, status=400)

    try:
        # Reuse export_pdf to build the PDF response and get bytes
        resp = export_pdf(request)
        pdf_bytes = resp.content
        filename = f'patrimoines_{request.user.username}.pdf'

        email = EmailMessage(
            subject=f'PDF - Patrimoines de {request.user.username}',
            body=f'Veuillez trouver en pièce jointe le rapport PDF contenant vos patrimoines.',
            from_email=settings.EMAIL_HOST_USER,
            to=[recipient]
        )
        email.attach(filename, pdf_bytes, 'application/pdf')
        email.send(fail_silently=False)
        return JsonResponse({'status': 'success', 'message': 'E-mail envoyé'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

# --------------------------Itinéraire vers patrimoine-------------------------------------------

def itinerary_to_patrimoine(request):
    if request.method == "POST":
        try:
            patrimoine_id = request.POST.get("patrimoine_id")
            start_lat = request.POST.get("start_lat")
            start_lng = request.POST.get("start_lng")
            mode = request.POST.get("mode", "driving")

            if not all([patrimoine_id, start_lat, start_lng]):
                return JsonResponse({"status": "error", "message": "Paramètres manquants"})

            patrimoine = get_object_or_404(Patrimoine, id=patrimoine_id, user=request.user)

            if mode not in ['driving', 'walking', 'cycling']:
                mode = 'driving'

            osrm_url = (
                f"https://router.project-osrm.org/route/v1/{mode}/"
                f"{start_lng},{start_lat};{patrimoine.longitude},{patrimoine.latitude}"
                f"?overview=full&geometries=geojson"
            )
            resp = requests.get(osrm_url, timeout=10)
            data = resp.json()

            if data.get('code') == 'Ok':
                route = data['routes'][0]
                return JsonResponse({
                    "status": "success",
                    "route": {
                        "geometry": route['geometry'],
                        "distance": route['distance'],
                        "duration": route['duration'],
                        "destination": {
                            "id": patrimoine.id,
                            "nom": patrimoine.nom,
                            "lat": float(patrimoine.latitude),
                            "lng": float(patrimoine.longitude),
                            "description": patrimoine.description,
                            "photo_url": patrimoine.photo.url if patrimoine.photo else ""
                        }
                    }
                })
            else:
                return JsonResponse({"status": "error", "message": "Impossible de calculer l'itinéraire"})

        except requests.exceptions.Timeout:
            return JsonResponse({"status": "error", "message": "Timeout du service de routage"})
        except requests.exceptions.RequestException:
            return JsonResponse({"status": "error", "message": "Erreur de connexion au service de routage"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Méthode non autorisée"})

# ------------------------Iti multiples -------------------------------
def itinerary_multi(request):
    """Calcule un itinéraire multi-points via OSRM."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            points = data.get('points', [])  # [{lat, lng}, ...]
            mode = data.get('mode', 'driving')

            if len(points) < 2:
                return JsonResponse({"status": "error", "message": "Au moins 2 points requis"})

            if mode not in ['driving', 'walking', 'cycling']:
                mode = 'driving'

            coords = ';'.join(f"{p['lng']},{p['lat']}" for p in points)
            osrm_url = (
                f"https://router.project-osrm.org/route/v1/{mode}/{coords}"
                f"?overview=full&geometries=geojson"
            )
            resp = requests.get(osrm_url, timeout=10)
            result = resp.json()

            if result.get('code') == 'Ok':
                route = result['routes'][0]
                return JsonResponse({
                    "status": "success",
                    "geometry": route['geometry'],
                    "distance": route['distance'],
                    "duration": route['duration'],
                })
            else:
                return JsonResponse({"status": "error", "message": "Impossible de calculer l'itinéraire"})

        except requests.exceptions.Timeout:
            return JsonResponse({"status": "error", "message": "Timeout"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Méthode non autorisée"})

# --------------------------------------------Get Patrimoines JSON---------------------------------------------------


def get_patrimoines_json(request):
    patrimoines = Patrimoine.objects.filter(user=request.user)
    data = []
    for p in patrimoines:
        item = {
            'id': p.id,
            'nom': p.nom,
            'lat': float(p.latitude),
            'lng': float(p.longitude),
            'description': p.description or '',
            'photo_url': '',
        }
        if p.photo and hasattr(p.photo, 'url'):
            try:
                item['photo_url'] = p.photo.url
            except Exception:
                pass
        data.append(item)
    return JsonResponse(data, safe=False)

# ---------------------------Reset password---------------------------------------------------

User = get_user_model()

def password_reset_request(request):
    if request.method == "POST":
        email = request.POST.get("email")

        # On ne révèle jamais si l'email existe ou pas
        try:
            user = User.objects.get(email=email)

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            reset_link = request.build_absolute_uri(
                reverse("password_reset_confirm", kwargs={
                    "uidb64": uid,
                    "token": token
                })
            )

            send_mail(
                subject="Réinitialisation de votre mot de passe",
                message=f"""
Bonjour {user.username},

Cliquez sur le lien ci-dessous pour réinitialiser votre mot de passe :

{reset_link}

Ce lien expire dans 1 heure.
""",
                from_email="gestpat99@gmail.com",
                recipient_list=[email],
            )

        except User.DoesNotExist:
            return render(request, "password_reset.html", {
                "error": "Mot de passe incorrect ou email non enregistré"
            })

        return render(request, "password_reset_done.html")

    return render(request, "password_reset.html")



def password_reset_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            pw1 = request.POST.get("new_pw")

            try:
                validate_password(pw1, user=user)
            except ValidationError as e:
                return render(request, "password_reset_confirm.html", {
                    "error": e.messages[0]
                })
            if True:
                user.set_password(pw1)
                user.save()
                return redirect("sign_in")

        # GET: afficher le formulaire de réinitialisation sans message d'erreur
        return render(request, "password_reset_confirm.html", {
            "uidb64": uidb64,
            "token": token
        })
    return render(request, "password_reset_invalid.html")

# ---------------------------------------------------------------------------------------------------------

from django import forms

Villes = [
    ("Lome", "Lomé"),
    ("Kara", "Kara"),
    ("Sokode", "Sokodé"),
    ("Atakpame", "Atakpamé"),
    ("Kpalime", "Kpalimé"),
    ("Aneho", "Aného"),
    ("Tsevie", "Tsévié"),
    ("Dapaong", "Dapaong"),
    ("Bassar", "Bassar"),
    ("Notse", "Notsé"),
    ("Badou", "Badou"),
]

class PatrimoineForm(forms.ModelForm):

    polygone = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

    gpx_file = forms.FileField(
       required=False,
       label="Importer un fichier GPX"
   )
   
    ville = forms.ChoiceField(
        choices=Villes,
        required=True,
        label="Ville",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Patrimoine
        fields = [ 'ville','nom', 'latitude', 'longitude','gpx_file', 'photo']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du patrimoine'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001'
            }),
        }
    
    def clean(self):
        """Validation personnalisée du formulaire"""
        cleaned_data = super().clean()
        lat = cleaned_data.get('latitude')
        lng = cleaned_data.get('longitude')
        
        # Vérifier que les coordonnées sont valides
        if lat is not None and lng is not None:
            if not (-90 <= lat <= 90):
                self.add_error('latitude', 'La latitude doit être entre -90 et 90')
            if not (-180 <= lng <= 180):
                self.add_error('longitude', 'La longitude doit être entre -180 et 180')
        
        return cleaned_data



def contAD(request):
    if request.method == 'POST':
        username = request.POST.get('username')

        try:
            user_obj = User.objects.get(username=username)
            admin_emails = list(User.objects.filter(is_superuser=True).values_list('email', flat=True))

            if admin_emails:
                subject = f"Demande de déblocage de compte : {username}"
                body = f"""
                L'utilisateur {username} ({user_obj.email}) vient de cliquer sur le bouton de demande de déblocage.
                
                Son compte a été suspendu après plusieurs tentatives infructueuses.
                Vous pouvez le réactiver ici : {request.build_absolute_uri('/admin/')}
                """

                send_mail(
                    subject,
                    body,
                    settings.EMAIL_HOST_USER,
                    admin_emails,
                    fail_silently=False
                )
                print("df")
                redirect("sign_in.html")
                # On informe l'utilisateur que c'est fait
                return render(request, 'sign_in.html', {
                    "success": "L'administrateur a été notifié de votre demande."
                })

        except User.DoesNotExist:
            return redirect('sign_in')

    return redirect('sign_in')