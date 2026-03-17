# Data Profiling mit ydata-profiling

Dieses Projekt ist bewusst einfach und praxisnah: Wenn du neue Daten bekommst, verwendest du zuerst `ydata-profiling`, erzeugst einen HTML-Report und entscheidest dann selbst, was an den Daten auffaellig oder falsch ist.

Wichtiger Hinweis zum Einstieg: Die Datei `ydata_guide.html` gibt dir eine kompakte inhaltliche Orientierung dazu, wie du den erzeugten Profiling-Report liest, welche Kennzahlen wichtig sind und worauf du bei auffaelligen Daten achten solltest. Wenn du neu in das Thema einsteigst, schau dir diese Datei am besten zuerst an.

Bevor du mit dem eigentlichen Profiling startest, solltest du ausserdem deine eigene `my_data.csv` in den Ordner `DataProfiling` kopieren. Die Skripte im Projekt verwenden diese Datei im Standardablauf als Eingabedatei. Ohne diese Datei funktionieren die beschriebenen Standardbefehle nicht wie vorgesehen.

## Voraussetzungen

- Python `>=3.10, <3.14`
- Empfohlen und getestet: Python `3.12.3`
- Nicht kompatibel: Python `3.14` und `3.15`
- Betriebssystem: Windows
- Empfohlen: PowerShell oder Windows Terminal

## Virtuelle Umgebung erstellen

Im Projektordner. Unter Windows solltest du dafuer gezielt eine kompatible Version waehlen, zum Beispiel Python `3.12`:

```powershell
py -3.12 -m venv .venv
```

`python -m venv .venv` ist auf Windows hier absichtlich nicht empfohlen, weil `python` bei dir auf Python `3.14` oder `3.15` zeigen kann. Damit laesst sich `ydata-profiling==4.18.1` nicht installieren.

Installierte Python-Versionen pruefst du mit:

```powershell
py -0p
```

Wenn Python `3.12` nicht installiert ist, installiere es zuerst und erstelle danach die `.venv` erneut.

## Virtuelle Umgebung aktivieren

### PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

Falls PowerShell die Aktivierung blockiert, kannst du fuer die aktuelle Sitzung einmalig Folgendes ausfuehren:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Eingabeaufforderung (CMD)

```bat
.venv\Scripts\activate.bat
```

## Abhaengigkeiten installieren

Zuerst `pip` in der aktiven `.venv` verwenden und dann die Projektanforderungen installieren:

```powershell
python -m pip install -r requirements.txt
```

## data_profiling.py ausfuehren

Wenn die virtuelle Umgebung aktiviert ist, startest du das Skript so:

```powershell
python data_profiling.py
```

Ohne aktivierte `.venv` nimmst du direkt den Interpreter aus der virtuellen Umgebung:

```powershell
.\.venv\Scripts\python.exe data_profiling.py
```

Andere CSV-Datei analysieren:

```powershell
python data_profiling.py deine_datei.csv
```

Ohne aktivierte `.venv`:

```powershell
.\.venv\Scripts\python.exe data_profiling.py deine_datei.csv
```

Eigenen Namen fuer den HTML-Report setzen:

```powershell
python data_profiling.py deine_datei.csv --output mein_report.html
```

Ohne aktivierte `.venv`:

```powershell
.\.venv\Scripts\python.exe data_profiling.py deine_datei.csv --output mein_report.html
```

## data_cleaning.py ausfuehren

`data_cleaning.py` ist der naechste Schritt nach dem Profiling. Das Skript liest die Rohdaten ein, wertet die Alerts aus `ydata-profiling` aus, bereinigt nur klar erkennbare Probleme automatisch und erstellt danach eine bereinigte CSV plus einen zweiten Report.

Das Skript arbeitet aktuell mit den Standarddateien im Projektordner:

- Eingabe: `my_data.csv`
- Bereinigte Ausgabe: `my_data_cleaned.csv`
- Neuer Report nach dem Cleaning: `profile2.html`

### Variante 1: `.venv` ist bereits aktiviert

```powershell
python data_cleaning.py
```

### Variante 2: `.venv` ist nicht aktiviert

```powershell
.\.venv\Scripts\python.exe data_cleaning.py
```

### Was automatisch bereinigt wird

- komplette Duplikate
- komplett leere Zeilen
- eingebettete wiederholte Header-Zeilen
- fehlende Werte in Spalten, wenn der Missing-Anteil unter dem Schwellwert liegt
- `inf`- und `-inf`-Werte
- komplett leere Spalten
- offensichtliche Kategorie-Probleme wie ueberfluessige Leerzeichen

### Was nicht automatisch entschieden wird

- stark korrelierte Spalten
- hohe Kardinalitaet
- schiefe Verteilungen
- Nullwerte, wenn sie fachlich vielleicht erlaubt sind
- Spalten, die man fachlich selbst als Kategorie, Datum oder Schluessel bewerten muss

Kurz gesagt: `data_cleaning.py` ersetzt nicht die manuelle Bewertung, sondern uebernimmt nur die klaren Standard-Bereinigungen nach dem ersten Profiling.

## Wichtiger Hinweis zu setuptools

`ydata-profiling 4.18.1` erwartet in dieser Umgebung noch `pkg_resources`. Dafuer muss `setuptools` kleiner als `81` bleiben.

Deshalb ist in `requirements.txt` bereits enthalten:

```text
setuptools<81
```

## Projektdateien

- `data_profiling.py`: erzeugt einen `ydata-profiling` HTML-Report fuer eine CSV-Datei
- `data_cleaning.py`: bereinigt Standardprobleme auf Basis der Profiling-Alerts und erstellt neue Ausgaben
- `my_data.csv`: Beispiel-Datei
- `my_data_cleaned.csv`: bereinigte Ausgabe von `data_cleaning.py`
- `my_data_profile.html`: typischer Report von `data_profiling.py`
- `profile2.html`: Report nach dem Cleaning
- `requirements.txt`: benoetigte Python-Pakete
- `.gitignore`: schliesst `.venv` aus Git aus

## Beispiel kompletter Ablauf unter Windows

```powershell
cd DataProfiling
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python data_profiling.py
```

## Ergebnis

Standardmaessig entstehen im Projekt diese Hauptausgaben:

- `my_data_profile.html` durch `data_profiling.py`
- `my_data_cleaned.csv` durch `data_cleaning.py`
- `profile2.html` als Report nach dem Cleaning

## Bedeutung der Statistik-Kennzahlen im Report

Jede numerische Spalte zeigt im ydata-profiling Report folgende Kennzahlen:

| Kennzahl | Bedeutung | Was pruefen? |
|---|---|---|
| **Distinct** | Anzahl einzigartiger Werte (z.B. 18 verschiedene Preise) | Sehr wenig Distinct bei Zahlen -> eher Kategorie als echte Zahl |
| **Distinct (%)** | Anteil einzigartiger Werte an allen Zeilen | < 1% -> starke Wiederholung, moeglicherweise kodierter Wert |
| **Missing** | Anzahl fehlender Eintraege (NaN / leer) | 0 = keine Luecken -> gut |
| **Missing (%)** | Anteil fehlender Eintraege in Prozent | > 5% -> Cleaning-Entscheidung noetig |
| **Infinite** | Anzahl unendlicher Werte (`inf` / `-inf`) | Entsteht z.B. durch Division durch 0; muss entfernt werden |
| **Infinite (%)** | Anteil unendlicher Werte | > 0% -> immer bereinigen |
| **Mean** | Arithmetischer Mittelwert (Durchschnitt) aller Werte | Stark von Minimum oder Maximum abweichend -> Ausreisser pruefen |
| **Minimum** | Kleinster vorhandener Wert | Negativ wo nicht erlaubt (z.B. Preis) -> Datenfehler |
| **Maximum** | Groesster vorhandener Wert | Unrealistisch hoch -> Ausreisser oder Eingabefehler |
| **Zeros** | Anzahl Eintraege mit Wert `0` | Bei Preis/Menge: 0 legitim oder Luecke? |
| **Zeros (%)** | Anteil Nullwerte in Prozent | > 5-10% -> fachlich pruefen ob 0 erlaubt ist |
| **Negative** | Anzahl negativer Werte | Bei Betraegen/Mengenspalten immer pruefen |
| **Negative (%)** | Anteil negativer Werte | > 0% bei Preisen/Mengen -> Datenfehler |
| **Memory size** | Speicherbedarf der Spalte im RAM | Nur relevant bei sehr grossen Datensaetzen |

### Beispiel-Interpretation (Price Each)

```text
Distinct       18        -> nur 18 verschiedene Preise in ~185.000 Zeilen
Distinct (%)   < 0.1%    -> stark wiederkehrende Werte -> kein echter Freitext
Missing        0         -> keine fehlenden Preise -> gut
Infinite       0         -> keine Division-durch-0-Fehler
Mean           184.52    -> durchschnittlicher Preis ~185 USD
Minimum        2.99      -> guenstigstes Produkt: 2,99 USD - plausibel
Maximum        1700      -> teuerste Position: 1.700 USD - pruefen ob realistisch
Zeros          0         -> kein Preis ist 0 -> kein offensichtlicher Lueckenwert
Negative       0         -> keine negativen Preise -> korrekt
```

**Fazit fuer diese Spalte:** Daten sehen sauber aus. Die 18 Distinct-Werte erklaeren sich dadurch, dass `Price Each` direkt am Produktnamen haengt (HIGH_CORRELATION Alert) - jedes Produkt hat einen festen Preis.

## Wie du den Report praktisch liest

Wenn der Report offen ist, gehe immer in dieser Reihenfolge vor:

1. `Overview`
   Pruefe Zeilen, Spalten, Datentypen, fehlende Werte und Dubletten.

2. `Variables`
   Pruefe jede wichtige Spalte einzeln.
   Frage dich: Ist das wirklich Zahl, Text, Kategorie oder Datum?

3. `Missing values`
   Sind fehlende Werte normal oder ein Datenproblem?

4. `Sample`
   Schaue dir echte Zeilen an. Hier siehst du oft schnell kaputte Eintraege, Leerzeilen oder wiederholte Kopfzeilen.

5. `Interactions` und `Correlations`
   Erst anschauen, wenn die Datenstruktur sauber ist. Sonst interpretierst du Muell.

## Wie du selbst entscheidest, was falsch ist

`ydata-profiling` soll dir nicht die Entscheidung abnehmen. Nutze diese Fragen:

1. Was bedeutet genau eine Zeile fachlich?
2. Welche Spalten sollten Zahlen sein?
3. Welche Spalten sollten Datum sein?
4. Sind Dubletten echte Fehler oder erlaubt?
5. Sind fehlende Werte kritisch oder normal?
6. Gibt es unplausible Werte, Tippfehler oder Mischformate?

## Faustregel

Erst `ydata-profiling`, dann verstehen, dann entscheiden, dann erst cleanen.

## Alternative Frameworks fuer Data Profiling

Es gibt mehrere Alternativen zu `ydata-profiling`. Jede hat andere Staerken:

| Framework | Installation | Besonderheit |
|---|---|---|
| **ydata-profiling** | `pip install ydata-profiling` | Sehr ausfuehrlich, HTML-Report, Alerts, Korrelationen - unser Standard |
| **sweetviz** | `pip install sweetviz` | Visuell sehr stark, besonders gut fuer Vergleiche (Train vs. Test) |
| **pandas-profiling** | _(war der alte Name von ydata-profiling)_ | Heute identisch mit ydata-profiling |
| **D-Tale** | `pip install dtale` | Interaktives Web-UI, aendern und analysieren direkt im Browser |
| **dataprep** | `pip install dataprep` | Schnell, einfach, gut fuer grosse Datensaetze |
| **AutoViz** | `pip install autoviz` | Automatische Visualisierungen, kein HTML-Report |
| **Lux** | `pip install lux-api` | Empfiehlt automatisch passende Visualisierungen in Jupyter |
| **Great Expectations** | `pip install great-expectations` | Fuer Datenvalidierung und Qualitaets-Tests in Pipelines |

### Wann welches Framework?

- **ydata-profiling** -> Standardfall: neues Dataset, vollstaendiger Ueberblick, HTML-Report
- **sweetviz** -> Vergleich zweier Datensaetze (z.B. vor/nach Cleaning, Train/Test)
- **D-Tale** -> interaktive Erkundung ohne Code
- **dataprep** -> grosse Datensaetze (schneller als ydata-profiling)
- **Great Expectations** -> Datenpipelines, automatische Qualitaets-Checks

### Kurzbeispiel sweetviz (Vergleich Rohdaten vs. bereinigt)

```python
import sweetviz as sv
import pandas as pd

df_raw = pd.read_csv("my_data.csv", dtype=str)
df_cleaned = pd.read_csv("my_data_cleaned.csv")

report = sv.compare([df_raw, "Rohdaten"], [df_cleaned, "Bereinigt"])
report.show_html("sweetviz_compare.html")
```

### Kurzbeispiel dataprep

```python
from dataprep.eda import create_report
import pandas as pd

df = pd.read_csv("my_data_cleaned.csv")
create_report(df).show_browser()
```