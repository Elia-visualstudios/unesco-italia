from django.db import models
from django.conf import settings 
from django.utils import timezone
from django.core.validators import MinValueValidator
class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descrizione = models.TextField(blank=True)

    def __str__(self):
        return self.nome


class Accessibilita(models.Model):
    sedia_a_rotelle = models.BooleanField(null=True, blank=True, db_index=True)
    ausili_visivi = models.BooleanField(null=True, blank=True, db_index=True)
    supporto_uditivo = models.BooleanField(null=True, blank=True, db_index=True)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return (
            f"Accessibilità (sedia: {self.sedia_a_rotelle}, "
            f"visivi: {self.ausili_visivi}, uditivo: {self.supporto_uditivo})"
        )

    class Meta:
        indexes = [
            models.Index(fields=["sedia_a_rotelle"]),
            models.Index(fields=["ausili_visivi"]),
            models.Index(fields=["supporto_uditivo"]),
        ]

    @property
    def has_data(self) -> bool:
        # True se almeno uno dei tre è valorizzato (True o False)
        return any(v is not None for v in (self.sedia_a_rotelle, self.ausili_visivi, self.supporto_uditivo))

    @property
    def any_true(self) -> bool:
        # True se almeno uno è True
        return any(v is True for v in (self.sedia_a_rotelle, self.ausili_visivi, self.supporto_uditivo))

    @property
    def all_true(self) -> bool:
        # True se tutti e tre sono True
        return all(v is True for v in (self.sedia_a_rotelle, self.ausili_visivi, self.supporto_uditivo))

class Sito(models.Model):
    nome = models.CharField(max_length=200)
    descrizione = models.TextField(blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name="siti")
    accessibilita = models.ForeignKey(Accessibilita, on_delete=models.SET_NULL, null=True, blank=True, related_name="siti")
    latitudine = models.FloatField(null=True, blank=True)
    longitudine = models.FloatField(null=True, blank=True)
    regione = models.CharField(max_length=100, blank=True)
    citta = models.CharField(max_length=100, blank=True)
    unesco_id = models.IntegerField(unique=True, db_index=True)

    def __str__(self):
        return self.nome

    class Meta:
        indexes = [
            models.Index(fields=["categoria"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(latitudine__isnull=True) |
                      (models.Q(latitudine__gte=-90) & models.Q(latitudine__lte=90)),
                name="sito_lat_range_or_null",
            ),
            models.CheckConstraint(
                check=models.Q(longitudine__isnull=True) |
                      (models.Q(longitudine__gte=-180) & models.Q(longitudine__lte=180)),
                name="sito_lng_range_or_null",
            ),
        ]

    nome = models.CharField(max_length=200)
    descrizione = models.TextField(blank=True)
    regione = models.CharField(max_length=100, db_index=True)
    citta   = models.CharField(max_length=100, db_index=True)
    latitudine = models.FloatField(null=True, blank=True)
    longitudine = models.FloatField(null=True, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    accessibilita = models.ForeignKey(
        "Accessibilita", on_delete=models.SET_NULL, null=True, blank=True, related_name="siti"
    )
    anno_iscrizione = models.IntegerField(null=True, blank=True)
    unesco_id = models.CharField(max_length=50, unique=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["regione"]),
            models.Index(fields=["citta"]),
            models.Index(fields=["categoria"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(latitudine__gte=-90) & models.Q(latitudine__lte=90),
                name="sito_lat_range",
            ),
            models.CheckConstraint(
                check=models.Q(longitudine__gte=-180) & models.Q(longitudine__lte=180),
                name="sito_lng_range",
            ),
        ]

    def __str__(self):
        return f"{self.nome} ({self.citta})" if self.citta else self.nome


class Itinerario(models.Model):
    nome = models.CharField(max_length=200)
    descrizione = models.TextField(blank=True)

    def __str__(self):
        return self.nome


class Tappa(models.Model):
    itinerario = models.ForeignKey(Itinerario, on_delete=models.CASCADE, related_name="tappe")
    sito = models.ForeignKey(Sito, on_delete=models.CASCADE)
    ordine = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["ordine"]
        constraints = [
            models.UniqueConstraint(fields=["itinerario", "ordine"], name="tappa_unique_itin_ordine"),
        ]

    def __str__(self):
        return f"{self.ordine}. {self.sito.nome}"

class PrenotazioneItinerario(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="prenotazioni_itinerario")
    itinerario = models.ForeignKey(Itinerario, on_delete=models.CASCADE, related_name="prenotazioni")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        unique_together = ("user", "itinerario")
        indexes = [
            models.Index(fields=["user", "itinerario"]),
        ]

    def __str__(self):
        return f"{self.user} → {self.itinerario} ({self.created_at:%Y-%m-%d})"

class Booking(models.Model):
    itinerario = models.ForeignKey("Itinerario", on_delete=models.CASCADE, related_name="bookings")
    nome = models.CharField(max_length=120)
    email = models.EmailField()
    data = models.DateField()
    numero_persone = models.PositiveIntegerField(validators=[MinValueValidator(1)], default=1)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["itinerario"]), models.Index(fields=["data"])]

    def __str__(self):
        return f"{self.nome} → {self.itinerario.nome} il {self.data}"