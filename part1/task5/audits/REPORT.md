# Abschlussaudit Aufgabe 5

Stand: 23.09.2026. Die Arbeit enthält eine gezielte Literaturkuration und eine reale Metadaten-/Featureprüfung; sie enthält keine eigene differenzielle Expressionsanalyse.

## Quellen und Identitäten

Sechs eingeschlossene Primärstudien, vier registrierte Alternativen beziehungsweise nicht übernommene Kandidaten. Entscheidungen mit DOI in `data/screening.tsv`. Kantenquellen und Fundstellen in `data/edges.tsv`; Vollzitate in `data/sources.tsv`.

Alle neun NCBI-Genanker wurden gegen die gespeicherte ESummary-Antwort geprüft: ABCA1 19, IL1B 3553, TNF 7124, TREM2 54209, CD14 929, FCGR3A 2214, TLR2 7097, CXCL8 3576 und ICAM1 3383. Alle Taxon 9606. Der miRNA-Arm ist hsa-miR-33a-5p, MIMAT0000091; die passende miRBase-Seite liegt lokal vor. TASK5-IDs kennzeichnen lokale Konzepte und werden nicht als externe Ontologie-IDs ausgegeben.

GSE253904 enthält die SubSeries GSE253902/253903. GSM8029950 und GSM8029951 sind GEX-/ADT-Einträge derselben benannten Probe. Die dokumentierte Zahl von 12 CITE-seq-GSM-Einträgen wurde nicht als 12 Personen interpretiert. Die Differenz zwischen der Gesamtzahl in der Publikation (21 Läsionen) und den Personenangaben der beiden GEO-Serien (6 und 12) wird im Text offengelegt, ohne eine unbelegte Probenzuordnung zu erfinden.

## Prüfungen

- `python3 part1/task5/scripts/build_network.py`: PASS. 22 eindeutige Knoten, 18 referenziell gültige Kanten, gültige Quellen/Taxonomie/Vorzeichen.
- 36.884 heruntergeladene Featurezeilen: 36.601 RNA und 283 Antikörpermerkmale. Alle neun Genknoten eindeutig über Symbole auf Ensembl-Features abgebildet. Dies ist kein Expressionsnachweis.
- Download-Prüfsummen gegen `data/provenance.json`: PASS für acht kleine Originaleingaben.
- `quarto render part1/task5/task5.qmd --no-execute`: PASS, selbstständiges HTML mit eingebetteter SVG.
- SVG als PNG betrachtet: lesbare Knoten und H-IDs, keine überlappenden Beschriftungen. H18 nennt den Kristall-Co-Stimulus auch in der Zeichnung.
- Stilaudit: keine langen Gedankenstriche oder typografischen Anführungszeichen im QMD.

## Fachliche Schutzmaßnahmen gegen Fehlinterpretation

Keine humane miR-33a→ABCG1-Kante. Keine generische NET→TLR9-Kante. Keine Kausalvorzeichen auf Markerbeziehungen. NET-induzierte IL1B-RNA und Kristall-abhängige Freisetzung reifen IL-1β sind getrennt. Endothelkanten sind nicht als makrophagenintrinsisch annotiert. Neun gerichtete Effektkanten besitzen Vorzeichen, neun Marker-/Beteiligungsrelationen haben `unknown`.

Die vier Evidenzklassen sind Methodenklassen, keine kalibrierten Wahrscheinlichkeiten. Kontextfelder dürfen bei der weiteren Netzverwendung nicht wegfallen. Eigene lokale Diagramm- und Exportdateien sind deterministisch aus dem Skript reproduzierbar. Web-Suchergebnisse und nicht archivierte Volltexte sind nicht vollständig offline rekonstruierbar; diese Grenze steht im Suchprotokoll.
