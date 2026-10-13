# miR-6517-Auswertung reproduzieren

Der gemeinsame Einstieg berechnet die Teil-II-Auswertung aus den gespeicherten Quellen neu, einschließlich der ergänzenden PFKL-Analysen, des Typst-Berichts und der Ergebnispräsentation. Die alten miR-146a-Replays bleiben separat.

## Start

Aus der Projektwurzel:

```sh
uv sync --locked --project code/part2/reproduction
uv run --offline --locked --project code/part2/reproduction python code/part2/reproduction/replay.py
```

Die Installation kann Internet benötigen. Der anschließende Analyselauf verwendet lokale Eingaben und stellt keine neuen Literatur- oder Datenbankabfragen. Er legt eine unabhängige Kopie unter `output/reproduction/mir6517_<Zeitstempel>/` an und benötigt etwa 1,5 GB zusätzlichen Speicher. Originale und bisherige Ergebnisse werden nicht überschrieben.

Die neue Berichtsfassung liegt dort unter `workspace/output/pdf/part2_report.pdf`, die Folien unter `workspace/output/presentation/ergebnisse_mir6517.pdf`. `steps.json` und `logs/` enthalten Befehle, Laufzeiten und Ausgaben; `summary.json` den Prüfstatus. Mit `--list` lässt sich die Befehlsfolge anzeigen, mit `--output /absoluter/pfad` ein noch nicht vorhandener Zielordner wählen. Nach einem Fehler beginnt eine Wiederholung in einer neuen Kopie.

## Umgebung

| Bestandteil | Festlegung |
|---|---|
| Python | 3.14.6; vollständige Paketstände in `uv.lock` |
| Julia | 1.12.7; `../model/Project.toml` und `Manifest.toml` |
| Dokumente und Grafiken | Typst, Graphviz (`dot`), Poppler (`pdftotext`); Arial, Libertinus Serif, DejaVu Sans; lokale Roboto-Dateien für die Folien |

Julia-Pakete bei Bedarf installieren:

```sh
julia --startup-file=no --project=code/part2/model -e 'using Pkg; Pkg.instantiate()'
```

Geprüft ist eine unabhängige Dateikopie mit vorhandenen Paketen unter macOS/Apple Silicon. Eine Neuinstallation auf einem fremden Rechner wurde nicht getestet. Andere Schriftarten, Graphviz- oder numerische Bibliotheken können Dateiunterschiede verursachen. `environment.json` halten die verwendete Umgebung fest.

## Reihenfolge und Eingaben

Die aktuellen Befehle stehen in `replay.py`:

| Abschnitt | Eingaben und Ergebnisse |
|---|---|
| Literatur und Sequenzen | Gesicherte Papers, Supplemente, Suchantworten und kuratierte Notizen; Milch-Inventar, Auswahlfluss, Referenzvergleich, humane UTR-Motive und Evidenztabellen |
| Ergänzende Parameterdaten | RNADecayCafe, Doherty und Chen; nachvollziehbare Tabellenentnahmen, Zellkontexte und Grenzen; keine neue biologische Kalibrierung |
| Modellierung | Lynch-Enzymmessungen und dokumentierte Annahmen; Enzymanpassung, interne Vorhersageprüfung, regulatorische Petrinetz-Szenarien und synthetische Parameterschätzbarkeit |
| Dokumente | Bericht und Ergebnispräsentation aus den neu berechneten Ergebnissen |

Das Netzwerk verwendet KEGG-Reaktionszuordnungen und GENCODE-Bindestellen. Die entfernten RNA-/SGBS-Auswertungen und ihre R-Umgebung gehören nur noch zum [historischen Ablauf](../../../archive/rna_context_20261013/README.md).

Benötigt werden `data/`, `obsidian/Projekt/`, `code/part2/`, `code/tools/`, `report/typst/`, `presentation/ergebnisse_mir6517/` und die Roboto-Schriften unter `presentation/assets/fonts/`. PDFs und große Referenzen können in einer reinen Git-Kopie fehlen. Sie müssen aus dem dokumentierten lokalen Datenbestand ergänzt werden; der Einstieg lädt nichts nach.

Berechnete Ergebnistabellen werden nicht in die Arbeitskopie übernommen. Einzige redaktionelle Ausnahme ist `output/part2/review_summary/bibliography_sources.json`, der Herkunftsnachweis der Bibliografie. `input_manifest.json` verzeichnet die kopierten Eingaben mit SHA-256.

## Dateivergleich

`passed` setzt voraus, dass alle Befehle abgeschlossen sind, Kernergebnisse vorliegen und kopierte Eingaben, Originaleingaben sowie bisherige Ergebnisse unverändert geblieben sind. Unerklärte Ergebnisabweichungen ergeben einen Fehlerstatus.

`comparisons.json` unterscheidet identische, neue und geänderte Dateien. Herkunftsmanifeste und R-Sitzungsinformationen werden als Metadaten gesondert ausgewiesen. Vier historische Literaturexporte haben dokumentierte Kurationsänderungen: `studies.tsv`, `target_screen/candidates.tsv`, `additional_candidates/target_pairs.tsv` und der Quellenkatalog `Quellen.tsv`. Zwei Prüfdateien enthalten außerdem geänderte Code-Prüfsummen nach der Formatierung. Nur die einzeln geprüften Vorher-/Nachher-Hashes in `documented_curation_differences.json` werden akzeptiert. Die historischen Tabellen werden nicht überschrieben.

Der aktuelle Nachweis und der frühere 44-Befehle-Lauf sind in der [Reproduktionsnotiz](../../../obsidian/Projekt/Datenauswertung/Reproduktion%20der%20miR-6517-Auswertung.md) getrennt dokumentiert. Die ergänzenden Analyseskripte können weiterhin einzeln ausgeführt werden; ihre Eingaben müssen dann bereits vorhanden sein.

## Grenzen

Der Ablauf wiederholt Berechnungen aus gespeicherten Quellen. Er wiederholt keine Recherche mit aktuellen Suchmaschinen, keine unabhängige Studienauswahl und keine visuelle Volltextlektüre. Manuell entnommene Angaben bleiben belegte Eingaben. Technische Reproduzierbarkeit bestätigt weder eine humane miR-6517-Targetwirkung noch eine Wirkung nach Milchkonsum.

## Report language and layout

The report is now English and uses the vendored kunskap 0.1.0 template. The presentation remains German with its existing colours. `build_report.py` generates separate English report figures from saved outputs; it does not refit models. Full analysis replays and document-only rebuilds record their verification scope separately.
