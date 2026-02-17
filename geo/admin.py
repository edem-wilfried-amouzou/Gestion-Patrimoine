from django.contrib import admin
from .models import patrimoine


class patrimoineAdmin(admin.ModelAdmin):
    list_display = ('nom', 'latitude', 'longitude', 'utilisateur', 'date_ajout')
    search_fields = ('nom', 'utilisateur__username')
    list_filter = ('date_ajout',)


# Register model with its ModelAdmin
admin.site.register(patrimoine, patrimoineAdmin)

