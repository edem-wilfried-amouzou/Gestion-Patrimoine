from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from django.core.exceptions import ValidationError
import os


# ✅ Validation externe (plus propre)
def validation_image(image):
    if image.size > 5 * 1024 * 1024:
        raise ValidationError("L'image ne doit pas dépasser 5MB.")
    if not image.name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        raise ValidationError("Format d'image non supporté.")


class Patrimoine(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nom = models.CharField(max_length=200, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    image = models.ImageField(upload_to="patrimoine/", null=True, blank=True)
    polygone = models.JSONField(blank=True, null=True)  
    date_creation = models.DateTimeField(auto_now_add=True)
    date_update = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Patrimoine'
        verbose_name_plural = 'Patrimoines'
        db_table = 'patrmoine'

    def __str__(self):
        return self.nom


class ImagePatrimoine(models.Model):

    patrimoine = models.ForeignKey(
        "Patrimoine",
        on_delete=models.CASCADE,
        related_name="images"
    )

    image_originale = models.ImageField(
        upload_to="patrimoines/original/",
        validators=[validation_image]
    )

    image_hd = models.ImageField(
        upload_to="patrimoines/hd/",
        blank=True,
        null=True
    )

    miniature = models.ImageField(
        upload_to="patrimoines/mini/",
        blank=True,
        null=True
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.image_originale:
            return

        try:
            img = Image.open(self.image_originale.path)
            img.verify()
        except Exception:
            raise ValidationError("Image invalide ou corrompue")

        # ⚠️ Réouvrir après verify
        img = Image.open(self.image_originale.path)

        # 🔵 HD
        img_hd = img.copy()
        img_hd.thumbnail((1600, 1600))

        hd_path = self.image_originale.path.replace("original", "hd")
        os.makedirs(os.path.dirname(hd_path), exist_ok=True)
        img_hd.save(hd_path, quality=85, optimize=True)

        # 🟢 MINI
        img_thumb = img.copy()
        img_thumb.thumbnail((300, 300))

        thumb_path = self.image_originale.path.replace("original", "mini")
        os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
        img_thumb.save(thumb_path, quality=75, optimize=True)

        self.image_hd.name = self.image_originale.name.replace("original", "hd")
        self.miniature.name = self.image_originale.name.replace("original", "mini")

        super().save(update_fields=["image_hd", "miniature"])