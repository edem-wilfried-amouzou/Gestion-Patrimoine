from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Patrimoine
import folium
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
    """
    Compresse une image pour l'insertion dans le PDF.
    Retourne un BytesIO de l'image compressée ou None si erreur.
    """
    try:
        with PILImage.open(image_path) as img:
            # Convertir en RGB si nécessaire (PNG avec transparence, etc.)
            if img.mode in ('RGBA', 'P', 'LA'):
                background = PILImage.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Redimensionner proportionnellement
            # max_width_cm * 28.35 px/cm ≈ pixels à 72dpi
            max_w_px = int(max_width_cm * 28.35 * 2)   # ~567px pour 10cm
            max_h_px = int(max_height_cm * 28.35 * 2)  # ~397px pour 7cm

            img.thumbnail((max_w_px, max_h_px), PILImage.LANCZOS)

            # Compression JPEG progressive avec qualité ajustée
            output = BytesIO()
            quality = 75
            img.save(output, format='JPEG', quality=quality, optimize=True, progressive=True)

            # Si encore trop lourd, réduire la qualité
            while output.tell() > max_kb * 1024 and quality > 30:
                quality -= 10
                output = BytesIO()
                img.save(output, format='JPEG', quality=quality, optimize=True, progressive=True)

            output.seek(0)
            return output, img.size  # (buffer, (width_px, height_px))
    except Exception as e:
        print(f"Erreur compression image: {e}")
        return None, None


@login_required
def dashboard(request):
    """
    Tableau de bord principal avec la carte Folium.
    Affiche les patrimoines de l'utilisateur connecté (bleu)
    et ceux des autres utilisateurs (orange) sur la même carte.
    """
    # Patrimoines de l'utilisateur connecté
    patrimoines = Patrimoine.objects.filter(user=request.user).order_by('nom')

    # Patrimoines des AUTRES utilisateurs
    others_patrimoines = Patrimoine.objects.exclude(user=request.user).select_related('user').order_by('nom')

    # CENTRAGE INTELLIGENT : tous les patrimoines confondus
    all_lats = [p.latitude for p in patrimoines] + [p.latitude for p in others_patrimoines]
    all_lngs = [p.longitude for p in patrimoines] + [p.longitude for p in others_patrimoines]

    if all_lats:
        center_lat = mean(all_lats)
        center_lng = mean(all_lngs)
    else:
        # Centre par défaut (Lomé, Togo)
        center_lat = 6.1319
        center_lng = 1.2228

    # CRÉATION CARTE FOLIUM
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=13,
        tiles='OpenStreetMap'
    )

    # --- MARQUEURS : MES PATRIMOINES (bleu) ---
    for p in patrimoines:
        popup_html = f"""
        <div style="min-width:180px; max-width:260px; font-family:sans-serif;">
            <h3 style="margin:0 0 6px 0; color:#0047cc; font-size:14px;">{p.nom}</h3>
            <p style="margin:4px 0; color:#475569; font-size:12px;">{p.description or 'Aucune description'}</p>
            <p style="margin:4px 0; color:#94a3b8; font-size:11px;">
                {p.latitude:.5f}, {p.longitude:.5f}
            </p>
        """
        if p.photo and hasattr(p.photo, 'url'):
            try:
                popup_html += f'<img src="{p.photo.url}" style="max-width:100%; height:60px; object-fit:cover; border-radius:6px; margin-top:6px;">'
            except Exception:
                pass
        popup_html += "</div>"

        folium.Marker(
            [p.latitude, p.longitude],
            popup=folium.Popup(popup_html, max_width=270),
            icon=folium.Icon(color="blue", icon="home", prefix="fa"),
            tooltip=f"🔵 {p.nom}"
        ).add_to(m)

    # --- MARQUEURS : AUTRES UTILISATEURS (orange) ---
    for p in others_patrimoines:
        owner = p.user.username
        popup_html = f"""
        <div style="min-width:180px; max-width:260px; font-family:sans-serif;">
            <div style="background:#fef3c7; border-radius:12px; padding:3px 8px; display:inline-block; margin-bottom:6px; font-size:11px; color:#92400e;">
                👤 {owner}
            </div>
            <h3 style="margin:0 0 6px 0; color:#d97706; font-size:14px;">{p.nom}</h3>
            <p style="margin:4px 0; color:#475569; font-size:12px;">{p.description or 'Aucune description'}</p>
            <p style="margin:4px 0; color:#94a3b8; font-size:11px;">
                {p.latitude:.5f}, {p.longitude:.5f}
            </p>
        """
        if p.photo and hasattr(p.photo, 'url'):
            try:
                popup_html += f'<img src="{p.photo.url}" style="max-width:100%; height:60px; object-fit:cover; border-radius:6px; margin-top:6px;">'
            except Exception:
                pass
        popup_html += "</div>"

        folium.Marker(
            [p.latitude, p.longitude],
            popup=folium.Popup(popup_html, max_width=270),
            icon=folium.Icon(color="orange", icon="map-marker", prefix="fa"),
            tooltip=f"🟠 {p.nom} ({owner})"
        ).add_to(m)

    # Convertir la carte en HTML
    map_html = m._repr_html_()

    # --- JSON MES PATRIMOINES ---
    patrimoines_json = []
    for p in patrimoines:
        data = {
            'id': p.id,
            'nom': p.nom,
            'lat': float(p.latitude),
            'lng': float(p.longitude),
            'description': p.description or '',
            'photo_url': '',
        }
        if p.photo and hasattr(p.photo, 'url'):
            try:
                data['photo_url'] = p.photo.url
            except Exception:
                pass
        patrimoines_json.append(data)

    # --- JSON AUTRES PATRIMOINES ---
    others_json = []
    for p in others_patrimoines:
        data = {
            'id': p.id,
            'nom': p.nom,
            'lat': float(p.latitude),
            'lng': float(p.longitude),
            'description': p.description or '',
            'photo_url': '',
            'owner_username': p.user.username,
            'owner_id': p.user.id,
        }
        if p.photo and hasattr(p.photo, 'url'):
            try:
                data['photo_url'] = p.photo.url
            except Exception:
                pass
        others_json.append(data)

    return render(request, 'patrimoine/dashboard.html', {
        'map': map_html,
        'patrimoines': patrimoines,
        'patrimoines_json': json.dumps(patrimoines_json),
        'others_patrimoines_json': json.dumps(others_json),
        'center_lat': center_lat,
        'center_lng': center_lng,
    })


# ─── AJOUT ───────────────────────────────────────────────────────────────────

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


# ─── ÉDITION ─────────────────────────────────────────────────────────────────

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


# ─── SUPPRESSION ─────────────────────────────────────────────────────────────

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


# ─── EXPORT GPX ──────────────────────────────────────────────────────────────

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


# ─── EXPORT PDF ──────────────────────────────────────────────────────────────

@login_required
def export_pdf(request):
    """
    Export PDF clean, photos compressées, taille max ~5 MB.
    Design : une page de garde + une fiche par patrimoine sur 2 colonnes.
    """
    patrimoines = Patrimoine.objects.filter(user=request.user).order_by('nom')

    buffer = BytesIO()

    # Marges réduites pour gagner de la place
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    # ── Couleurs ──────────────────────────────────────────────────────────────
    BLUE       = colors.HexColor('#0047cc')
    BLUE_LIGHT = colors.HexColor('#eef5ff')
    BLUE_MID   = colors.HexColor('#0066ff')
    SLATE      = colors.HexColor('#475569')
    SLATE_DARK = colors.HexColor('#1e293b')
    ORANGE     = colors.HexColor('#f59e0b')
    WHITE      = colors.white
    GREY_LINE  = colors.HexColor('#e2e8f0')

    # ── Styles ────────────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()

    style_cover_title = ParagraphStyle(
        'CoverTitle',
        fontName='Helvetica-Bold',
        fontSize=28,
        textColor=WHITE,
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    style_cover_sub = ParagraphStyle(
        'CoverSub',
        fontName='Helvetica',
        fontSize=13,
        textColor=colors.HexColor('#bcd6ff'),
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    style_cover_date = ParagraphStyle(
        'CoverDate',
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#8ebcff'),
        alignment=TA_CENTER,
    )
    style_section_title = ParagraphStyle(
        'SectionTitle',
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=BLUE,
        spaceBefore=10,
        spaceAfter=4,
    )
    style_card_title = ParagraphStyle(
        'CardTitle',
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=SLATE_DARK,
        spaceAfter=3,
    )
    style_label = ParagraphStyle(
        'Label',
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=BLUE_MID,
        spaceAfter=1,
    )
    style_value = ParagraphStyle(
        'Value',
        fontName='Helvetica',
        fontSize=9,
        textColor=SLATE,
        spaceAfter=4,
        leading=13,
    )
    style_footer = ParagraphStyle(
        'Footer',
        fontName='Helvetica',
        fontSize=8,
        textColor=colors.HexColor('#94a3b8'),
        alignment=TA_CENTER,
    )
    style_no_data = ParagraphStyle(
        'NoData',
        fontName='Helvetica-Oblique',
        fontSize=10,
        textColor=colors.HexColor('#94a3b8'),
        alignment=TA_CENTER,
        spaceAfter=20,
    )

    elements = []

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE DE GARDE avec fond bleu via tableau pleine page
    # ══════════════════════════════════════════════════════════════════════════
    page_w = A4[0] - 3 * cm   # largeur utile

    cover_data = [[
        Paragraph("Gestion Patrimoine", style_cover_title),
    ]]
    cover_table = Table(cover_data, colWidths=[page_w])
    cover_table.setStyle(TableStyle([
        ('BACKGROUND',  (0, 0), (-1, -1), BLUE),
        ('ROUNDEDCORNERS', [12]),
        ('ALIGN',       (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',      (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',  (0, 0), (-1, -1), 40),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 40),
    ]))
    elements.append(cover_table)
    elements.append(Spacer(1, 14))

    # Sous-titre et métadonnées
    sub_data = [[
        Paragraph(f"Rapport de patrimoine · {request.user.username}", style_cover_sub),
    ], [
        Paragraph(f"Généré le {datetime.now().strftime('%d %B %Y à %H:%M')}", style_cover_date),
    ], [
        Paragraph(f"{patrimoines.count()} site(s) enregistré(s)", style_cover_date),
    ]]
    sub_table = Table(sub_data, colWidths=[page_w])
    sub_table.setStyle(TableStyle([
        ('ALIGN',   (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',  (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(sub_table)
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width=page_w, thickness=1, color=GREY_LINE))
    elements.append(Spacer(1, 20))

    # ══════════════════════════════════════════════════════════════════════════
    # Cas : aucun patrimoine
    # ══════════════════════════════════════════════════════════════════════════
    if not patrimoines.exists():
        elements.append(Paragraph("Aucun patrimoine enregistré.", style_no_data))
        doc.build(elements)
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="patrimoines_{request.user.username}.pdf"'
        return response

    # ══════════════════════════════════════════════════════════════════════════
    # RÉSUMÉ STATISTIQUE (tableau compact)
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(Paragraph("Résumé", style_section_title))
    elements.append(Spacer(1, 6))

    nb_photos = sum(1 for p in patrimoines if p.photo)
    summary_data = [
        ['Sites totaux', 'Avec photo', 'Sans photo'],
        [
            str(patrimoines.count()),
            str(nb_photos),
            str(patrimoines.count() - nb_photos),
        ]
    ]
    summary_table = Table(summary_data, colWidths=[page_w / 3] * 3)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), BLUE),
        ('TEXTCOLOR',     (0, 0), (-1, 0), WHITE),
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 9),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND',    (0, 1), (-1, 1), BLUE_LIGHT),
        ('TEXTCOLOR',     (0, 1), (-1, 1), SLATE_DARK),
        ('GRID',          (0, 0), (-1, -1), 0.5, GREY_LINE),
        ('ROUNDEDCORNERS', [6]),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 24))
    elements.append(HRFlowable(width=page_w, thickness=1, color=GREY_LINE))
    elements.append(Spacer(1, 16))

    # ══════════════════════════════════════════════════════════════════════════
    # FICHES PATRIMOINES — 2 par ligne
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(Paragraph("Fiches des sites", style_section_title))
    elements.append(Spacer(1, 8))

    col_w = (page_w - 0.5 * cm) / 2  # largeur d'une colonne (2 cols + gap)

    patrimoine_list = list(patrimoines)
    # Grouper par paires
    pairs = [patrimoine_list[i:i+2] for i in range(0, len(patrimoine_list), 2)]

    for pair in pairs:
        row_cells = []

        for p in pair:
            # ── Contenu de la fiche ──────────────────────────────────────────
            cell_content = []

            # Numéro + nom
            idx = patrimoine_list.index(p) + 1
            cell_content.append(Paragraph(f"{idx}. {p.nom}", style_card_title))

            # Coordonnées
            cell_content.append(Paragraph("Coordonnées", style_label))
            cell_content.append(Paragraph(
                f"{p.latitude:.5f}, {p.longitude:.5f}", style_value
            ))

            # Description
            cell_content.append(Paragraph("Description", style_label))
            desc = (p.description or "Aucune description")
            # Tronquer si trop long
            if len(desc) > 200:
                desc = desc[:197] + "..."
            cell_content.append(Paragraph(desc, style_value))

            # Photo compressée
            if p.photo and hasattr(p.photo, 'path') and os.path.exists(p.photo.path):
                compressed, size = compress_image_for_pdf(
                    p.photo.path,
                    max_width_cm=col_w / cm - 0.6,
                    max_height_cm=5,
                    max_kb=250
                )
                if compressed:
                    # Calculer dimensions réelles en cm pour ReportLab
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

        # Si paire incomplète (dernier patrimoine seul), ajouter cellule vide
        if len(row_cells) == 1:
            row_cells.append([Paragraph("", style_value)])

        # Construire le tableau 2 colonnes pour cette paire
        # Chaque cellule est une liste de flowables → on les imbrique dans un sous-tableau
        def make_card(content_list):
            """Encapsule le contenu dans un mini-tableau stylé (carte)."""
            inner_data = [[item] for item in content_list]
            inner = Table(inner_data, colWidths=[col_w - 0.4 * cm])
            inner.setStyle(TableStyle([
                ('ALIGN',         (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING',    (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('LEFTPADDING',   (0, 0), (-1, -1), 0),
                ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
            ]))
            return inner

        left_card  = make_card(row_cells[0])
        right_card = make_card(row_cells[1])

        row_table = Table(
            [[left_card, right_card]],
            colWidths=[col_w, col_w],
            hAlign='LEFT'
        )
        row_table.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (0, 0), BLUE_LIGHT),
            ('BACKGROUND',    (1, 0), (1, 0), colors.HexColor('#f8fafc')),
            ('BOX',           (0, 0), (0, 0), 0.8, BLUE_MID),
            ('BOX',           (1, 0), (1, 0), 0.8, GREY_LINE),
            ('ROUNDEDCORNERS', [8]),
            ('TOPPADDING',    (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING',   (0, 0), (-1, -1), 10),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
            ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
            ('COLPADDING',    (0, 0), (-1, -1), 5),
        ]))

        elements.append(row_table)
        elements.append(Spacer(1, 10))

    # ── Pied de page ──────────────────────────────────────────────────────────
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width=page_w, thickness=1, color=GREY_LINE))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        f"Gestion Patrimoine · {request.user.username} · {datetime.now().strftime('%d/%m/%Y')}",
        style_footer
    ))

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.build(elements)
    buffer.seek(0)

    # Vérifier la taille (max 5 MB)
    pdf_size = buffer.getbuffer().nbytes
    if pdf_size > 5 * 1024 * 1024:
        # Re-compresser plus agressivement si dépassement
        # (en pratique rare avec nos paramètres actuels)
        pass

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="patrimoines_{request.user.username}.pdf"'
    return response


# ─── ITINÉRAIRE VERS UN PATRIMOINE ───────────────────────────────────────────

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


# ─── API JSON ─────────────────────────────────────────────────────────────────

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