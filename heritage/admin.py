from django.contrib import admin
from .models import Sito, Categoria, Accessibilita, Itinerario, Tappa, Booking
@admin.register(Sito)
class SitoAdmin(admin.ModelAdmin):
    list_display = ("nome", "citta", "regione", "categoria", "anno_iscrizione")
    search_fields = ("nome", "citta", "regione", "unesco_id")
    list_filter = ("categoria", "regione")
    list_select_related = ("categoria", "accessibilita")


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)

@admin.register(Accessibilita)
class AccessibilitaAdmin(admin.ModelAdmin):
    list_display = ("sedia_a_rotelle", "ausili_visivi", "supporto_uditivo")
    list_filter = ("sedia_a_rotelle", "ausili_visivi", "supporto_uditivo")

class TappaInline(admin.TabularInline):
    model = Tappa
    extra = 1

@admin.register(Itinerario)
class ItinerarioAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    inlines = [TappaInline]

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("itinerario", "nome", "email", "data", "numero_persone", "created_at")
    list_filter = ("data", "itinerario")
    search_fields = ("nome", "email", "itinerario__nome")