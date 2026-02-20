from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Patrimoine
from statistics import mean
from django.http import HttpResponse, JsonResponse, FileResponse
import gpxpy.gpx
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
import requests
import json
import os
from django.conf import settings
from PIL import Image as PILImage
from datetime import datetime


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


@login_required
def dashboard(request):
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

    return render(request, 'patrimoine/dashboard.html', {
        'patrimoines': patrimoines,
        'patrimoines_json': json.dumps(patrimoines_json),
        'others_patrimoines_json': json.dumps(others_json),
        'center_lat': center_lat,
        'center_lng': center_lng,
        'bounds_json': json.dumps(bounds),
    })


@login_required
def add_patrimoine(request):
    if request.method == "POST":
        try:
            nom = request.POST.get("nom")
            lat = request.POST.get("latitude")
            lng = request.POST.get("longitude")
            description = request.POST.get("description", "")
            photo = request.FILES.get("photo")

            if not nom or not lat or not lng:
                return JsonResponse({"status": "error", "message": "Tous les champs sont requis"})

            patrimoine = Patrimoine.objects.create(
                user=request.user,
                nom=nom,
                latitude=float(lat),
                longitude=float(lng),
                description=description,
                photo=photo
            )

            return JsonResponse({
                "status": "success",
                "message": "Patrimoine ajouté avec succès",
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


@login_required
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


@login_required
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


@login_required
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
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(
            latitude=p.latitude, longitude=p.longitude,
            elevation=0, name=p.nom, description=p.description
        ))
        gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(
            latitude=p.latitude, longitude=p.longitude,
            elevation=0, name=p.nom, description=p.description
        ))

    response = HttpResponse(gpx.to_xml(), content_type='application/gpx+xml')
    response['Content-Disposition'] = f'attachment; filename="patrimoines_{request.user.username}.gpx"'
    return response


@login_required
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


@login_required
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


@login_required
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


@login_required
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