"""
compare_sweetviz.py
-------------------
Vergleicht Rohdaten (my_data.csv) mit bereinigten Daten (my_data_cleaned.csv)
mithilfe von sweetviz.

Ergebnis: sweetviz_compare.html
  - Linke Seite:  Rohdaten
  - Rechte Seite: Bereinigte Daten
  - Jede Spalte direkt nebeneinander vergleichbar:
      Verteilung, Distinct-Werte, Missing, Typen

Ausfuehren:
    python compare_sweetviz.py
"""

from pathlib import Path

import pandas as pd
import sweetviz as sv

BASE_DIR   = Path(__file__).resolve().parent
RAW_CSV    = BASE_DIR / "my_data.csv"
CLEAN_CSV  = BASE_DIR / "my_data_cleaned.csv"
OUTPUT_HTML = BASE_DIR / "sweetviz_compare.html"


def main() -> None:
    if not RAW_CSV.exists():
        print(f"  ✗ Datei nicht gefunden: {RAW_CSV.name}")
        return
    if not CLEAN_CSV.exists():
        print(f"  ✗ Datei nicht gefunden: {CLEAN_CSV.name}")
        print("    → Zuerst data_cleaning.py ausfuehren!")
        return

    print(f"\n  Lade {RAW_CSV.name}  …")
    df_raw = pd.read_csv(RAW_CSV, dtype=str)
    print(f"  Zeilen: {len(df_raw):>7}   Spalten: {len(df_raw.columns)}")

    print(f"  Lade {CLEAN_CSV.name}  …")
    df_clean = pd.read_csv(CLEAN_CSV)
    print(f"  Zeilen: {len(df_clean):>7}   Spalten: {len(df_clean.columns)}")

    print(f"\n  Erstelle sweetviz-Vergleichsreport …")
    report = sv.compare(
        [df_raw,   "Rohdaten   (my_data.csv)"],
        [df_clean, "Bereinigt  (my_data_cleaned.csv)"],
    )

    report.show_html(str(OUTPUT_HTML), open_browser=True)
    print(f"\n  Report gespeichert: {OUTPUT_HTML.name}")
    print("  → Im Browser geoeffnet\n")


if __name__ == "__main__":
    main()
