# Regelbasiertes Text-Mining

Literatur suchen, Volltexte prüfen und einfache Relationssätze extrahieren. Der Standardlauf verwendet deterministische Regeln und benötigt keinen LLM-Zugang.

## Offline-Demo

Python ab 3.11, `uv` und Graphviz (`dot`) vorausgesetzt:

```sh
cd code/text_mining
uv sync --locked
uv run snakemake --cores 1
```

Ergebnis: `../../output/text_mining/rules-demo/graph.svg`. Texte und Annotationen sind synthetisch. Für Wiederholungen mit geändertem Code einen neuen Ordner über `--config out=../../output/text_mining/<name>` wählen.

Alternativ ohne Snakemake:

```sh
uv run litmine run --config examples/rules/config.json --out ../../output/text_mining/rules-cli
```

## Eigene Eingaben

Konfiguration: Suchbegriffe, `processing_mode: "rules"`, `offline` und lokale Texte über `seeds[].fulltext_path`. Pfade gelten relativ zur Konfigurationsdatei. Lokale Annotationen folgen [diesem Beispiel](examples/rules/annotations.json); Offsets zählen Unicode-Zeichen.

Mit `offline: false` werden Europe PMC, PubTator und optional UniProt abgefragt. Treffergrenzen stehen in der Konfiguration. Lokale Texte werden nicht hochgeladen. PDFs vorher in Text umwandeln.

```sh
uv run litmine run --config config.local.json --out ../../output/text_mining/mein-lauf
```

`clock_cancer` und `task4_caco2_sarscov2` prüfen Themen- und Untersuchungsbelege unabhängig vom Extraktionserfolg. `legacy_clock` erhält das alte Screening. Für Aufgabe 4: [Konfiguration](config.task4.json) und [Auswertung](docs/task4.md); die dort benötigten Volltexte liegen nur lokal.

## Ergebnisse und Grenzen

Ein Lauf enthält Such-/Entscheidungsprotokolle, `review.json`, `qc.json`, PRISMA-Zählwerte, fünf Parquet-Tabellen, LadybugDB und `graph.svg`. Fehlende Volltexte bleiben `not_retrieved`; unklare Formulierungen führen zur Enthaltung. Ein Abstract ersetzt keinen Volltextbeleg.

Der Standard-Graph enthält `auto_pass`-Belege. `graph.scope: "own_experiment"` verlangt zusätzlich eine entsprechende Attribution; `"reported_assertions"` nimmt auch `assertion_pass` auf. Prüfstatus und Zitat bestätigen keine biologische Wahrheit. Ohne unabhängigen Goldstandard bleibt die fachliche Qualität `not_evaluated`.

## Replay und Tests

```sh
uv run litmine replay --from-run ../../output/text_mining/rules-demo --out ../../output/text_mining/rules-replay
uv run python -m unittest discover -s tests -q
```

Replay verwendet gespeicherte Antworten; Code und Regelversion müssen übereinstimmen. Bestehende Läufe nicht überschreiben. Der [frühere LLM-Entwurf](docs/README.md) und explizite Legacy-Konfigurationen bleiben getrennt vom Standardlauf.
