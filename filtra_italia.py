import pandas as pd

src = "unesco_od_italy.csv"
dst = "unesco_italia.csv"

df = pd.read_csv(src, encoding="utf-8", sep=";")

out = pd.DataFrame()
out["unesco_id"] = df.get("id_number", df.get("id", ""))
out["nome"] = df.get("site", df.get("name_en", ""))
out["descrizione"] = df.get("short_description", df.get("short_description_en", ""))
out["regione"] = df.get("region", df.get("region_en", ""))
out["citta"] = df.get("location", df.get("location_en", ""))

# coordinate
if "latitude" in df.columns and "longitude" in df.columns:
    out["lat"] = pd.to_numeric(df["latitude"].astype(str).str.replace(",", "."), errors="coerce")
    out["long"] = pd.to_numeric(df["longitude"].astype(str).str.replace(",", "."), errors="coerce")
elif "coordinates" in df.columns:
    coords = df["coordinates"].astype(str).str.split(",", n=1, expand=True)
    out["lat"] = pd.to_numeric(coords[0].str.replace(",", "."), errors="coerce")
    out["long"] = pd.to_numeric(coords[1].str.replace(",", "."), errors="coerce")
else:
    out["lat"] = None
    out["long"] = None

out["categoria"] = df.get("category", "")

def year4(x):
    s = str(x).strip()
    return int(s[:4]) if s[:4].isdigit() else None
out["anno"] = df["date_inscribed"].map(year4) if "date_inscribed" in df.columns else None

# accessibilità placeholder
out["wheelchair"] = 0
out["ausili_visivi"] = 0
out["supporto_uditivo"] = 0
out["note"] = ""

cols = ["unesco_id","nome","descrizione","regione","citta","lat","long",
        "categoria","anno","wheelchair","ausili_visivi","supporto_uditivo","note"]
out = out[cols]

out.to_csv(dst, index=False, encoding="utf-8")
print(f"Creato {dst} con {len(out)} record.")
