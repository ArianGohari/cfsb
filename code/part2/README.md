# Teil II: miR-6517/PFKL

Das kontinuierliche Petrinetz vergleicht erhöhten mRNA-Abbau mit verminderter Translation. Die simulierte Wirkung auf menschliches PFKL ist eine Annahme, kein Nachweis einer Wirkung nach Milchkonsum.

| Ordner | Aufgabe |
|---|---|
| [literature/milk_inventory/](literature/milk_inventory/README.md) | Milchbelege, Sequenzen und Targets prüfen |
| `analysis/` | KEGG-/GENCODE-Netzwerk und PFKL-Abbauraten |
| `model/pfkl/` | Petrinetz, Enzymmodell und Modellprüfungen |
| `documents/` | Abbildungen, Report und Präsentation bauen |
| `tests/` | Sequenzsuche und Milchproben-Zuordnung prüfen |
| [reproduction/](reproduction/README.md) | Umgebung und Gesamtlauf |

Modell: [regulation.jl](model/pfkl/regulation.jl). Simulation: [simulate_regulation.jl](model/pfkl/simulate_regulation.jl). Der separate Enzymfit in `fit_enzyme.py` liefert keine mRNA-/Proteinabbauraten.

```sh
uv sync --locked --project code/part2/reproduction
uv run --offline --locked --project code/part2/reproduction python -m unittest discover -s code/part2/tests
```

Einzelskripte schreiben nach `output/part2/`; der Gesamtlauf arbeitet in einer separaten Kopie. Frühere miR-146a- und RNA-/SGBS-Auswertungen bleiben im lokalen Archiv.
