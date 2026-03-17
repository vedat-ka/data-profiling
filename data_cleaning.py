"""
data_cleaning.py
----------------
Generisches Cleaning-Script – gesteuert ausschliesslich durch ydata-profiling.

Ablauf:
  1. CSV einlesen  (dtype=str → Originalformat bleibt erhalten)
  2. ydata-profiling auf Rohdaten → alle Befunde / Alerts extrahieren
  3. Für jeden Alert-Typ wird automatisch entschieden:
       ACTIONABLE  → bereinigen
       INFO-ONLY   → ausgeben, kein Eingriff
  4. Bereinigte CSV speichern
  5. ydata-profiling erneut → profile2.html (Vergleich)

Alert-Typen und ihre Behandlung:
  DUPLICATES        → drop_duplicates()
  MISSING           → Zeilen mit NaN in dieser Spalte entfernen (wenn p < 50 %)
  INFINITE          → Zeilen mit inf-Werten in dieser Spalte entfernen
  EMPTY             → Spalte komplett leer → Spalte droppen
  REJECTED          → ydata hat Spalte verworfen (leer/konstant) → Spalte droppen
  DIRTY_CATEGORY    → Whitespace in Kategorie-Werten trimmen
  CONSTANT          → nur melden (Spalte hat nur 1 Wert – Entscheidung beim Nutzer)
  ZEROS             → nur melden (Nullwerte – können legitim sein)
  HIGH_CORRELATION  → nur melden (Redundanz – Entscheidung beim Nutzer)
  HIGH_CARDINALITY  → nur melden (z. B. ID-Spalten)
  IMBALANCE         → nur melden (schiefe Verteilung – kein Cleaning)
  SKEWED            → nur melden (Transformation für ML – kein Cleaning)
  UNIQUE            → nur melden (z. B. Primary Key)
  UNIFORM           → nur melden
  TYPE_DATE         → nur melden (Format-Entscheidung beim Nutzer)
  CONSTANT_LENGTH   → nur melden
  NEAR_DUPLICATES   → nur melden (manuelle Prüfung empfohlen)
  UNSUPPORTED       → nur melden
  NON_STATIONARY    → nur melden (Zeitreihen-Eigenschaft)
  SEASONAL          → nur melden (Zeitreihen-Eigenschaft)

Prinzip:
  - Kein hardcodierter Spaltenname, kein dataset-spezifischer Code
  - Keine willkürliche Typ-Konvertierung während des Cleanings (dtype=str)
  - Nach dem Cleaning: automatisches SQL-Typ-Casting je Spalte
      INTEGER  → wenn alle Werte ganzzahlig sind
      FLOAT    → wenn alle Werte Dezimalzahlen sind
      DATETIME → wenn Werte als Datum/Zeit interpretierbar sind
      TEXT     → sonst (unveränderlich)
  - Für jede CSV ohne Anpassungen nutzbar
"""

from pathlib import Path

import re

import numpy as np
import pandas as pd
from ydata_profiling import ProfileReport
from ydata_profiling.model.alerts import AlertType


BASE_DIR    = Path(__file__).resolve().parent
INPUT_CSV   = BASE_DIR / "my_data.csv"
OUTPUT_CSV  = BASE_DIR / "my_data_cleaned.csv"
OUTPUT_HTML = BASE_DIR / "profile2.html"
SVG_STYLE_PATTERN = "<style type=text/css>*{stroke-linejoin: round; stroke-linecap: butt}</style>"
SVG_STYLE_REPLACEMENT = (
    "<style type=text/css>"
    "path, line, polyline, polygon, rect, circle, ellipse {"
    "stroke-linejoin: round; stroke-linecap: butt"
    "}</style>"
)

# Schwellenwert: Missing-Anteil ab dem eine Spalte NICHT gedroppt wird (Info-only)
MISSING_MAX_DROP = 0.50   # 50 %

# Regex: Spalten die wie ID-Spalten heissen (case-insensitive)
# Trifft auf: 'ID', 'id', 'Order ID', 'order_id', 'CustomerID', 'product_id', ...
_ID_PATTERN = re.compile(r"(^id$|_id$|\bid\b|id$)", re.IGNORECASE)


def sanitize_embedded_svg_styles(html_path: Path) -> int:
    html = html_path.read_text(encoding="utf-8")
    replacements = html.count(SVG_STYLE_PATTERN)
    if replacements == 0:
        return 0
    html = html.replace(SVG_STYLE_PATTERN, SVG_STYLE_REPLACEMENT)
    html_path.write_text(html, encoding="utf-8")
    return replacements


# ── ID-Spalten SQL-Check (generisch, unabhängig von ydata-profiling) ───────────

def check_id_columns(df: pd.DataFrame) -> None:
    """
    Findet alle Spalten deren Name nach einer ID-Spalte aussieht (*ID*, *_id*, *Id*)
    und prüft für jede:
      1. Sind die Werte numerisch?   → SQL: INTEGER
      2. Sind die Werte eindeutig?   → SQL: PRIMARY KEY / UNIQUE
      3. Gibt es NaN?                → SQL: NOT NULL
      4. Gibt es Duplikate in der ID-Spalte?

    Kein Eingriff in die Daten – nur Meldung.
    Der Nutzer entscheidet anschliessend ob eine Spalte wirklich PK sein soll.
    """
    id_cols = [col for col in df.columns if _ID_PATTERN.search(col)]
    if not id_cols:
        print(f"  ℹ ID-CHECK          → Keine ID-Spalten erkannt")
        return

    print(f"  {'─'*50}")
    print(f"  ID-Spalten SQL-Readiness-Check")
    print(f"  {'─'*50}")
    for col in id_cols:
        series = df[col]
        numeric_series = pd.to_numeric(series, errors="coerce")

        n_total      = len(series)
        n_nan        = series.isna().sum()
        n_non_numeric= numeric_series.isna().sum() - n_nan  # zusätzliche durch Konvertierung
        n_distinct   = series.dropna().nunique()
        n_dupes      = series.dropna().duplicated().sum()
        is_numeric   = n_non_numeric == 0
        is_unique    = n_dupes == 0
        is_not_null  = n_nan == 0

        sql_type     = "INTEGER" if is_numeric else "TEXT"
        sql_pk       = "✓ PRIMARY KEY möglich" if (is_unique and is_not_null and is_numeric) else "✗ NICHT als PRIMARY KEY geeignet"

        print(f"\n  Spalte: '{col}'")
        print(f"    Typ erkannt:       {'numerisch (INTEGER)' if is_numeric else 'nicht-numerisch (TEXT)'}")
        print(f"    Nullwerte:         {n_nan}  {'✓ keine' if is_not_null else '✗ vorhanden – NOT NULL verletzt'}")
        print(f"    Einzigartig:       {'✓ ja' if is_unique else f'✗ nein – {n_dupes} Duplikate in der ID-Spalte'}")
        print(f"    Distinct-Werte:    {n_distinct} / {n_total}  ({n_distinct/n_total:.1%})")
        print(f"    SQL-Eignung:       {sql_pk}")
        if not is_unique and n_dupes > 0:
            print(f"    Hinweis:           Duplikate in '{col}' = mehrere Zeilen pro ID")
            print(f"                       → Ist '{col}' wirklich ein PK? Oder ein FK (z.B. Order ID = mehrere Positionen)?")
    print()


# ── SQL-Typ Casting (nach dem Cleaning, generisch) ───────────────────────────

def cast_sql_types(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Versucht jede Spalte automatisch in den geeignetsten SQL-Typ zu konvertieren.

    Reihenfolge der Tests je Spalte:
      1. INTEGER  → pd.to_numeric + prüfen ob alle Werte ganzzahlig sind
      2. FLOAT    → pd.to_numeric  (Dezimalzahlen)
      3. DATETIME → pd.to_datetime (erkennt gängige Datumsformate)
      4. TEXT     → Fallback, keine Änderung

    Eine Spalte wird NUR dann gecastet wenn 0 Werte dabei verloren gehen
    (d.h. kein NaN durch den Cast entsteht der vorher nicht da war).
    Kein hardcodierter Spaltenname – funktioniert für jede CSV.
    """
    msgs = []
    df = df.copy()

    for col in df.columns:
        n_nan_before = df[col].isna().sum()

        # ── Test 1 & 2: Numerisch? ────────────────────────────────────────────
        numeric = pd.to_numeric(df[col], errors="coerce")
        n_failed = numeric.isna().sum() - n_nan_before
        if n_failed == 0 and not numeric.dropna().empty:
            if (numeric.dropna() % 1 == 0).all():
                df[col] = numeric.astype("Int64")   # nullable Integer
                msgs.append(f"    {col:<30} TEXT  →  INTEGER  ✓")
            else:
                df[col] = numeric.astype("float64")
                msgs.append(f"    {col:<30} TEXT  →  FLOAT    ✓")
            continue

        # ── Test 3: Datum/Zeit? ───────────────────────────────────────────────
        try:
            dt = pd.to_datetime(df[col], errors="coerce", format="mixed")
        except TypeError:
            dt = pd.to_datetime(df[col], errors="coerce")
        n_failed_dt = dt.isna().sum() - n_nan_before
        if n_failed_dt == 0 and not dt.dropna().empty:
            df[col] = dt
            msgs.append(f"    {col:<30} TEXT  →  DATETIME ✓")
            continue

        # ── Fallback: TEXT ────────────────────────────────────────────────────
        msgs.append(f"    {col:<30} TEXT  →  TEXT     (kein auto-cast)")

    return df, msgs


# ── Blank-Row-Erkennung (kein Alert, aber erkennbar aus desc) ─────────────────

def clean_blank_rows(df: pd.DataFrame, desc) -> tuple[pd.DataFrame, int]:
    """
    Keine eigene AlertType, aber erkennbar wenn alle Spalten identisch viele
    Missing-Werte haben → komplett leere Zeilen.
    Immer anwenden: dropna(how='all') ist immer sicher.
    """
    before = len(df)
    df = df.dropna(how="all")
    return df, before - len(df)


def clean_repeated_headers(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    Entfernt eingebettete Header-Zeilen (wiederholte Kopfzeilen innerhalb der Daten).
    Erkennt Zeilen wo mindestens eine Zelle denselben Wert hat wie der Spaltenname.
    Typischer Fall: CSV-Export wurde mehrfach aneinanderhängt.
    Kein hardcodierter Spaltenname – generisch für jede CSV.
    """
    before = len(df)
    mask = pd.Series(False, index=df.index)
    for col in df.columns:
        mask |= (df[col].astype(str).str.strip() == col)
    df = df[~mask].copy()
    return df, before - len(df)


# ── Alert-Handler (ein Handler pro AlertType) ─────────────────────────────────

def handle_duplicates(df: pd.DataFrame, alert) -> tuple[pd.DataFrame, str]:
    """DUPLICATES → drop_duplicates()"""
    before = len(df)
    df = df.drop_duplicates()
    removed = before - len(df)
    return df, f"  ✓ DUPLICATES        → {removed} Zeilen entfernt"


def handle_missing(df: pd.DataFrame, alert) -> tuple[pd.DataFrame, str]:
    """
    MISSING → Zeilen mit NaN in dieser Spalte entfernen.
    Nur wenn p_missing < MISSING_MAX_DROP.
    Sonst: Info-only (zu viele fehlende Werte, manuelle Entscheidung nötig).
    """
    col = alert.column_name
    if col not in df.columns:
        return df, f"  – MISSING           → Spalte '{col}' nicht im df"
    p = alert.values.get("p_missing", 0)
    if p > MISSING_MAX_DROP:
        return df, (f"  ! MISSING (INFO)    → '{col}': {p:.1%} fehlen – "
                    f"über {MISSING_MAX_DROP:.0%} Schwelle, bitte manuell entscheiden")
    before = len(df)
    df = df.dropna(subset=[col])
    removed = before - len(df)
    return df, f"  ✓ MISSING           → '{col}': {removed} Zeilen mit NaN entfernt ({p:.2%})"


def handle_infinite(df: pd.DataFrame, alert) -> tuple[pd.DataFrame, str]:
    """INFINITE → Zeilen mit inf/-inf in dieser Spalte entfernen."""
    col = alert.column_name
    if col not in df.columns:
        return df, f"  – INFINITE          → Spalte '{col}' nicht im df"
    numeric = pd.to_numeric(df[col], errors="coerce")
    mask = np.isinf(numeric)
    removed = mask.sum()
    if removed > 0:
        df = df[~mask].copy()
        return df, f"  ✓ INFINITE          → '{col}': {removed} Zeilen mit inf entfernt"
    return df, f"  – INFINITE          → '{col}': keine inf-Werte mehr vorhanden"


def handle_empty(df: pd.DataFrame, alert) -> tuple[pd.DataFrame, str]:
    """EMPTY → Spalte ist komplett leer → Spalte entfernen."""
    col = alert.column_name
    if col in df.columns:
        df = df.drop(columns=[col])
        return df, f"  ✓ EMPTY             → Spalte '{col}' entfernt (komplett leer)"
    return df, f"  – EMPTY             → Spalte '{col}' bereits nicht im df"


def handle_rejected(df: pd.DataFrame, alert) -> tuple[pd.DataFrame, str]:
    """REJECTED → ydata hat Spalte verworfen (leer/unbrauchbar) → Spalte entfernen."""
    col = alert.column_name
    if col in df.columns:
        df = df.drop(columns=[col])
        return df, f"  ✓ REJECTED          → Spalte '{col}' entfernt (von ydata verworfen)"
    return df, f"  – REJECTED          → Spalte '{col}' bereits nicht im df"


def handle_dirty_category(df: pd.DataFrame, alert) -> tuple[pd.DataFrame, str]:
    """
    DIRTY_CATEGORY → führende/nachfolgende Leerzeichen in Kategorie-Werten trimmen.
    Kein Typ-Cast, kein Format-Eingriff – nur str.strip().
    """
    col = alert.column_name
    if col not in df.columns:
        return df, f"  – DIRTY_CATEGORY    → Spalte '{col}' nicht im df"
    before_unique = df[col].nunique()
    df[col] = df[col].astype(str).str.strip()
    after_unique = df[col].nunique()
    diff = before_unique - after_unique
    return df, (f"  ✓ DIRTY_CATEGORY    → '{col}': Whitespace getrimmt, "
                f"Distinct {before_unique} → {after_unique} ({diff} zusammengeführt)")


# Info-only Handler: kein Eingriff, nur Ausgabe
def handle_info_only(df: pd.DataFrame, alert) -> tuple[pd.DataFrame, str]:
    col = f"'{alert.column_name}'" if alert.column_name else "(dataset)"
    extra = ""
    if alert.alert_type == AlertType.HIGH_CORRELATION:
        fields = alert.values.get("fields", [])
        extra = f" ↔ {fields}"
    elif alert.alert_type == AlertType.MISSING:
        p = alert.values.get("p_missing", 0)
        extra = f" ({p:.1%} fehlen)"
    return df, f"  ℹ {alert.alert_type.name:<18} → {col}{extra}  [nur Information, kein Eingriff]"


# ── Dispatch-Tabelle: AlertType → Handler ─────────────────────────────────────
# ACTIONABLE: werden aktiv bereinigt
# INFO-ONLY:  werden ausgegeben, kein Eingriff in die Daten

ACTIONABLE_HANDLERS = {
    AlertType.DUPLICATES:     handle_duplicates,
    AlertType.MISSING:        handle_missing,
    AlertType.INFINITE:       handle_infinite,
    AlertType.EMPTY:          handle_empty,
    AlertType.REJECTED:       handle_rejected,
    AlertType.DIRTY_CATEGORY: handle_dirty_category,
}

INFO_ONLY_TYPES = {
    AlertType.CONSTANT,
    AlertType.ZEROS,
    AlertType.HIGH_CORRELATION,
    AlertType.HIGH_CARDINALITY,
    AlertType.IMBALANCE,
    AlertType.SKEWED,
    AlertType.UNIQUE,
    AlertType.UNIFORM,
    AlertType.TYPE_DATE,
    AlertType.CONSTANT_LENGTH,
    AlertType.NEAR_DUPLICATES,
    AlertType.UNSUPPORTED,
    AlertType.NON_STATIONARY,
    AlertType.SEASONAL,
}


# ── Befunde ausgeben ──────────────────────────────────────────────────────────

def print_findings(desc, label: str) -> None:
    t = desc.table
    print(f"\n  {'─'*50}")
    print(f"  {label}")
    print(f"  {'─'*50}")
    print(f"  Zeilen:              {t['n']:>8}")
    print(f"  Spalten:             {t['n_var']:>8}")
    print(f"  Fehlende Zellen:     {t['n_cells_missing']:>8}  ({t['p_cells_missing']:.3%})")
    print(f"  Duplikate:           {t['n_duplicates']:>8}  ({t['p_duplicates']:.3%})")
    print(f"\n  Spaltenbefunde:")
    for col, var in desc.variables.items():
        flags = []
        if var["n_missing"] > 0:
            flags.append(f"missing {var['p_missing']:.2%}")
        if var.get("p_distinct", 0) > 0.95 and var["type"] == "Text":
            flags.append("high-cardinality")
        flag_str = "  ← " + ", ".join(flags) if flags else ""
        print(f"    {col:<28} [{var['type']:<13}]{flag_str}")
    print(f"\n  Alerts ({len(desc.alerts)}):")
    for alert in desc.alerts:
        col = f"'{alert.column_name}'" if alert.column_name else "(dataset)"
        print(f"    [{alert.alert_type.name:<20}]  {col}")
    print()


# ── Hauptprogramm ────────────────────────────────────────────────────────────

def main() -> None:
    # dtype=str → kein Auto-Cast, Originalformat bleibt erhalten
    df_raw = pd.read_csv(INPUT_CSV, dtype=str)
    rows_raw = len(df_raw)

    print(f"\n{'='*54}")
    print(f"  CSV:     {INPUT_CSV.name}")
    print(f"  Zeilen:  {rows_raw:>6}   Spalten: {len(df_raw.columns)}")
    print(f"{'='*54}")

    # ── Schritt 1: Rohdaten analysieren ──────────────────────────────────────
    print("\n  Analysiere Rohdaten mit ydata-profiling …")
    profile_raw = ProfileReport(df_raw, explorative=True, progress_bar=False)
    desc_raw = profile_raw.get_description()
    print_findings(desc_raw, "Befunde Rohdaten (vor Cleaning)")

    # ── Schritt 2: Blank-Rows (immer zuerst, kein eigener Alert) ─────────────
    print(f"{'='*54}")
    print("  Cleaning-Pipeline:\n")

    df = df_raw.copy()
    df, blank_removed = clean_blank_rows(df, desc_raw)
    if blank_removed > 0:
        print(f"  ✓ BLANK_ROWS        → {blank_removed} komplett leere Zeilen entfernt")
    else:
        print(f"  – BLANK_ROWS        → 0  (kein Befund)")

    df, header_removed = clean_repeated_headers(df)
    if header_removed > 0:
        print(f"  ✓ REPEAT_HEADERS    → {header_removed} wiederholte Header-Zeilen entfernt")
    else:
        print(f"  – REPEAT_HEADERS    → 0  (kein Befund)")

    # ── Schritt 3: Jeden Alert verarbeiten ────────────────────────────────────
    # Duplikate zuerst, dann Spalten-Alerts
    alerts_sorted = sorted(
        desc_raw.alerts,
        key=lambda a: (0 if a.alert_type == AlertType.DUPLICATES else 1)
    )

    for alert in alerts_sorted:
        atype = alert.alert_type
        if atype in ACTIONABLE_HANDLERS:
            df, msg = ACTIONABLE_HANDLERS[atype](df, alert)
            print(msg)
        elif atype in INFO_ONLY_TYPES:
            df, msg = handle_info_only(df, alert)
            print(msg)
        else:
            print(f"  ? UNBEKANNT         → {atype.name}  (kein Handler, übersprungen)")

    # ── Schritt 4: ID-Spalten SQL-Check ─────────────────────────────────────────
    print()
    check_id_columns(df)

    # ── Schritt 5: SQL-Typ Casting ───────────────────────────────────────────
    df_sql, cast_msgs = cast_sql_types(df)
    print(f"  {'─'*50}")
    print(f"  SQL-Typ Casting (automatisch)")
    print(f"  {'─'*50}")
    for msg in cast_msgs:
        print(msg)
    print()

    # ── Schritt 6: Zusammenfassung ────────────────────────────────────────────
    rows_clean = len(df)
    print(f"{'='*54}")
    print(f"  Zeilen vorher:   {rows_raw:>6}")
    print(f"  Zeilen nachher:  {rows_clean:>6}")
    print(f"  Entfernt:        {rows_raw - rows_clean:>6}")
    print(f"{'='*54}")

    # ── Schritt 7: Bereinigte CSV speichern (mit SQL-Typen) ───────────────────────
    df_sql.to_csv(OUTPUT_CSV, index=False)
    print(f"\n  CSV gespeichert:    {OUTPUT_CSV.name}   (bereinigt + SQL-Typen: INTEGER / FLOAT / DATETIME)")

    # ── Schritt 8: Erneut analysieren → profile2.html ────────────────────────
    print(f"\n  Analysiere bereinigte Daten → {OUTPUT_HTML.name} …")
    profile_clean = ProfileReport(
        df_sql,
        title=f"ydata-profiling (bereinigt): {OUTPUT_CSV.name}",
        explorative=True,
        progress_bar=False,
    )
    desc_clean = profile_clean.get_description()
    print_findings(desc_clean, "Befunde bereinigt (nach Cleaning)")

    profile_clean.to_file(OUTPUT_HTML)
    replacements = sanitize_embedded_svg_styles(OUTPUT_HTML)
    if replacements:
        print(f"  SVG-Styles bereinigt: {replacements} kompatibilitaetskritische Blocks angepasst")
    print(f"  Report gespeichert: {OUTPUT_HTML.name}")
    print("\n  Vergleich:")
    print("    my_data_profile.html  ←  Rohdaten")
    print("    profile2.html         ←  Bereinigte Daten")
    print()


if __name__ == "__main__":
    main()
