from django.contrib import admin
from django.urls import path, include
from heritage.views import home, siti_geojson, itinerario_geojson, ItinerarioListView, itinerario_dettaglio, toggle_prenotazione
from heritage.views import BookingCreateView
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("api/sites.geojson", siti_geojson, name="sites_geojson"),
    path("api/itinerario/<int:pk>.geojson", itinerario_geojson, name="itinerario_geojson"),
    path("itinerari/", ItinerarioListView.as_view(), name="itinerari_list"),
    path("itinerari/<int:pk>/", itinerario_dettaglio, name="itinerario_dettaglio"),
    path("itinerari/<int:pk>/toggle-prenota/", toggle_prenotazione, name="toggle_prenotazione"),
    path("accounts/", include("django.contrib.auth.urls")),  
    path("itinerari/<int:pk>/prenota/", BookingCreateView.as_view(), name="booking_create"),
]
