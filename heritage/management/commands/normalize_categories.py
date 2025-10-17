# heritage/management/commands/normalize_categories.py
from django.core.management.base import BaseCommand
from django.db import transaction
from heritage.models import Categoria, Sito

CANONICAL = {
    "culturale": "Culturale",
    "cultural": "Culturale",
    "cultura": "Culturale",
    "culturali": "Culturale",

    "naturale": "Naturale",
    "natural": "Naturale",
    "natura": "Naturale",
    "naturali": "Naturale",
}

class Command(BaseCommand):
    help = "Normalizza le categorie a due soli valori canonici: Culturale, Naturale. Unisce duplicati e riassegna i Sito."

    def handle(self, *args, **opts):
        with transaction.atomic():
            cat_cult, _ = Categoria.objects.get_or_create(nome="Culturale", defaults={"descrizione": ""})
            cat_nat,  _ = Categoria.objects.get_or_create(nome="Naturale", defaults={"descrizione": ""})

            reassigned = 0
            deleted = 0
            report = []

            for cat in Categoria.objects.all().order_by("nome"):
                name = (cat.nome or "").strip()
                key = name.lower()

                if cat.id in (cat_cult.id, cat_nat.id):
                    continue

                target_name = CANONICAL.get(key)
                if not target_name:
                
                    target_name = "Culturale"

                target_cat = cat_cult if target_name == "Culturale" else cat_nat
                count = Sito.objects.filter(categoria=cat).update(categoria=target_cat)
                reassigned += count
                report.append(f'"{name}" -> "{target_cat.nome}" ({count} siti)')

                if not Sito.objects.filter(categoria=cat).exists():
                    cat.delete()
                    deleted += 1

            self.stdout.write(self.style.SUCCESS("Normalizzazione completata."))
            self.stdout.write("\n".join(report))
            self.stdout.write(self.style.SUCCESS(f"Riassegnati: {reassigned} | Categorie eliminate: {deleted}"))
