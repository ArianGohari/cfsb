# Teil II reproduzieren

`replay.py` wiederholt Literaturauswertung, Sequenzprüfung, Modellierung und Dokumentbuild offline in einer separaten Kopie. Benötigte Eingaben werden nicht heruntergeladen.

## Voraussetzungen

- Python 3.14.6 und `uv`; Paketstände in `uv.lock`.
- Julia 1.12.7; Paketstände in `../model/Project.toml` und `Manifest.toml`.
- Typst, Graphviz (`dot`) und Poppler (`pdftotext`).
- Arial, Libertinus Serif, DejaVu Sans sowie lokale Roboto-Schriften.
- Die lokalen Ordner `data/`, `obsidian/Projekt/`, `report/typst/`, `presentation/ergebnisse_mir6517/` und `presentation/assets/fonts/`.
- `output/part2/review_summary/bibliography_sources.json` als gespeicherter Herkunftsnachweis.

Daten, Notizen und Dokumentquellen sind nicht auf GitHub. Geprüft wurde der Lauf unter macOS/Apple Silicon mit vorhandenen Paketen; keine Neuinstallation auf einem fremden Rechner.

## Ausführen

Ab Projektwurzel:

```sh
uv sync --locked --project code/part2/reproduction
julia --startup-file=no --project=code/part2/model -e 'using Pkg; Pkg.instantiate()'
uv run --offline --locked --project code/part2/reproduction python code/part2/reproduction/replay.py
```

`--list` zeigt die Befehle. `--output <neuer-ordner>` setzt das Ziel. Ohne diese Option entsteht `output/reproduction/mir6517_<Zeitstempel>/` mit etwa 1,5 GB zusätzlichem Speicherbedarf.

## Ergebnis prüfen

`workspace/` enthält die Arbeitskopie und ihre Ergebnisse. `logs/` und `steps.json` zeigen die ausgeführten Befehle; `environment.json` die Umgebung.

`summary.json` meldet `passed`, wenn alle Schritte und Dateiprüfungen bestehen. `comparisons.json` vergleicht Ergebnisse mit dem bisherigen Bestand. Bekannte Kurationsunterschiede werden nur für die festgelegten Hashpaare in `documented_curation_differences.json` akzeptiert. Originaleingaben und bisherige Ergebnisse dürfen sich nicht ändern.

Die Prüfung belegt technische Reproduzierbarkeit, keine humane miRNA-Wirkung. Neue Recherchen, Volltextlektüre und Studienauswahl gehören nicht zum Replay.
