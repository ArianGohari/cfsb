# Code für Teil II

Aktueller Schwerpunkt: miR-6517/PFKL.

| Ordner | Aufgabe |
|---|---|
| `literature/milk_inventory/` | Quellen, Milch-Inventar, Sequenz- und Targetprüfung |
| `analysis/` | KEGG-/GENCODE-Netzwerk und Prüfung publizierter PFKL-Abbauraten |
| `documents/` | Literaturübersicht, Abbildungen, Bericht und Präsentation erstellen |
| `model/pfkl/` | Enzymmodell, regulatorisches Petrinetz und Modellprüfungen |
| `tests/` | Sequenz- und Prozessierungsprüfungen |
| `reproduction/` | Gesamtauswertung in einer getrennten Arbeitskopie wiederholen |

Der [Reproduktionseinstieg](reproduction/README.md) dokumentiert die Umgebung und die aktuellen Schritte. Die Julia-Umgebung steht unter `model/Project.toml` und `model/Manifest.toml`. R und DESeq2 werden im aktuellen Ablauf nicht mehr benötigt.

```sh
uv sync --locked --project code/part2/reproduction
uv run --offline --locked --project code/part2/reproduction python code/part2/reproduction/replay.py
```

## Frühere miR-146a-Auswertung

Programme, Referenzmodelle und Prüfungen liegen unter [archive/code/part2](../../archive/code/part2/README.md). Historische Skripte über den Starter ausführen, der ihre ursprünglichen relativen Pfade wiederherstellt:

```sh
uv run --offline --project archive/code/tools/reproduction --locked python code/tools/run.py archive/code/part2/model/catalyst/scripts/replay.py
```

Neue Ausgaben entstehen unter `output/runs/`. Die Pfadzuordnung steht in `code/tools/part2_layout.json`; archivierte Ergebnisse bleiben unverändert.

## Modell und Folien nachvollziehen

1. `model/pfkl/regulation.jl` definiert die beiden Stellen M (mRNA) und E (Protein) sowie die vier Reaktionen. `simulate_regulation.jl` berechnet die Szenarien.
2. `model/pfkl/fit_enzyme.py` passt die Substratkurve an die publizierten PFKL-Messwerte an. Die miRNA-Wirkung wird damit nicht kalibriert.
3. `model/pfkl/summarize_regulation.py` wertet die simulierten Verläufe aus; `check_enzyme.py` prüft den Enzymfit.
4. `documents/build_presentation.py` und `documents/build_report.py` bauen die Dokumente aus gespeicherten Ergebnissen.

Für einzelne Skripte dieselbe gesperrte Python-Umgebung wie beim Gesamtlauf verwenden. Der Gesamtlauf arbeitet in einer eigenen Kopie; einzelne Analyseskripte schreiben direkt nach `output/part2/`.

```sh
uv run --offline --locked --project code/part2/reproduction python -m unittest discover -s code/part2/tests
ruff check code/part2 code/tools --select F
```

Die entfernte RNA-/SGBS-Auswertung und der frühere Gesamtlauf liegen unter [archive/rna_context_20261013](../../archive/rna_context_20261013/README.md). Rohdaten und historische Ergebnisse bleiben an ihren bisherigen Orten.
