# 🇮🇹 UNESCO Italia – Piattaforma interattiva dei siti Patrimonio Mondiale

**UNESCO Italia** è un'applicazione web sviluppata con **Django 5**, che mostra su mappa interattiva i siti UNESCO italiani e consente di esplorare itinerari tematici, filtrare i siti per accessibilità e prenotare visite guidate.

---

## 🧭 Funzionalità principali

- 🌍 **Mappa interattiva** con [Leaflet.js](https://leafletjs.com/)
- 🏛️ **Elenco completo** dei siti UNESCO italiani
- ♿ **Filtri di accessibilità** (sedia a rotelle, ausili visivi, supporto uditivo)
- 🧳 **Itinerari tematici** con tappe e mappe dedicate
- 📅 **Prenotazioni utenti** (nome, email, data, numero persone)
- 🗺️ **GeoJSON API** per il caricamento dinamico delle posizioni
- 💾 Database con oltre 60 siti UNESCO aggiornati

---

## ⚙️ Requisiti

- Python **3.13**
- pip (gestore pacchetti)
- Virtualenv (opzionale ma consigliato)

---

## 🚀 Installazione e avvio del progetto

Apri un terminale (PowerShell o CMD) e segui i passaggi:

```bash
# 1️⃣ Clona il repository
git clone https://github.com/Elia-visualstudios/unesco-italia.git
cd unesco-italia

# 2️⃣ Crea e attiva un ambiente virtuale
py -3.13 -m venv venv
.\venv\Scripts\activate

# 3️⃣ Installa le dipendenze
pip install -r requirements.txt

# 4️⃣ Applica le migrazioni
python manage.py migrate

# 5️⃣ (Facoltativo) Popola il database
python manage.py import_sites unesco_italia_access_complete.csv
python manage.py update_coords_from_csv unesco_italia_access_complete_FIXED.csv
python manage.py seed_itinerari
python manage.py import_access

# 6️⃣ Avvia il server di sviluppo
python manage.py runserver
