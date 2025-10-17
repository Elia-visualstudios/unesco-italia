import os
import django
import csv

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unesco_it.settings')
django.setup()

from heritage.models import Sito, Categoria, Accessibilita



csv_file = 'siti_unesco.csv' 

with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    
    for i, row in enumerate(reader, 1):
        try:
            unesco_id = row.get('unesco_id', '').strip()
            
            if Sito.objects.filter(unesco_id=unesco_id).exists():
                print(f"⏭️  [{i}] {unesco_id} - Già presente, aggiorno accessibilità...")
                sito = Sito.objects.get(unesco_id=unesco_id)
            else:
                print(f"➕ [{i}] Creo nuovo sito: {row.get('nome', '').strip()}")
                
                categoria_nome = row.get('categoria', '').strip()
                categoria = None
                if categoria_nome:
                    categoria, _ = Categoria.objects.get_or_create(nome=categoria_nome)
                
                lat = row.get('lat', '').strip()
                long = row.get('long', '').strip()
                
                sito = Sito.objects.create(
                    nome=row.get('nome', '').strip(),
                    descrizione=row.get('descrizione', '').strip(),
                    regione=row.get('regione', '').strip(),
                    citta=row.get('citta', '').strip(),
                    latitudine=float(lat) if lat else None,
                    longitudine=float(long) if long else None,
                    categoria=categoria,
                    anno_iscrizione=int(row.get('anno', '')) if row.get('anno', '').strip() else None,
                    unesco_id=unesco_id
                )
            
            def str_to_bool(s):
                if s == '1':
                    return True
                elif s == '0':
                    return False
                return None
            
            wheelchair = str_to_bool(row.get('wheelchair', '').strip())
            ausili_visivi = str_to_bool(row.get('ausili_visivi', '').strip())
            supporto_uditivo = str_to_bool(row.get('supporto_uditivo', '').strip())
            
            if sito.accessibilita:
                sito.accessibilita.sedia_a_rotelle = wheelchair
                sito.accessibilita.ausili_visivi = ausili_visivi
                sito.accessibilita.supporto_uditivo = supporto_uditivo
                sito.accessibilita.note = row.get('note', '').strip()
                sito.accessibilita.save()
            else:
                acc = Accessibilita.objects.create(
                    sedia_a_rotelle=wheelchair,
                    ausili_visivi=ausili_visivi,
                    supporto_uditivo=supporto_uditivo,
                    note=row.get('note', '').strip()
                )
                sito.accessibilita = acc
                sito.save()
            
            print(f"   ✓ Accessibilità: 🪑={wheelchair} 👁️={ausili_visivi} 🔊={supporto_uditivo}")
        
        except Exception as e:
            print(f"✗ Errore riga {i} ({row.get('nome', 'Unknown')}): {e}")

print(f"\n✅ Importazione completata!")
print(f"Total siti in DB: {Sito.objects.count()}")