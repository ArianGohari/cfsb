# Aufgabe 6: quantitativer Analysebericht

Stand: 24.09.2026

## Fragestellung und Analyseeinheiten

Die Analyse prüft, wie sich das kuratierte Mausnetz an öffentliche Expressionsdaten anbinden lässt. GSE97310 enthält drei veröffentlichte 10X-Countmatrizen für gesunde Aorta sowie 11 und 20 Wochen HFD. Jede Matrix ist eine aggregierte Bedingung ohne rekonstruierbare Tier-IDs. Sie wurde deshalb nur deskriptiv ausgewertet.

Für statistische Tests wurden GSE17256 und GSE18565 verwendet. GSE17256 hat vier getrennte Maus-Pools pro Monozyten-Subset; jeder Pool umfasst laut GEO fünf Tiere. GSE18565 hat drei menschliche Spender mit beiden Monozyten-Subsets. Die biologische Replikation liegt damit auf Pool- bzw. Spenderebene, nicht auf Zell- oder Probe-Set-Ebene.

## Methode

Die von GEO bereitgestellten GC-RMA-Werte wurden log2-transformiert. Das Hauptmodell blockiert die Nummer der gemeinsamen Sortierung bzw. des Spenders und testet mit `limma` den Kontrast klassisch minus nichtklassisch. Die Probe-Set-Analyse korrigiert je Plattform alle Tests mit Benjamini-Hochberg. Für die gezielte Analyse wurden eindeutig annotierte Probe-Sets je Gensymbol auf der log2-Skala gemittelt. Sieben Genprogramme waren vor der Modellanpassung festgelegt; ihr Score ist der Mittelwert der innerhalb einer Spezies z-standardisierten Genexpression.

Der Maus-Mensch-Vergleich enthält 18 vorab gewählte Paare, die am 24.09.2026 von der offiziellen NCBI-Datasets-Orthologschnittstelle bestätigt wurden. 17 Paare waren in beiden Plattformannotationen eindeutig messbar. Die gespeicherten JSON-Antworten und alle GEO-Eingaben sind über `analysis/source_manifest.tsv` fixiert.

## Ergebnisse

In GSE17256 lagen 7.537 von 45.101 Probe-Sets bei FDR < 0,05, in GSE18565 8.693 von 54.675. Die beiden Vergleiche trennen Monozyten-Subsets und messen keinen Krankheitseffekt.

Unter den sechs murinen Netzwerkgenen waren Ccr2 höher (log2-FC 1,969; FDR 0,000040), Cx3cr1 niedriger (-0,370; FDR 0,0443), Il1b niedriger (-1,621; FDR 0,000031) und Abca1 niedriger (-0,483; FDR 0,0083) in Ly6C-hohen Zellen. Für Abcg1 und Ccr5 ergab die gezielte Korrektur keinen gesicherten Unterschied. Alle Zahlen stehen in `analysis/selected_gene_results.tsv`.

Das klassische Monozytenprogramm war in Ly6C-hohen Zellen höher, das patrouillierende Programm niedriger. Das neutrophile Granulaprogramm war ebenfalls höher. Da sortierte Monozyten gemessen wurden, wird dieser Score als Transkriptionsprogramm und nicht als Neutrophilenanteil interpretiert.

Im Orthologsatz stimmten 9 von 17 Effektrichtungen überein. Die Spearman-Korrelation der log2-Fold-Changes betrug 0,0784 (p = 0,7648). Ein gemeinsamer Speziestrend ist in diesem kleinen Satz nicht nachweisbar. Die gepaarte und ungepaarte Sensitivitätsanalyse ergab bei allen 56 geprüften Gen- und Programmeffekten dieselbe Richtung.

GSE97310 umfasst 401, 956 und 1.219 Barcodes. Alle sechs Netzwerkgene und alle 26 Gene der erweiterten Programmliste waren in jeder Matrix annotiert. Es wurden keine statistischen Tests zwischen den drei Aggregaten gerechnet.

## Grenzen

Die Arraydaten stammen aus Blutmonozyten gesunder Tiere und Menschen. Sie prüfen keine Atheroskleroseprogression, keine Plaque-Zellzustände und keine Netzwerkkanten. GSE97310 hat für die vorhandenen Matrizen keine Varianz zwischen Tieren. Die mRNA-Daten messen weder Proteinaktivität noch reife miRNA oder metabolischen Flux. Programm-Scores hängen außerdem von der festgelegten Genliste und der älteren Plattformannotation ab.

## Reproduktion und Prüfung

Ausführung aus der Projektwurzel:

```bash
python3 -B part1/task6/scripts/fetch_analysis_sources.py
python3 -B part1/task6/scripts/build_network.py
Rscript part1/task6/scripts/analyze_monocyte_arrays.R part1/task6
python3 -B part1/task6/scripts/analyze_gse97310.py
rsvg-convert -w 1656 -o part1/task6/figures/quantitative_results.png part1/task6/figures/quantitative_results.svg
python3 -B part1/task6/scripts/validate_analysis.py
quarto render part1/task6/task6.qmd --no-execute
```

Alle sieben Befehle wurden am 24.09.2026 mit Exitcode 0 ausgeführt. Der Validator prüfte fünf Quellenhashes, vier Maus-Pools, drei menschliche Spender, 45.101 und 54.675 Ergebniszeilen, sechs Netzwerkgene pro Spezies, 14 Programmtests, null GSE97310-Inferenztests und die SVG-Syntax. Der HTML-Linktest fand 79 lokale oder externe Referenzen und keine fehlende lokale Datei. Verwendet wurden R 4.6.1, `limma` 3.68.5 und `jsonlite` 2.0.0.
