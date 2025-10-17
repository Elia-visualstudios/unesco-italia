import csv
from django.core.management.base import BaseCommand, CommandError
from heritage.models import Sito

class Command(BaseCommand):
    help = "Aggiorna lat/long/città/regione dei Sito dal CSV (matching per unesco_id)"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str)

    def handle(self, *args, **opts):
        path = opts["csv_path"]
        updated = 0
        try:
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        unesco_id = int(row["unesco_id"])
                    except Exception:
                        continue
                    lat = row.get("lat")
                    lng = row.get("long")
                    citta = row.get("citta")
                    regione = row.get("regione")

                    qs = Sito.objects.filter(unesco_id=unesco_id)
                    if not qs.exists():
                        continue

                    fields = {}
                    if lat not in (None, "", "NaN"): fields["latitudine"] = float(lat)
                    if lng not in (None, "", "NaN"): fields["longitudine"] = float(lng)
                    if citta and str(citta).strip().lower() != "nan": fields["citta"] = citta
                    if regione and str(regione).strip().lower() != "nan": fields["regione"] = regione

                    if fields:
                        qs.update(**fields)
                        updated += 1
        except FileNotFoundError as e:
            raise CommandError(str(e))

        self.stdout.write(self.style.SUCCESS(f"Aggiornati {updated} record da {path}"))
