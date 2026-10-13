# Milch-miRNA-Inventar

## Annotationsprüfung

`python3 code/part2/literature/milk_inventory/audit_annotations.py` vergleicht die 16 priorisierten Kandidaten offline mit den gesicherten miRBase-/MirGeneDB-Seiten und FASTA-Dateien. Ausgabe: `output/part2/milk_inventory/annotation_audit`. `--output /tmp/ziel` erlaubt einen getrennten Replay. Abrufmanifest: `data/datasets/milk_mirna_inventory/annotation_retrieval_20261009.json`. Die Datenbanklabels bleiben als solche erhalten; fehlende Einträge werden nicht als Fehlannotation bewertet. Keine erneute Read-Auswertung und kein experimenteller Funktionsnachweis.

Erster Extraktionsblock der erweiterten Kandidatensuche: sechs Studienprofile und drei ausgewählte Haupttabellen. Keine vollständige systematische Review, keine Sequenzharmonisierung und keine Kandidatenrangliste.

## Reproduzieren

Aus der Projektwurzel, mit Python und der vorhandenen `uv`-Umgebung:

```sh
uv run --offline --with pyyaml==6.0.3 --no-project python code/part2/literature/milk_inventory/build.py
python3 code/part2/literature/milk_inventory/verify_pdf.py
uv run --offline --with pyyaml==6.0.3 --no-project python code/tools/export_source_base.py
```

`verify_pdf.py` benötigt Popplers `pdftotext`. Der Export läuft ohne Netzwerk. Diese neuen Skripte verwenden die aktuelle Ablage und benötigen keinen historischen Pfadadapter.

Eingaben:

- Unveränderte PDFs und Marker-Volltexte unter `data/sources`.
- `data/datasets/milk_mirna_inventory/extraction_manifest.json`: Prüfsummen, genaue Fundstellen, Tabellenbereiche und dokumentierte PDF-Prüfung.
- `catalogue_20261008.tsv` im selben Ordner: eingefrorener Startbestand.
- Die sechs Obsidian-Quellennotizen: bearbeitbare `Inventar*`-Eigenschaften. Historische Bewertungen bleiben erhalten.

Ausgaben unter `output/part2/milk_inventory`: Studien- und Screeningtabellen, 416 Zahlenwerte mit Herkunft, Zusammenfassungen je Studie/Name/Material, Summen und Prüfsummen. Mit `--output /tmp/ziel` lassen sich getrennte Ausgaben zum Vergleich erzeugen.

Alle Originalnamen bleiben unverändert. Die 86 Quellzeilen enthalten Nullwerte, eine neue Vorhersage und ausgewählte Teilmengen der veröffentlichten Inventare. Sie sind keine Zahl verschiedener nachgewiesener Milch-miRNAs. CPM, Reads und mittlere TPM werden nicht zusammenaddiert. Li-Gewebedaten und Krupova-Ziegenwerte werden nicht als bovine Milchnachweise exportiert.

Die Rechenregeln sind reproduzierbar. Studienauswahl, wissenschaftliche Interpretation und visuelle Prüfung bleiben dokumentierte Kurationsschritte, keine unabhängige Doppelprüfung. Fehlende Supplements und nächste Schritte stehen in der [Studienmatrix](../../../../obsidian/Projekt/Literatur/04%20Datenextraktion/Studienmatrix%20Milch-miRNAs.md).

## Vollständige Matrizen und Referenzvergleich

Stand 09.10.2026: Li S1/S2/S4/S5, Krupova Figshare/GEO und miRBase 20/21/23.1 sind lokal mit Abrufmanifesten gesichert. Die Original-XLSX-Dateien werden nur gelesen.

```sh
uv run --offline --project code/part2/reproduction --locked python code/part2/literature/milk_inventory/compare_sequences.py
```

Die vorhandene gesperrte Python-Umgebung enthält `openpyxl` 3.1.5. Der neue Export steht unter `output/part2/milk_inventory/sequence_comparison`. `--output /tmp/ziel` erzeugt eine getrennte Kopie für den deterministischen Vergleich. Die Auswertungsregeln stehen in `data/datasets/milk_mirna_inventory/sequence_comparison_protocol.json`; die Ergänzung zur Prüfung von Sequenzenden ist als nachträgliche Diagnose datiert.

Die Pipeline prüft Quellenhashes, Probenarten und den GEO-/Figshare-Abgleich. Sie reproduziert Lis fraktionsbezogene Nachweiszahlen, trennt neue Vorhersagen und vergleicht die zugeordneten reifen Referenzsequenzen mit humanen Sequenzen. Jede extrahierte Zahl besitzt Datei-, Blatt- und Zelladresse. Gleichlautende oder sequenzidentische Annotationen werden bei Studienbelegen nicht doppelt gezählt, Messwerte nicht über Studien summiert.

`annotation_review_priority.tsv` ist eine explorative Prüfliste, keine bestätigte Liste bovin-spezifischer Wirkstoffe. Eine Referenzsequenz ist kein experimenteller Nachweis derselben exakten Enden in jedem Read. Sekundärlisten anderer Publikationen werden nicht als unabhängige Messungen gezählt. Neue Quellen werden über die Quellennotizen kuratiert; der Katalog-Snapshot vom 08.10. bleibt unverändert.

## Target-Sichtung aller 16 Kandidaten

Offline aus gespeicherten PubMed-Antworten:

```sh
python3 code/part2/literature/milk_inventory/search_targets.py
python3 code/part2/literature/milk_inventory/export_target_screen.py
```

Der erste Befehl erzeugt den Trefferindex, der zweite die aktuelle Vergleichstabelle aus der Obsidian-Synthesenotiz. Originalantworten, exakte Namensvarianten, Suchwarnungen und Hashes liegen unter `data/datasets/milk_mirna_inventory/target_screen_20261009/`. Der erste Abruf erfolgte über den `ncbi-entrez`-Skill in einer isolierten Umgebung mit `requests`; der Offline-Lauf benötigt nur die Python-Standardbibliothek. Keine eigene Targetvorhersage und keine vollständige systematische Hauptsuche. Alle 16 bleiben im Prüfbestand.

## Humane kanonische Seed-Suche

```sh
python3 code/part2/literature/milk_inventory/scan_human_seeds.py
python3 code/part2/tests/test_human_seed_screen.py
```

Offline, Python-Standardbibliothek. Eingaben: GENCODE-48-FASTA/GTF mit SHA256 unter `data/datasets/milk_mirna_inventory/human_target_reference`, vorab gespeicherte Suchregeln und 16 Kandidaten aus der Annotationsprüfung. Zwei Endvarianten separat. Ausgabe: `output/part2/milk_inventory/human_seed_screen`; `--output /tmp/ziel` erlaubt getrennte Replays.

Protein-coding-Isoformen des basic-CHR-Subsets, Chromosomen 1–22/X/Y, 3′UTR ab acht Basen. Kanonische 8mer/7mer-m8/7mer-A1; keine TargetScan-Scores, Zelltypfilter oder Pathway-Auswertung. UTR- und Transkriptkoordinaten sind 1-basiert und inklusiv. GTF-Stopcodonüberlappungen werden beim unabhängigen Längenabgleich entfernt. Trefferzahlen sind keine Rangliste; fehlende Stellen schließen andere Regionen und Mechanismen nicht aus.

Tests prüfen Stellenklassen und Randfälle, unabhängige positionsweise Paarung, alle Trefferkoordinaten und deterministischen Replay. `validation.json` bezeichnet technische Prüfung, keine biologische Validierung. [Wissenschaftliche Einordnung](../../../../obsidian/Projekt/Datenauswertung/Humane%20Seed-Bindestellen%20der%20Milch-miRNA-Kandidaten.md).

## Publizierte Targetsequenzen prüfen

`python3 code/part2/literature/milk_inventory/audit_reported_targets.py` prüft die eingefrorene Volltextentnahme zu Yang/PFKL und Zhang/MAP2K2. Eingaben und Fundstellen unter `data/datasets/milk_mirna_inventory/fulltext_review_20261009`; Ausgabe `output/part2/milk_inventory/fulltext_review/sequence_audit.json`. PDF-/Text-Hashes, Abbildungssequenzen und humane GENCODE-Referenz werden nachvollziehbar verbunden. Keine stillschweigende Korrektur widersprüchlicher Angaben im Artikel.

## Pilot: Tierart und Verarbeitung

`export_processing_pilot.py` exportiert die 23 bearbeitbaren Obsidian-Befundnotizen aus fünf vorhandenen Studien. Species-Zuordnung aus Materialherkunft; zusätzliche GEO-Prüfung für Kuh-/Ziegenproben. Quelle und Fundstelle sind je Befund, Blatt/Zelle je importiertem Messwert erhalten. Keine neue Hauptsuche und kein autonomer Volltext-Scraper.

```sh
uv run --offline --with pyyaml==6.0.3 --no-project python code/part2/literature/milk_inventory/export_processing_pilot.py
uv run --offline --with pyyaml==6.0.3 --no-project python code/part2/tests/test_processing_pilot.py
```

Mit `--output /tmp/ziel` getrennt reproduzieren. Ausgabe `output/part2/milk_inventory/processing_pilot`. Base und Erläuterung: `obsidian/Projekt/Literatur/04 Datenextraktion/Milch und Verarbeitung.md`. Fehlende Werte sind keine Nullen; Panels, gemeinsame Artenzahlen und Gesamtzahlen über Prozesszustände sind keine gruppenspezifische Richness. Berichts- und nachgerechnete Werte bleiben getrennt.

## Chen-Namensaudit und Shome-Archiv

`python3 code/part2/literature/milk_inventory/audit_chen_shome.py` verarbeitet die gespeicherten ENA-Metadaten und alle 245 Chen-Namen offline (Standardbibliothek). Regeln und Abrufhashes: `data/datasets/milk_mirna_inventory/chen_shome_followup_20261009`. Ausgabe: `output/part2/milk_inventory/chen_shome_audit`; getrennten Replay mit `--output` starten. Namenskandidaten ersetzen keine historische Sequenzzuordnung. Der bestehende 270er-Sequenzpool bleibt unverändert; Shome-FASTQ wurden nicht geladen.

## Studiengrafik und publizierte Namenslisten

`plot_study_counts.py` (gesperrte Umgebung unter `code/part2/reproduction`) liest die `Diagrammwerte` aus dem aktuellen Quellenexport und erzeugt vier getrennte Studienpanels in `output/part2/milk_inventory/study_counts`. Vorher `code/tools/export_source_base.py` ausführen.

`extend_published_lists.py` (Python-Standardbibliothek) verbindet Li-/Krupova-Zeilen mit Alis Tabelle 3 unter Beibehaltung aller Fundstellen und Nachweisstatus. Der Ali-Referenzvergleich ist vorläufig (miRBase 23.1 statt 22.1); er überschreibt das historische 270-Sequenzen-Inventar nicht. Ausgabe `output/part2/milk_inventory/published_lists`.

## Gemeinsame Kandidatenevidenz

`uv run --offline --with pyyaml --no-project python code/part2/literature/milk_inventory/build_candidate_evidence.py` verbindet Milchbelege, Ali-Zuordnungen, Annotationsaudit und humane Stellenprüfung. Aktuelle Targetbefunde kommen aus den Quellennotizen; die 16er-Literaturbewertung aus ihrer Obsidian-Synthese. Alle Basissequenzen bleiben sichtbar; keine automatische Kandidatenrangliste. Ausgabe: `output/part2/milk_inventory/candidate_evidence`.

## Bae-Reporterprüfung

`uv run --offline --with pyyaml --no-project python code/part2/literature/milk_inventory/review_bae_reporter.py` liest die visuell entnommenen Abb.-5A-Sequenzen aus der Bae-Quellennotiz. Vergleich mit dem bestehenden RAP1A-Screen und lokaler GENCODE-48-FASTA; Ergebnisse und Eingabehashes unter `output/part2/milk_inventory/bae_reporter_review`. Die gezeichnete miRNA stimmt am 5′-Ende nicht mit der Inventarreferenz überein. Keine Aussage zur tatsächlich eingesetzten vollständigen Mimicsequenz.

## Begrenzte zusätzliche Kandidatenrunde

`uv run --offline --with pyyaml --no-project python code/part2/literature/milk_inventory/review_additional_candidates.py` verarbeitet die gespeicherten Elicit-Suchen und fünf editierbare Quellennotizen. Ausgabe `output/part2/milk_inventory/additional_candidates`; 151 Rundestatus, 47 Suchkandidaten, fünf vertiefte Kandidaten und acht humane Targetpaar-Prüfungen. Nutzt bestehende MirGeneDB-FASTA und GENCODE-48-Transkriptmenge. Keine funktionelle Validierung aus Seedtreffern. Quelle und Auswahlprotokoll unter `data/datasets/milk_mirna_inventory/bounded_candidate_search_20261010`.

## PFKL-Folgeprüfung

`python3 code/part2/literature/milk_inventory/review_pfkl.py` prüft GENCODE-48-Varianten und deterministische Seed-/UTR-Kontrollen. `python3 code/part2/literature/milk_inventory/review_pfkl_expression.py` prüft den GSE249195-Download und extrahiert HPA-Kontextwerte. Die GEO-Matrix ist im gesicherten Abruf unvollständig; das Skript schreibt ausdrücklich keine Expressionswerte daraus. Ergebnisse unter `output/part2/milk_inventory/pfkl_followup` und `pfkl_expression`, Eingaben unter `data/datasets/milk_mirna_inventory/pfkl_followup_20261010`. Vergleichsbruchteile sind keine Signifikanztests oder Targetwahrscheinlichkeiten.

## CASP3-Folgeprüfung

`python3 code/part2/literature/milk_inventory/review_casp3.py` wiederholt die PFKL-Kontrollregeln für MANE und getrennt eine nach dem Motivtreffer gewählte CASP3-Variante. `python3 code/part2/literature/milk_inventory/review_casp3_expression.py` prüft und extrahiert GSE144424 unter Erhalt der Personenzuordnung. Rohabrufe: `data/datasets/milk_mirna_inventory/casp3_followup_20261010`; Ableitungen: `output/part2/milk_inventory/casp3_followup` und `casp3_expression`. Keine DE-Prüfung, keine bestätigte miRNA-Wirkung.
