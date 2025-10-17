import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from heritage.models import Sito, Accessibilita


def to_bool_or_none(x: str | None):
    s = (x or "").strip().lower()
    if s in {"1", "true", "t", "yes", "y", "si", "s", "on"}:
        return True
    if s in {"0", "false", "f", "no", "n", "off"}:
        return False
    return None


class Command(BaseCommand):
    help = "Importa/aggiorna i dati di accessibilità dal CSV"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Percorso al CSV (es. unesco_italia_access_complete.csv)")
        parser.add_argument(
            "--match-on", choices=["unesco_id", "nome"], default="unesco_id",
            help="Campo su cui abbinare i siti (default: unesco_id)"
        )

    def handle(self, *args, **opts):
        path = Path(opts["csv_path"])
        if not path.exists():
            raise CommandError(f"CSV non trovato: {path}")

        match_on = opts.get("match_on", "unesco_id")

        created = updated = skipped = 0
        missing = []

        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row.get("unesco_id") if match_on == "unesco_id" else row.get("nome")
                if not key:
                    skipped += 1
                    continue

                try:
                    sito = (
                        Sito.objects.get(unesco_id=int(key))
                        if match_on == "unesco_id"
                        else Sito.objects.get(nome=key)
                    )
                except Sito.DoesNotExist:
                    missing.append(key)
                    continue

                vals = dict(
                    sedia_a_rotelle=to_bool_or_none(row.get("wheelchair")),
                    ausili_visivi=to_bool_or_none(row.get("ausili_visivi")),
                    supporto_uditivo=to_bool_or_none(row.get("supporto_uditivo")),
                )

                # Se il sito ha già un record di accessibilità → aggiorna
                if sito.accessibilita:
                    for k, v in vals.items():
                        setattr(sito.accessibilita, k, v)
                    sito.accessibilita.save()
                    updated += 1
                else:
                    acc = Accessibilita.objects.create(**vals)
                    sito.accessibilita = acc
                    sito.save()
                    created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Create: {created} | Aggiornate: {updated} | Saltate: {skipped} | Siti non trovati: {len(missing)}"
        ))
        if missing:
            self.stdout.write("Non trovati (prime 10): " + ", ".join(map(str, missing[:10])))
