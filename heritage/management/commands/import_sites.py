import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from heritage.models import Sito, Categoria, Accessibilita


class Command(BaseCommand):
    help = (
        "Importa siti UNESCO da CSV con colonne: "
        "unesco_id,nome,descrizione,regione,citta,lat,long,categoria,anno,"
        "wheelchair,ausili_visivi,supporto_uditivo,note"
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str)

    def handle(self, *args, **opts):
        path = opts["csv_path"]

        def to_float(val):
            if val is None:
                return None
            s = str(val).strip().replace(",", ".")
            try:
                return float(s)
            except ValueError:
                return None

        def to_bool(val):
            s = str(val or "").strip().lower()
            if s in {"1", "true", "t", "yes", "y", "si", "s", "on"}:
                return True
            if s in {"0", "false", "f", "no", "n", "off"}:
                return False
            return None  

        try:
            with open(path, newline="", encoding="utf-8") as f:
                r = csv.DictReader(f)

                required = {
                    "unesco_id", "nome", "descrizione", "regione", "citta", "lat", "long",
                    "categoria", "anno", "wheelchair", "ausili_visivi", "supporto_uditivo", "note"
                }
                header = {c.strip() for c in (r.fieldnames or [])}
                if not required.issubset(header):
                    missing = ", ".join(sorted(required - header))
                    raise CommandError(f"CSV colonne mancanti: {missing}")

                created = updated = skipped_invalid_coords = skipped_missing_id = 0

                with transaction.atomic():
                    for i, row in enumerate(r, start=1):
                        unesco_id = (row.get("unesco_id") or "").strip()
                        if not unesco_id:
                            skipped_missing_id += 1
                            continue

                        categoria = None
                        cat_name = (row.get("categoria") or "").strip()
                        if cat_name:
                            categoria, _ = Categoria.objects.get_or_create(nome=cat_name)

                        w = to_bool(row.get("wheelchair"))
                        v = to_bool(row.get("ausili_visivi"))
                        h = to_bool(row.get("supporto_uditivo"))
                        note = (row.get("note") or "").strip()

                        any_bool_set = any(x is not None for x in (w, v, h))
                        acc = None
                        if any_bool_set or note:
                            acc, _ = Accessibilita.objects.get_or_create(
                                sedia_a_rotelle=w,
                                ausili_visivi=v,
                                supporto_uditivo=h,
                                defaults={"note": note},
                            )
                            if note and acc.note != note:
                                acc.note = note
                                acc.save(update_fields=["note"])

                        lat = to_float(row.get("lat") or row.get("latitudine"))
                        lng = to_float(row.get("long") or row.get("longitudine"))
                        if lat is None or lng is None:
                            skipped_invalid_coords += 1
                            continue

                        anno_str = str(row.get("anno", "")).strip()
                        anno_val = int(anno_str) if anno_str.isdigit() else None

                        obj, is_new = Sito.objects.update_or_create(
                            unesco_id=unesco_id,
                            defaults={
                                "nome": (row.get("nome") or "").strip(),
                                "descrizione": row.get("descrizione", ""),
                                "regione": row.get("regione", ""),
                                "citta": row.get("citta", ""),
                                "latitudine": lat,
                                "longitudine": lng,
                                "categoria": categoria,
                                "accessibilita": acc,
                                "anno_iscrizione": anno_val,
                            },
                        )
                        if is_new:
                            created += 1
                        else:
                            updated += 1

                        if i % 100 == 0:
                            self.stdout.write(
                                f"[{i}] Creati: {created} | Aggiornati: {updated} | "
                                f"Scartati (coord non valide): {skipped_invalid_coords} | "
                                f"Scartati (unesco_id mancante): {skipped_missing_id}"
                            )

                self.stdout.write(self.style.SUCCESS(
                    f"FATTO. Creati: {created} | Aggiornati: {updated} | "
                    f"Scartati (coord non valide): {skipped_invalid_coords} | "
                    f"Scartati (unesco_id mancante): {skipped_missing_id}"
                ))

        except FileNotFoundError:
            raise CommandError(f"File non trovato: {path}")
