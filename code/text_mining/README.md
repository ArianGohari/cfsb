# Text-Mining ohne LLM

Der Standardlauf verwendet deterministische Regeln für Screening und Relationsextraktion. Kein Ollama, kein Modellserver, kein API-Schlüssel. Suche, Volltextbeschaffung, Entity-Normalisierung, PRISMA-Zählwerte und die Exporte nach Parquet, LadybugDB und Graphviz-SVG bleiben erhalten.

## Offline ausprobieren

Voraussetzungen: Python ab 3.11, `uv`, Graphviz mit `dot` im PATH.

```sh
cd code/text_mining
uv sync --locked
uv run snakemake --cores 1
```

Ergebnis: `../../output/text_mining/rules-demo/graph.svg`. Die Demo enthält erfundenen Text und geprüfte lokale Entity-Spannen, keine vorgegebenen Modellantworten. Der Graph ist als `SYNTHETIC DEMO` gekennzeichnet.

Ohne Snakemake:

```sh
uv run litmine run --config examples/rules/config.json --out ../../output/text_mining/rules-cli
```

Bestehende Runs bleiben unverändert. Bei geänderten Eingaben oder Code einen neuen Ausgabeordner mit `--config out=../../output/text_mining/<name>` wählen. Archivierte Runs nicht mit `--forceall` überschreiben.

## Ablauf

1. Europe PMC durchsuchen und Treffer anhand ihrer Identifier zusammenführen. Suchqueries, Treffergrenzen und Rohantworten protokollieren.
2. Titel und Abstract anhand von Clock-/Checkpoint-Begriffen als Kandidaten markieren. Fehlende Begriffe bedeuten `unclear`, nicht Ausschluss. Beide Gruppen gehen zur Volltextbeschaffung.
3. OA-PMC-Volltexte oder lokale UTF-8-Texte lesen. Fehlende Volltexte bleiben `not_retrieved`. Kein Abstract-Ersatz für Volltext-Evidence.
4. Volltext anhand des Profils prüfen. `clock_cancer` (Standard) und `task4_caco2_sarscov2` benötigen Themenbelege (I1) und einen Untersuchungsbeleg (I2), aber keine erfolgreiche Relationsextraktion. Einschluss bedeutet Kandidat im Dokument-Scope, nicht nachgewiesene Biologie. `legacy_clock` erhält das alte, an Relationssätze gekoppelte Screening. Eine eindeutige Selbstbeschreibung als Review kann zum Ausschluss führen.
5. PubTator-Annotationen exakt am Text verankern. Optional eindeutige reviewed UniProt-Zuordnungen aus GeneIDs ergänzen. Lokale Annotationen sind ebenfalls möglich.
6. Einfache aktive/passive Relationssätze erkennen und mit dem gemeinsamen Validator prüfen. Unklare Typen/Identifier, Verneinungen, Spekulationen und komplexe Satzfortsetzungen führen zur Enthaltung.
7. Entscheidungen, QC, PRISMA-Kontrollzahlen und optional Goldstandard-Metriken schreiben.
8. Fünf Parquet-Tabellen und LadybugDB exportieren. Abschließend `graph.dot` mit Graphviz nach `graph.svg` rendern.

Die Regeln stehen in `litmine/rules.py` und verwenden die eingebauten Kriterien; abweichende `criteria` werden abgewiesen. Im Regelbetrieb wird jeder Volltext am Stück geprüft, damit Zeichenlimits keine Verneinung vom Satz abschneiden. Die alten `chunking`-Werte gelten nur für den Legacy-LLM-Modus. Beispiele: `PER2 binds TP53.` oder `TP53 is stabilized by PER2.`. Eigene Experimente werden nur bei einer direkten Formulierung wie `We demonstrated that PER2 binds TP53.` zugeordnet. Ein bloßer Relationssatz behält unbekannte Attribution. Neue Profile kennzeichnen ihn als `assertion_pass`, sofern keine weiteren Validierungsprobleme vorliegen; `legacy_clock` behält `uncertain`. Gemeinsames Auftreten zweier Namen ergibt keine Relation. `ACTIVATES` und `INHIBITS` sind gerichtete Textaussagen; `UPREGULATED_IN` und `DOWNREGULATED_IN` verbinden einen ausdrücklich genannten Analyten mit einer Zelllinie und behaupten keine kausale Regulation.

Die Regeln erfassen bewusst nur einen kleinen Teil wissenschaftlicher Formulierungen. Satzerkennung, Abschnitte, Referenzen und OCR können die Auswahl verzerren. Auch ein eindeutiger Satz kann fachlich falsch sein oder fremde Ergebnisse wiedergeben. `auto_pass` prüft Schema und Textbeleg, nicht biologische Wahrheit. Kontext wie Zelllinie oder Versuchsbedingung wird nicht geraten; die Taxonomie eines Proteins beweist nicht die untersuchte Spezies.

## Öffentliche Literatur verarbeiten

`config.local.json` verwendet jetzt `processing_mode: "rules"`. Die unveränderte Suchgrenze von 20 Treffern dient als Pilot; für größere Läufe `search.max_records` und gegebenenfalls `max_protein_lookups` bewusst erhöhen.

```sh
uv run snakemake --cores 1 \
  --config pipeline_config=config.local.json out=../../output/text_mining/rules-pilot-001
```

`offline: false` erlaubt öffentliche GET-Anfragen an Europe PMC, PubTator und UniProt. PubTator ist ein externer, modellbasierter Annotationsdienst, aber kein generatives LLM. Die Pipeline fragt vorhandene Annotationen über PMID ab; sie lädt keine lokalen Volltexte zu einem Modell hoch. Für einen komplett lokalen Lauf `offline: true`, lokale Volltexte und `annotations` konfigurieren.

Dateipfade sind relativ zur Konfigurationsdatei. Lokale Volltexte kommen über `seeds[].fulltext_path`; Marker-Markdown ist möglich, PDF-Konvertierung gehört nicht zum Lauf. Annotationen verwenden `annotations: {"PMID:...": "datei.json"}` und das Format aus `examples/rules/annotations.json`. Offsets zählen Unicode-Zeichen, keine Bytes. Erlaubte Identifier: NCBIGene, UniProt, NCBITaxon und Cellosaurus (`Cellosaurus:CVCL_0025` etwa für Caco2).

PubTator- und Dokumenttexte stimmen oft nicht vollständig überein. Eindeutige Passagen werden mit längenerhaltender Whitespace-Normalisierung verankert. Fehlt eine Passage, ist ein eindeutiger vollständiger Satz mit mindestens sechs Wörtern als Fallback erlaubt. Der Entity-Text muss immer exakt übereinstimmen. Es gibt kein unscharfes Matching und keine Übertragung von Aliasnamen in andere Sätze; Lücken erscheinen in QC. UniProt-Mapping ergänzt Proteinkandidaten, ändert aber nicht stillschweigend Gene in Proteine. Bei mehreren für dasselbe Prädikat zulässigen Argument-Identitäten enthält sich die Regel.

## Ergebnisse und Replay

Jeder Run enthält `review.json`, `manifest.json`, `records.csv`, `screening.csv`, `prisma_counts.json`, `qc.json`, `report.md`, `evaluation.json`, fünf Parquet-Tabellen (`papers`, `documents`, `entities`, `relations`, `evidence`), `graph.lbug`, `graph.dot`, `graph.svg` und `graph_export.json`.

Unter `raw/` liegen Beschaffungssnapshots, unter `rules/` die deterministischen Eingaben und Entscheidungen. Manifest und QC nennen Verarbeitungsmodus, Regelversion und Code-Hashes. `llm_calls` ist im Regelbetrieb 0; es entsteht kein LLM-Verzeichnis.

Alle Evidence-Zeilen bleiben in Parquet. `graph.scope: "attributed"` (Standard) exportiert `auto_pass`; `"own_experiment"` verlangt zusätzlich diese Attribution. `"reported_assertions"` nimmt auch `assertion_pass` mit unbekannter Attribution auf. Scope und Status stehen in Graph und Exportbeleg. Keiner dieser Modi bestätigt unbekannten Kontext. Nur eingeschlossene Volltexte gelangen in den Graph; Papers ohne geeignete Evidence bleiben sichtbar. Der Export bricht standardmäßig oberhalb von 500 Knoten ab, statt still zu kürzen. `graph.max_nodes: null` hebt die Grenze auf, kann aber viel Speicher benötigen.

```sh
uv run litmine replay --from-run ../../output/text_mining/rules-demo --out ../../output/text_mining/rules-replay
uv run litmine export --review ../../output/text_mining/rules-demo/review.json --out ../../output/text_mining/rules-rebuilt
```

Replay liest die Beschaffungssnapshots offline und berechnet die Regeln erneut. Für identische Ergebnisse müssen Code und Regelversion übereinstimmen. Laufpfade und Provenienz dürfen sich unterscheiden; die fachlichen Tabelleninhalte bleiben beim gleichen Code gleich.

Alte explizite LLM-Konfigurationen und ihre Tests bleiben aus Kompatibilitätsgründen erhalten. Neue Konfigurationen ohne `llm` verwenden Regeln; `processing_mode: "rules"` erzwingt Regeln auch bei einem verbliebenen LLM-Block. Die alte Fixture-Demo unter `examples/demo/` ist kein Standardlauf mehr.

## Task4: vorhandenen Korpus verarbeiten

```sh
cd code/text_mining
uv run litmine run --config config.task4.json --out ../../output/text_mining/task4-new-run
```

Die Konfiguration enthält 29 lokale Volltexte aus `data/sources/part1/task4/corpus/`. Sie lädt keine Texte hoch. PMID33898942 ist Entwicklungsdaten; die anderen Papers dürfen nicht anhand späterer Evaluationslabels nachoptimiert werden. Regeln, Scope, Grenzen und gemessene Ergebnisse stehen in `docs/task4.md`. Für Wiederholungen stets einen neuen Ausgabeordner wählen.

## Prüfung und wissenschaftliche Grenzen

```sh
uv run python -m unittest discover -s tests -q
uv run litmine evaluate --review ../../output/text_mining/rules-demo/review.json \
  --gold mein_goldstandard.json --out ../../output/text_mining/rules-demo/evaluation-gold.json
```

Tests prüfen unter anderem Richtungen, Verneinungen, Enthaltungen, Replay ohne LLM und tatsächliche Parquet-/LadybugDB-/SVG-Exporte. Ohne unabhängigen Goldstandard bleibt die wissenschaftliche Qualität `not_evaluated`. Der zusätzliche einfache Extraktionsbaseline-Vergleich ist auf bereits eingeschlossene, annotierte Texte beschränkt, kein unabhängiger End-to-End-Vergleich.

Die Unterlagen unter `docs/` beschreiben teilweise noch den früheren LLM-Entwurf. Für den jetzigen Ablauf gilt diese README. Das Suchprotokoll ist weiterhin ein Entwurf; vor einer Hauptauswertung müssen Suchumfang, Einschlussregeln und Review-Typ festgelegt werden. PRISMA-Zählwerte ersetzen weder eine Studienzuordnung noch eine Biasbewertung. `graph.svg` ist der Knowledge Graph, kein PRISMA-Flussdiagramm.

Archivierte Läufe liegen unter `../../archive/text_mining/data/runs/`. Für Replay `--from-run` auf diesen Ordner setzen und für `--out` einen neuen Ordner unter `../../output/text_mining/` wählen.

Archivierte Läufe liegen unter `../../archive/text_mining/data/runs/`. Für Replay `--from-run` auf diesen Ordner setzen und für `--out` einen neuen Ordner unter `../../output/text_mining/` wählen.
