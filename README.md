# Computational (Food) Systems Biology

Code zum Kursprojekt von Arian Gohari, Ludwig-Maximilians-Universität München.

Dieses Repository enthält ausschließlich Code, technische Dokumentation und Umgebungsdateien. Report und Präsentation werden separat als PDFs abgegeben, Teil I als Quarto-Buch. Papers, Datensätze, Ergebnisse, Obsidian-Notizen und historische Arbeitskopien liegen außerhalb des Git-Repositories.

## Code

| Ordner | Inhalt |
|---|---|
| `code/part1/` | Die sechs Kursaufgaben: dynamische Modelle, Parameterschätzung, SBML und Netzwerkanalysen |
| `code/part2/literature/` | Milch-miRNA-Inventar, Sequenzvergleich und Prüfung möglicher Targets |
| `code/part2/analysis/` | KEGG-/GENCODE-Netzwerk und Prüfung publizierter PFKL-Abbauraten |
| `code/part2/model/pfkl/` | Kontinuierliches Petrinetz für PFKL-mRNA und -Protein, Enzymmodell und Modellprüfungen |
| `code/part2/documents/` | Abbildungen, Report und Präsentation aus gespeicherten Ergebnissen erstellen |
| `code/part2/reproduction/` | Gesperrte Python-Umgebung, Reproduktionsablauf und Paketierung |
| `code/text_mining/` | Literaturauswertung für Teil I |
| `code/tools/` | Quellenexport, Quarto-Ressourcen und historische Pfadzuordnungen |

## Teil II

Das regulatorische Modell vergleicht zwei angenommene Wirkungen von miR-6517 auf menschliches PFKL: erhöhten mRNA-Abbau und verminderte Translation. Es verwendet relative Zeit und liefert bedingte Vorhersagen, keinen Nachweis einer Wirkung nach Milchkonsum.

Das Modell steht in [regulation.jl](code/part2/model/pfkl/regulation.jl), die Simulation in [simulate_regulation.jl](code/part2/model/pfkl/simulate_regulation.jl). [Umgebung und Reproduktion](code/part2/reproduction/README.md) beschreiben die benötigten Eingaben und die Befehlsfolge.

```sh
uv sync --locked --project code/part2/reproduction
julia --startup-file=no --project=code/part2/model -e 'using Pkg; Pkg.instantiate()'
uv run --offline --locked --project code/part2/reproduction python code/part2/reproduction/replay.py --list
```

Eine Git-Kopie allein reicht nicht für den vollständigen Replay. Dafür werden die im Code dokumentierten lokalen Quellen unter `data/`, der Quellenkatalog unter `obsidian/Projekt/`, die Dokumentquellen unter `report/` und `presentation/` sowie der gespeicherte Bibliografie-Herkunftsnachweis benötigt. Die Skripte laden diese Dateien nicht automatisch nach. Verweise auf diese Ordner und auf `archive/` beziehen sich auf die vollständige lokale Projektablage.

Die lokale Ablage bleibt funktional gegliedert: `report/`, `presentation/`, `code/`, `data/`, `output/`, `archive/` und `obsidian/`. Nur `code/` wird hier veröffentlicht.

Geprüfter Stand: 42 Schritte des vollständigen lokalen Reproduktionsablaufs bestanden, einschließlich Report- und Präsentationsbuild; zwölf Tests für Sequenzsuche und Milchproben-Zuordnung bestanden. Die entfernte Fettzell-RNA-/SGBS-Auswertung gehört nicht mehr zum aktiven Code.
