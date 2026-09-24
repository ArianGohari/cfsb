# Aufgabe 1f: KEGG und ConsensusPathDB

Stand: 20.09.2026. Erstabruf 16:03:16–16:04:39 UTC, CPDB-Nachtrag bis 16:10:31 UTC. Vor dem Nachtrag wurde um 16:08:29 UTC das [Amendment](amendment.json) dokumentiert: ursprüngliches Budget 14, ausdrücklich genehmigte Erweiterung um maximal 8, Gesamtlimit 22 Requests. Alle 22 wurden genutzt. Nur öffentliche Quellen, keine Credentials, keine Simulation. Änderungen ausschließlich in `text_mining/pilot_task1f/pathways/`; die QMD bleibt beim Hauptagenten.

## Ergebnis für die QMD

KEGG enthält die menschlichen Einträge [hsa04710, Circadian rhythm](https://rest.kegg.jp/get/hsa04710) und [hsa04115, p53 signaling pathway](https://rest.kegg.jp/get/hsa04115). Ihre Genlisten und die separat abgerufenen KGML-Dateien stimmen überein: Die Uhrkarte umfasst 34 unterschiedliche Gene, die p53-Karte 75. Die beiden Genlisten haben in diesem Abruf keine Schnittmenge. Das betrifft genau diese Karten, nicht sämtliche KEGG-Einträge oder die biologische Vernetzung beider Prozesse.

| Zielgen | KEGG-Gene-ID | hsa04710 | hsa04115 |
|---|---|---|---|
| PER2 | hsa:8864 | enthalten | nicht enthalten |
| TP53 (p53) | hsa:7157 | nicht enthalten | enthalten |
| MDM2 | hsa:4193 | nicht enthalten | enthalten |
| ARNTL/BMAL1 | hsa:406 | enthalten | nicht enthalten |
| CLOCK | hsa:9575 | enthalten | nicht enthalten |

Präsenz wurde anhand der numerischen Gene-IDs geprüft, nicht nur anhand sichtbarer Beschriftungen. Der [abgerufene Geneintrag](https://rest.kegg.jp/get/hsa:406+hsa:8864+hsa:7157+hsa:4193+hsa:9575) bestätigt ausdrücklich BMAL1 und ARNTL als Namen von hsa:406. Die Prüfung erfasst Genmitgliedschaft, keine gewebespezifische Expression oder Aktivität.

Im [p53-KGML](https://rest.kegg.jp/get/hsa04115/kgml) sind zwei eindeutige Relationen zwischen den Zielgenen gespeichert: TP53 → MDM2 als `PPrel/activation` (Knoten 50 → 49) und als `GErel/expression` (50 → 51). Das sind direkte Kanten im Datenbankgraphen; daraus folgt nicht automatisch ein experimenteller Nachweis direkter physischer Bindung. Eine umgekehrte MDM2 → TP53-Relation ist in dieser KGML-Datei nicht enthalten. Der bekannte Abbaumechanismus darf deshalb nicht als hier abgerufene Kante ausgegeben werden; Bilddarstellung und Literatur wurden dafür nicht separat geprüft.

Im [Uhr-KGML](https://rest.kegg.jp/get/hsa04710/kgml) führt die Gruppe 86 aus BMAL1 und einem gemeinsamen NPAS2/CLOCK-Knoten zum gemeinsamen PER1/PER2/PER3-Knoten 16. Die Relation ist als `PPrel` ohne Subtyp gespeichert. Sie belegt keine eindeutige Einzelgenkante CLOCK → PER2 und enthält keine explizite Aktivierungs- oder Hemmungsangabe. Die Beschreibung des Pathways erläutert CLOCK/BMAL1- und PER/CRY-Rückkopplungen auf Textebene. Diese Beschreibung ersetzt keine eindeutige Kantenannotation. Die [offizielle KGML-Dokumentation](https://www.kegg.jp/kegg/xml/docs/) unterscheidet Proteinrelationen (`PPrel`) und Genexpressionsrelationen (`GErel`).

Eine PER2–TP53- oder PER2–MDM2-Kopplung ist durch die beiden abgerufenen Karten nicht belegt. Die Uhrkarte verweist allerdings auf Fu und Lee (2003), *The circadian clock: pacemaker and tumour suppressor* ([PMID 12724733](https://pubmed.ncbi.nlm.nih.gov/12724733/), [DOI 10.1038/nrc1072](https://doi.org/10.1038/nrc1072)). Das ist ein thematischer Literaturhinweis zur Verbindung mit Krebs, keine spezifisch annotierte Kopplungskante. Auch gemeinsame Gene, falls sie in anderen Pathway-Abgrenzungen vorkommen, wären allein kein Beweis mechanistischer Kopplung.

## Konkrete Einträge und Literaturprovenienz

Pathway-IDs sind von Publikations-IDs zu trennen. Die folgenden DOI/PMID gehören zu Referenzen der Einträge beziehungsweise zur CPDB-Datenbankpublikation, nicht zu einem eigenständigen DOI der Pathway-Karte.

| Eintrag / Quelle | Abgerufene Referenz | PMID | DOI |
|---|---|---|---|
| hsa04710 / KEGG, Raw 01 | Takahashi (2017), *Transcriptional architecture of the mammalian circadian clock* | [27990019](https://pubmed.ncbi.nlm.nih.gov/27990019/) | [10.1038/nrg.2016.150](https://doi.org/10.1038/nrg.2016.150) |
| hsa04710 / KEGG, Raw 01 | Fu, Lee (2003), *The circadian clock: pacemaker and tumour suppressor* | [12724733](https://pubmed.ncbi.nlm.nih.gov/12724733/) | [10.1038/nrc1072](https://doi.org/10.1038/nrc1072) |
| hsa04115 / KEGG, Raw 02 | Harris, Levine (2005), *The p53 pathway: positive and negative feedback loops* | [15838523](https://pubmed.ncbi.nlm.nih.gov/15838523/) | [10.1038/sj.onc.1208615](https://doi.org/10.1038/sj.onc.1208615) |
| hsa04115 / KEGG, Raw 02 | Levine et al. (2006), *The P53 pathway: what questions remain to be explored?* | [16557269](https://pubmed.ncbi.nlm.nih.gov/16557269/) | [10.1038/sj.cdd.4401910](https://doi.org/10.1038/sj.cdd.4401910) |
| CPDB / NCBI PubMed, Raw 13 | *ConsensusPathDB 2022: molecular interactions update as a resource for network biology* | [34850110](https://pubmed.ncbi.nlm.nih.gov/34850110/) | [10.1093/nar/gkab1128](https://doi.org/10.1093/nar/gkab1128) |
| CPDB / NCBI PubMed, Raw 13; auch auf CPDB-Startseite genannt | *The ConsensusPathDB interaction database: 2013 update* | [23143270](https://pubmed.ncbi.nlm.nih.gov/23143270/) | [10.1093/nar/gks1055](https://doi.org/10.1093/nar/gks1055) |

Alle 7 Uhr- und 15 p53-Referenzen einschließlich DOI/PMID stehen in den Raw-Antworten 01/02; die Offline-Ausgabe listet sämtliche ID-Paare. Die KEGG-Referenzen sind Pathway-weite Literatur, nicht kantenweise zugewiesene Primärbelege. Die verlinkten DOI-/PubMed-Landingpages wurden nicht zusätzlich abgerufen; CPDB-Metadaten und Abstracts stammen aus dem gespeicherten NCBI-XML.

## ConsensusPathDB: konkrete Treffer und Kopplungsannotation

Die ursprüngliche Grenze von 14 Requests ließ die CPDB-Trefferprüfung offen. Der genehmigte Nachtrag schließt diese Lücke: Das beobachtete GET-Suchformular funktioniert ohne Cookies oder Browserstate. Die HTTPS-Verbindungsfehler (curl 7, keine HTTP-Antwort) bleiben dokumentiert; über HTTP funktionieren Suche und ausgewählte Interaktionsdetails. Eine generelle Sperre oder Formularfehlfunktion liegt in diesen Abrufen nicht vor. HTTP bietet keine TLS-gesicherte Herkunftsprüfung.

### Pathways und Ursprungs-IDs

Die [Suche nach circadian](http://cpdb.molgen.mpg.de/CPDB/search?nameacc=name&keywords=circadian&searchspace=Pathway) liefert 7 Zeilen, die [Suche nach p53](http://cpdb.molgen.mpg.de/CPDB/search?nameacc=name&keywords=p53&searchspace=Pathway) 35 (Requests 15/16). Das sind Suchtreffer, keine vollständige fachliche Abgrenzung aller Uhr- oder p53-Prozesse. Eine Auswahl:

| CPDB-Objekt-ID | Name | Ursprungsquelle / Original-ID |
|---|---|---|
| 186064 | Circadian rhythm - Homo sapiens (human) | KEGG / hsa04710 |
| 186056 | p53 signaling pathway - Homo sapiens (human) | KEGG / hsa04115 |
| 147321 | Circadian Clock | Reactome / R-HSA-400253 |
| 122348 | BMAL1:CLOCK,NPAS2 activates circadian gene expression | Reactome / R-HSA-1368108 |
| 283605 | Circadian rhythm pathway | PID / circadianpathway |
| 4415597 | Circadian rhythm related genes | WikiPathways / WP3594 |
| 100377 | Stabilization of p53 | Reactome / R-HSA-69541 |
| 14265 | Regulation of TP53 Degradation | Reactome / R-HSA-6804757 |
| 4415424 | TP53 network | WikiPathways / WP1742 |
| 283803 | p53 pathway | PID / p53regulationpathway |

Diese CPDB-IDs sind die beobachteten Formularwerte `objs:list`; eine dauerhafte Stabilität wird nicht vorausgesetzt. Original-IDs und Quellen stammen aus den externen Links der Trefferzeilen. Alle Treffer samt Original-URLs stehen in [cpdb_evidence.json](cpdb_evidence.json), reproduzierbar aus Raw 15/16. Die verlinkten Ursprungsseiten wurden im Nachtrag nicht separat abgerufen.

Die Detailaufrufe für [186064](http://cpdb.molgen.mpg.de/CPDB/getInteractionsOfObjs?objtype=p&objs%3Alist=186064&checknames=%5B%5D&exp=0) und [186056](http://cpdb.molgen.mpg.de/CPDB/getInteractionsOfObjs?objtype=p&objs%3Alist=186056&checknames=%5B%5D&exp=0) liefern HTTP 200, den jeweils richtigen Pathwaynamen und den KEGG-Link, aber den Text "The selected objects have no interactions in ConsensusPathDB." (Raw 18/19). Das ist das Ergebnis dieser beiden Anfragen, kein Beleg für fehlende biologische Interaktionen oder fehlende Verknüpfungen in CPDB insgesamt. Der entsprechende Aufruf für [Reactome Circadian Clock, CPDB 147321](http://cpdb.molgen.mpg.de/CPDB/getInteractionsOfObjs?objtype=p&objs%3Alist=147321&checknames=%5B%5D&exp=0) funktioniert und liefert 32 Interaktionszeilen, laut Seite 32 verschiedene (Raw 21). Damit ist kein allgemeiner Browserstate-Block nachgewiesen.

### Tatsächliche Zielgenpräsenz

Die [PER2-Suche](http://cpdb.molgen.mpg.de/CPDB/search?nameacc=name&keywords=PER2&searchspace=PhysicalEntity) liefert 9 Zeilen; darunter auch bloße Teilstringtreffer wie CATSPER2, die nicht als PER2 gewertet werden. Request 22 sucht TP53, MDM2, ARNTL, BMAL1 und CLOCK mit Zeilenumbruch als OR; die vollständige URL steht im Protokoll. Aus exakten Namen/Aliasen und Typangaben sind folgende Proteinobjekte bestätigt:

| Ziel | CPDB-Proteinobjekt | Beispiel einer abgerufenen Quellenzuordnung |
|---|---|---|
| PER2 | 147176 | BioGRID / 114387; IntAct / EBI-1054296 |
| TP53 | 8712 | BioGRID / 113010 |
| MDM2 | 14013 | BioGRID / 110358 |
| ARNTL/BMAL1 | 10181, beide Namen im selben Objekt | BioGRID / 106899 |
| CLOCK | 10197 | BioGRID / 114944 |

PER2 erscheint außerdem als separates Genobjekt 452150. CPDB fasst in Proteinobjekten unterschiedliche Namen und Zustände zusammen, teilweise mit Bezeichnungen wie "gene" oder "RNA". Das ist keine Prüfung konkreter Isoformen oder Modifikationszustände. Bestätigt ist die Präsenz in CPDB, nicht automatisch die Mitgliedschaft aller fünf Ziele in jedem genannten Pathway.

### Direkte Kopplungsannotation: PER2–TP53 und PER2–MDM2

Der [Interaktionsaufruf für PER2-Objekt 147176](http://cpdb.molgen.mpg.de/CPDB/getInteractionsOfObjs?objtype=e&objs%3Alist=147176&checknames=%5B%5D&exp=0) liefert 120 Zeilen, laut CPDB 38 verschiedene Interaktionen (Raw 20). Darin stehen ausdrücklich:

| Wörtliche CPDB-Annotation | CPDB-Interaktions-IDs | Quelle und verlinkte Ursprungsobjekte |
|---|---|---|
| Physical interaction of PER2 gene; TP53 | 2649126, 2649135, 2649141, 3025362, 2649138, 3025365 | BioGRID, [PER2 114387](http://www.thebiogrid.org/SearchResults/summary/114387) und [TP53 113010](http://www.thebiogrid.org/SearchResults/summary/113010) |
| Physical interaction of MDM2 Gene; PER2 gene | 3523918, 2649147, 3523915, 3523921, 4069781 | BioGRID, [MDM2 110358](http://www.thebiogrid.org/SearchResults/summary/110358) und PER2 114387 |

Diese abgerufenen Annotationen belegen, dass CPDB konkrete physische Verbindungen zwischen Uhrkomponente PER2 und den Checkpoint-Komponenten TP53/MDM2 führt. Es handelt sich um paarbezogene Interaktionsannotation, nicht bloß gemeinsame Gene eines Pathways. Die Tabellenzeilen weisen aber keine Wirkrichtung, Ubiquitinierung, Stabilisierung oder Kernimport als Mechanismus dieser Paare nach. "Physical interaction" allein garantiert auch keinen direkten binären Bindungsnachweis durch eine bestimmte experimentelle Methode.

Die BioGRID-Nummern sind verlinkte Objekt-/Summary-IDs, keine nachgewiesenen BioGRID-Interaktions-IDs. Mehrere CPDB-Zeilen und die ausgeklappt gespeicherten "similar interactions" dürfen nicht als ebenso viele unabhängige Replikationen gezählt werden. Den beiden Paaren sind in dieser Antwort keine DOI oder PMID explizit zugeordnet; die CPDB-Datenbankpublikationen oben ersetzen keine kantenbezogenen Primärbelege. BioGRID-Detailabrufe waren im ausgeschöpften Zusatzbudget nicht mehr enthalten.

Für die QMD lautet der belastbare Befund daher: KEGG beschreibt die beiden Prozesse in den geprüften Karten getrennt; CPDB integriert beide Pathwaytypen und enthält zusätzlich BioGRID-basierte physische PER2–TP53- und PER2–MDM2-Interaktionsannotation. Mechanistische Aussagen und experimentelle Replikation müssen anhand der jeweiligen Primärquellen geprüft werden. Die Aufnahme derselben Quelle in mehrere Datenbanken ist keine unabhängige Bestätigung.

## Abgrenzung zu quantitativen Modellen

KEGG-Karten und die hier dokumentierte CPDB-Funktion dienen der qualitativen Beschreibung von Mitgliedschaften und Interaktionen. Die abgerufenen Daten liefern kein vollständig parametrisiertes ODE-/DDE-Modell der Uhr–Checkpoint-Kopplung: Geschwindigkeitsgesetze, Parameter und Anfangsbedingungen wurden nicht gewonnen. Daraus lassen sich weder Perioden noch PER2/p53-Phasenlagen simulieren. SBML ist dagegen ein Modellformat; ob ein konkretes SBML-Modell quantitativ simulierbar ist, muss anhand seines Inhalts geprüft werden. Ein Pathway-Export oder selbst ein SBML-Label garantiert das nicht. BioModels-Dateien wurden in dieser Teilrecherche nicht neu geprüft.

## Abrufprotokoll und Offline-Verifikation

Genau 22 öffentliche GET-Abrufversuche: ursprüngliche 14 plus genehmigte 8. Insgesamt 20 Antworten mit HTTP 200 und 2 Verbindungsfehler ohne HTTP-Status; Zusatzrequests 15–22 sämtlich HTTP 200, curl-Exitcode 0. Das Amendment enthält UTC, beide Budgetgrenzen und den SHA-256 des ursprünglichen 14-Zeilen-Logs. Keine automatischen Redirects oder Wiederholungen; auch fehlgeschlagene Versuche zählen zum Budget. Keine weiteren Remote-Aufrufe durch Parsing oder Verifikation.

[requests.jsonl](requests.jsonl) enthält pro Versuch UTC-Start/-Ende, vollständige URL, HTTP-Status, curl-Exitcode, Kommando und SHA-256 des Bodys. `request_NN.body`, `.headers` und `.stderr` enthalten die Rohartefakte; bei Verbindungsfehlern sind Body und Header leer. [verification.txt](verification.txt) enthält das lesbare vollständige Request-Protokoll und die fachlichen Prüfungen.

| Requests | Inhalt | Ergebnis |
|---|---|---|
| 01–04 | KEGG hsa04710/hsa04115, Text und KGML | HTTP 200 |
| 05–06 | CPDB HTTPS, /CPDB und / | keine HTTP-Antwort, curl 7 |
| 07 | KEGG-Geneinträge aller fünf Zielgene | HTTP 200 |
| 08 | CPDB HTTP-Startseite | HTTP 200 |
| 09 | offizielle KGML-Dokumentation | HTTP 200 |
| 10 | NCBI PubMed: ConsensusPathDB im Titel | HTTP 200, 6 Treffer-IDs |
| 11–12 | CPDB Navigation und menschliche Inhaltsseite | HTTP 200 |
| 13 | NCBI PubMed XML für 34850110 und 23143270 | HTTP 200 |
| 14 | CPDB-Suchformular, noch keine Suchresultate | HTTP 200 |
| 15–16 | CPDB Pathway-Suche: circadian / p53 | HTTP 200; 7 / 35 Trefferzeilen |
| 17 | CPDB PhysicalEntity-Suche: PER2 | HTTP 200; 9 Trefferzeilen |
| 18–19 | Interaktionsdetails der KEGG-Pathways 186064 / 186056 | HTTP 200; erkannte Objekte, Antwort ohne Interaktionen |
| 20 | Interaktionsdetails PER2 147176 | HTTP 200; 120 Zeilen, laut CPDB 38 verschiedene |
| 21 | Interaktionsdetails Reactome-Uhr 147321 | HTTP 200; 32 Zeilen |
| 22 | PhysicalEntity-Suche: TP53 / MDM2 / ARNTL / BMAL1 / CLOCK (OR) | HTTP 200; 273 Trefferzeilen einschließlich Teilstring- und Komplextreffern |

Offline-Prüfung ab Projektwurzel: `python3 -B text_mining/pilot_task1f/pathways/verify.py`. Ergebnis: PASS, Exitcode 0. Zusätzlich zu den KEGG-Prüfungen werden das unveränderte ursprüngliche Request-Log, Amendment-Zeitpunkt vor Request 15, Budget 14 + 8, CPDB-Suchparameter, Trefferzahlen, Zielobjekte, Quellen-IDs und sämtliche oben genannten paarbezogenen Interaktions-IDs geprüft. `cpdb_evidence.py` extrahiert die gespeicherten HTML-Tabellen offline; die Verifikation vergleicht die Extraktion mit `cpdb_evidence.json`. Keine Prüfung des biologischen Wahrheitsgehalts der referenzierten Volltexte und keine QMD-Kompilierung.
