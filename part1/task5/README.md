# Aufgabe 5

Die Ausarbeitung ist in [task5.html](task5.html) lesbar. [task5.qmd](task5.qmd) enthält den Quelltext.

Das statische humane Evidenznetz steht als [JSON](data/network.json), [Knoten-TSV](data/nodes.tsv), [Kanten-TSV](data/edges.tsv) und [SVG](figures/network.svg) bereit. Es umfasst 22 Knoten und 18 kontextannotierte Kanten. Die quantitative Reanalyse von GSE41571 vergleicht fünf rupturierte mit sechs stabilen humanen Karotisplaques. Die vollständigen Ergebnisse liegen unter [results/GSE41571](results/GSE41571/).

Ab Projektwurzel reproduzieren:

```sh
python3 part1/task5/scripts/build_network.py
Rscript part1/task5/scripts/analyse_gse41571.R
quarto render part1/task5/task5.qmd --no-execute
```

Python 3, Graphviz, R 4.6.1 mit `limma`, `ggplot2`, `jsonlite` sowie Quarto werden benötigt. Die Standardreproduktion liest archivierte Eingaben offline. `scripts/fetch_inputs.py` lädt die kleinen Netzquellen; `scripts/fetch_gse41571.sh` lädt die vier fixierten GEO-Dateien und prüft ihre SHA-256-Werte.

Der [Auditbericht](audits/REPORT.md) dokumentiert Quellen, Akzessionen und Prüfungen. Es wurden keine proprietären SFB1123-Daten, Rohreads oder CEL-Dateien analysiert. Die Kuration ist LLM-unterstützt und besitzt keine unabhängige menschliche Zweitprüfung.
