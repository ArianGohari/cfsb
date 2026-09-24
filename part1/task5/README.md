# Aufgabe 5

Die Ausarbeitung ist in [task5.html](task5.html) lesbar. [task5.qmd](task5.qmd) enthält den Quelltext.

Das statische humane Evidenznetz steht als [JSON](data/network.json), [Knoten-TSV](data/nodes.tsv), [Kanten-TSV](data/edges.tsv) und [SVG](figures/network.svg) bereit. Es umfasst 22 Knoten und 18 kontextannotierte Kanten. Vorzeichen und Evidenzformen werden in der Ausarbeitung erklärt.

Ab Projektwurzel reproduzieren:

```sh
python3 part1/task5/scripts/build_network.py
quarto render part1/task5/task5.qmd --no-execute
```

Python 3, Graphviz und Quarto werden benötigt. Die Standardreproduktion liest archivierte kleine Eingaben offline. `scripts/fetch_inputs.py` kann die acht Quellen online aktualisieren; neue Metadaten können von der archivierten Fassung abweichen.

Der [Auditbericht](audits/REPORT.md) dokumentiert Quellen, Akzessionen und Prüfungen. Es wurden keine proprietären SFB1123-Daten, Countmatrizen oder Sequenzrohdaten analysiert. Featurezuordnung bedeutet keine nachgewiesene Expression. Die Kuration ist LLM-unterstützt und besitzt keine unabhängige menschliche Zweitprüfung.
