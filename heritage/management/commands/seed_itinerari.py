from django.core.management.base import BaseCommand
from heritage.models import Itinerario, Tappa, Sito

def pick(name_part):
    return Sito.objects.filter(nome__icontains=name_part).order_by("id").first()

class Command(BaseCommand):
    help = "Crea itinerari demo (Nord Italia / Centro Italia / Sud & Isole)."

    def handle(self, *args, **opts):
        data = [
            ("Città d’arte del Nord", "Percorso tra alcune città d’arte del Nord Italia",
             ["Turin", "Milan", "Bergamo", "Verona", "Venice"]),
            ("Cuore del Rinascimento", "Tra i capolavori del Rinascimento italiano",
             ["Florence", "Siena", "Urbino", "Ferrara"]),
            ("Sud & Isole", "Siti imperdibili del Sud Italia e delle isole",
             ["Naples", "Matera", "Palermo", "Agrigento", "Syracuse"])
        ]

        for nome, descr, stops in data:
            itin, _ = Itinerario.objects.get_or_create(nome=nome, defaults={"descrizione": descr})
            itin.tappe.all().delete()
            for ordine, key in enumerate(stops, start=1):
                s = pick(key)
                if s:
                    Tappa.objects.create(itinerario=itin, sito=s, ordine=ordine)

        self.stdout.write(self.style.SUCCESS(f"Seed itinerari completato. Itinerari: {len(data)}"))
