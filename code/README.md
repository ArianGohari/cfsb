# Code

| Ordner | Inhalt |
|---|---|
| `part1/` | Code zu den sechs Kursaufgaben, nach Aufgabe geordnet |
| `part2/literature/` | Milch-miRNA-Inventar, Sequenzvergleich und Targetsuche |
| `part2/analysis/` | Pathway-/Targetnetzwerk und publizierte PFKL-Abbauraten |
| `part2/model/` | PFKL-Enzymmodell, Petrinetz und Modellprüfungen |
| `part2/documents/` | Abbildungen, Bericht und Präsentation aus den Ergebnissen |
| `part2/tests/` | Tests der Sequenzsuche und Zuordnung von Milchproben |
| `part2/reproduction/` | Festgelegte Umgebungen, vollständige Wiederholung und Abgabepaket |
| `text_mining/` | Eigenständiges Paket für Teil I |
| `tools/` | Quellenexport, Quarto-Ressourcen, Pfadprüfung und Starter für alte Skripte |

Einstieg für das aktuelle Projekt: [Teil II](part2/README.md). Die Python-Dateien dort werden mit `ruff format code/part2 code/tools` formatiert. Historischen Code nicht automatisch umformatieren: Seine Prüfsummen gehören zur Reproduktion früherer Ergebnisse.

Frühere Teil-II-Modelle liegen unter [archive/code/part2](../archive/code/part2/README.md), ihre Hilfsprogramme unter [archive/code/tools](../archive/code/tools/README.md). Historische Skripte mit `code/tools/run.py` starten. Der Starter stellt ihre ursprünglichen Pfade in einer temporären Kopie wieder her und schreibt neue Ergebnisse nach `output/runs/`.

Beispiel für Teil I:

```sh
python3 code/tools/run.py code/part1/task1/verify_task1.py
```

Falls eine Aufgabe ein bestimmtes Arbeitsverzeichnis benötigt, vor dem Skript etwa `--cwd part1/task4` angeben. Die wissenschaftlichen Eingaben und bisherigen Ergebnisse bleiben dabei unverändert.
