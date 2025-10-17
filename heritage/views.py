from functools import reduce
from operator import or_ as OR

from django.db.models import Q, OuterRef, Exists
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView
from django.views.generic.edit import CreateView
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy

from .models import Sito, Categoria, Itinerario, PrenotazioneItinerario, Booking, Tappa
from .forms import BookingForm


def home(request):
    return render(
        request,
        "heritage/home.html",
        {"categorie": Categoria.objects.order_by("nome")},
    )



def to_bool_param(v):
    """Converte parametri tipo '1/0', 'true/false', 'yes/no' in True/False/None."""
    s = (v or "").strip().lower()
    if s in ("1", "true", "yes", "y"):
        return True
    if s in ("0", "false", "no", "n"):
        return False
    return None


def _qs_base():
    """Query base per i Siti (con select_related per ridurre le query)."""
    return Sito.objects.select_related("categoria", "accessibilita").all()


def _apply_text_filters(qs, request):
    """Applica filtri per testo/categoria/regione/città."""
    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(Q(nome__icontains=q) | Q(citta__icontains=q) | Q(regione__icontains=q))

    cat_map = {
        "cultural": "Culturale",
        "culturale": "Culturale",
        "natural": "Naturale",
        "naturale": "Naturale",
    }
    categoria = (request.GET.get("categoria") or "").strip()
    if categoria:
        normalized = cat_map.get(categoria.lower(), categoria)
        qs = qs.filter(categoria__nome__iexact=normalized)

    regione = (request.GET.get("regione") or "").strip()
    if regione:
        qs = qs.filter(regione__iexact=regione)

    citta = (request.GET.get("citta") or "").strip()
    if citta:
        qs = qs.filter(citta__iexact=citta)

    return qs


def _apply_access_filters(qs, request):
    """Applica filtri di accessibilità (any/all) e 'solo con dati disponibili'."""
    wc = to_bool_param(request.GET.get("wheelchair"))
    av = to_bool_param(request.GET.get("ausili_visivi"))
    su = to_bool_param(request.GET.get("supporto_uditivo"))
    mode = (request.GET.get("acc_mode") or "any").strip().lower()
    if mode not in ("any", "all"):
        mode = "any"

    has_data = (request.GET.get("has_acc_data") or "").strip().lower() in ("1", "true", "yes", "y")

    filters = []
    if wc is not None:
        filters.append(Q(accessibilita__sedia_a_rotelle=wc))
    if av is not None:
        filters.append(Q(accessibilita__ausili_visivi=av))
    if su is not None:
        filters.append(Q(accessibilita__supporto_uditivo=su))

    if filters:
        if mode == "all":
            for f in filters:
                qs = qs.filter(f)
        else:
            qs = qs.filter(reduce(OR, filters))

    if has_data:
        qs = qs.exclude(
            accessibilita__sedia_a_rotelle__isnull=True,
            accessibilita__ausili_visivi__isnull=True,
            accessibilita__supporto_uditivo__isnull=True,
        )
    return qs


def _paginate(request):
    """Estrae limit/offset in modo safe."""
    try:
        limit = max(1, min(int(request.GET.get("limit", 100)), 500))
    except Exception:
        limit = 100
    try:
        offset = max(0, int(request.GET.get("offset", 0)))
    except Exception:
        offset = 0
    return limit, offset


def _serialize_geojson(rows, total):
    """Serializza i siti come FeatureCollection GeoJSON, con bbox."""
    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [s.longitudine, s.latitudine]},
            "properties": {
                "id": s.id,
                "unesco_id": s.unesco_id,
                "name": s.nome,
                "city": s.citta,
                "region": s.regione,
                "category": (s.categoria.nome if s.categoria_id else None),
                "acc": {
                    "sedia_a_rotelle": (s.accessibilita.sedia_a_rotelle if s.accessibilita else None),
                    "ausili_visivi": (s.accessibilita.ausili_visivi if s.accessibilita else None),
                    "supporto_uditivo": (s.accessibilita.supporto_uditivo if s.accessibilita else None),
                    "has_data": bool(
                        s.accessibilita
                        and (
                            s.accessibilita.sedia_a_rotelle is not None
                            or s.accessibilita.ausili_visivi is not None
                            or s.accessibilita.supporto_uditivo is not None
                        )
                    ),
                    "any_true": bool(
                        s.accessibilita
                        and (
                            s.accessibilita.sedia_a_rotelle is True
                            or s.accessibilita.ausili_visivi is True
                            or s.accessibilita.supporto_uditivo is True
                        )
                    ),
                },
            },
        }
        for s in rows
        if s.latitudine is not None and s.longitudine is not None  # coord valide
    ]

    payload = {"type": "FeatureCollection", "features": features, "count": total}
    if features:
        lons = [f["geometry"]["coordinates"][0] for f in features]
        lats = [f["geometry"]["coordinates"][1] for f in features]
        payload["bbox"] = [min(lons), min(lats), max(lons), max(lats)]
    return payload



def sites_geojson(request):
    """Alias principale usato dai template."""
    qs = _apply_access_filters(_apply_text_filters(_qs_base(), request), request)
    limit, offset = _paginate(request)
    total = qs.count()
    rows = qs[offset : offset + limit]
    return JsonResponse(_serialize_geojson(rows, total), json_dumps_params={"ensure_ascii": False})


def siti_geojson(request):
    """Alias secondario (per retro-compatibilità con nomi italiani)."""
    return sites_geojson(request)


def itinerario_geojson(request, pk: int):
    itin = get_object_or_404(Itinerario.objects.prefetch_related("tappe__sito"), pk=pk)
    features = []
    for tappa in itin.tappe.all():
        sito = tappa.sito
        if sito.latitudine is not None and sito.longitudine is not None:

            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [sito.longitudine, sito.latitudine]},
                    "properties": {
                        "id": sito.id,
                        "name": sito.nome,
                        "city": sito.citta,
                        "region": sito.regione,
                        "order": tappa.ordine,
                        "category": (sito.categoria.nome if sito.categoria else None),
                    },
                }
            )
    return JsonResponse({"type": "FeatureCollection", "features": features}, json_dumps_params={"ensure_ascii": False})



class ItinerarioListView(ListView):
    model = Itinerario
    template_name = "heritage/itinerari_list.html"
    context_object_name = "itinerari"
    paginate_by = 12

    def get_queryset(self):
        qs = Itinerario.objects.all().order_by("nome")

        wc_subq = Tappa.objects.filter(
            itinerario=OuterRef("pk"),
            sito__accessibilita__sedia_a_rotelle=True
        )
        visivi_subq = Tappa.objects.filter(
            itinerario=OuterRef("pk"),
            sito__accessibilita__ausili_visivi=True
        )
        uditivo_subq = Tappa.objects.filter(
            itinerario=OuterRef("pk"),
            sito__accessibilita__supporto_uditivo=True
        )

        qs = qs.annotate(
            has_wheelchair=Exists(wc_subq),
            has_visivi=Exists(visivi_subq),
            has_uditivo=Exists(uditivo_subq),
        ).prefetch_related(
            "tappe__sito__accessibilita"  
        )

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pren_ids = set()
        if self.request.user.is_authenticated:
            page_itins = [i.id for i in ctx["itinerari"]]
            pren_ids = set(
                PrenotazioneItinerario.objects.filter(
                    user=self.request.user, itinerario_id__in=page_itins
                ).values_list("itinerario_id", flat=True)
            )
        ctx["prenotati_ids"] = pren_ids
        return ctx

def itinerario_dettaglio(request, pk: int):
    itin = get_object_or_404(Itinerario.objects.prefetch_related("tappe__sito"), pk=pk)
    is_prenotato = False
    if request.user.is_authenticated:
        is_prenotato = PrenotazioneItinerario.objects.filter(user=request.user, itinerario=itin).exists()
    return render(request, "heritage/itinerario_dettaglio.html", {"itinerario": itin, "is_prenotato": is_prenotato})



@login_required
@require_POST
def toggle_prenotazione(request, pk: int):
    """Crea o elimina la prenotazione 'follow' dell'utente corrente per questo itinerario."""
    itin = get_object_or_404(Itinerario, pk=pk)
    obj, created = PrenotazioneItinerario.objects.get_or_create(user=request.user, itinerario=itin)
    if not created:
        obj.delete()
        return JsonResponse({"status": "removed"})
    return JsonResponse({"status": "added"})

class BookingCreateView(CreateView):
    model = Booking
    form_class = BookingForm
    template_name = "heritage/booking_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.itinerario = get_object_or_404(Itinerario, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.itinerario = self.itinerario
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("itinerari_list")