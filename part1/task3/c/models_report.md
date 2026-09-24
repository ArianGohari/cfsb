# Task 3(c): Schlüsselproteine aus Task 1 in BioModels

Stand: 21.09.2026. Aufgabenbezug: `project.md`, Zeilen 38-61 und 87: Gibt es Modelle mit den Schlüsselproteinen, und was tragen sie zu den Hypothesen aus Task 1 bei?

Ja. Die geprüften SBML-Dateien enthalten PER2:CRY- und BMAL1-Zustände sowie, in einem getrennten Modell, p53 und MDM2. Für eine direkte PER2-p53- oder Clock-p53-Kopplung liefert diese begrenzte Suche keinen SBML-Nachweis. Die Modelle sind brauchbare Teilmodelle; aus ihrer getrennten Existenz folgt keine belegte Kopplung. Es wurde nichts simuliert.

## Vorgehen und Datenstand

`inspect_models.py` verwendet nur die Python-Standardbibliothek. Zuerst wurden 1.096 vorhandene BIOMD-Metadatendateien unter `../b/cache` anhand von Name, Beschreibung und Publikationsdaten durchsucht. Gesucht wurden PER2, PER1, CRY, BMAL, CLOCK, circadian, p53, TP53 und MDM2 ohne Beachtung der Großschreibung. Die 90 Kandidaten in `metadata_candidates.tsv` sind Texttreffer, keine bestätigten Proteinmodelle. Insbesondere das kurze Teilwort `cry` kann unpassende Treffer erzeugen. Kein Kandidat erfüllt dort zugleich die im Skript definierte Clock- und p53/MDM2-Bedingung. Das ist ein Befund über diesen Cache und diese Suchfelder.

Ausgewählt wurden die beiden vorhandenen Task-1-Modelle sowie drei Clock-Modelle mit unterschiedlichen Abstraktionsgraden. BIOMD73 ergänzt explizite Clock-Bmal-Komplexbildung, BIOMD216 den Bezug zur DNA-Schadensantwort und BIOMD839 ein neueres PER:CRY-Modul. Drei zusätzliche SBML-Dateien wurden über öffentliche BioModels-GETs geladen. Eine erneute Korpuserhebung fand nicht statt.

Drei gezielte öffentliche Suchabfragen wurden zusätzlich ohne Kuratierungsfilter ausgeführt:

| API-Query | Gemeldete Treffer | Tatsächlich zurückgegeben |
|---|---:|---|
| `PER2` | 1 | BIOMD0000000170 |
| `(circadian OR CLOCK OR BMAL1 OR PER2) AND (p53 OR TP53 OR MDM2)` | 0 | keine |
| `"PER2" AND "p53"` | 0 | keine |

Die Query-Strings sind in `search_results.json`, vollständige URLs, UTC-Zeiten, HTTP-Status und SHA-256 in `cache/*.receipt.json` gespeichert; die unveränderten Antwortbytes liegen daneben. Alle sechs GETs lieferten HTTP 200. Die Suchantworten haben höchstens 100 angeforderte Ergebnisse und waren bei diesen Trefferzahlen vollständig. Die Suche hängt trotzdem von der BioModels-Indexierung, den abgefragten Begriffen und dem Zeitpunkt ab. Nicht indexierte Speziesnamen, andere Synonyme und externe Modelle können fehlen. Daraus folgt ausdrücklich keine Aussage, dass in ganz BioModels kein gekoppeltes Modell existiert.

## Geprüfte Modelle und konkrete Nachweise

IDs in dieser Tabelle sind SBML-IDs. Sämtliche 47 Spezies und 123 Reaktionen stehen in `species.tsv` und `reactions.tsv`, einschließlich Annotationen, Stöchiometrie, Modifikatoren und kinetischer MathML. Die Zahlen zählen auch algebraisch definierte Spezies, nicht nur unabhängige ODE-Zustände.

| Modell | Spezies / Reaktionen | Nachweis in der Datei | Beitrag und Grenze |
|---|---:|---|---|
| [BIOMD0000000170, Becker-Weimann et al. 2004](https://www.biomodels.org/BIOMD0000000170), PMID 15347590 | 7 / 17 | `y1`: "Per2 or Cry mRNA"; `y2`: `PER2_CRY_complex_cytoplasm`; `y3`: `PER2_CRY_complex_nucleus`; `y4`: Bmal1 mRNA; `y5`, `y6`, `y7`: zytoplasmatisches, nukleäres und aktives BMAL1. `per2_cry_complex_formation`: Quelle → `y2`, mit `y1` als Modifikator. `per2_cry_nuclear_import`: `y2` → `y3`. `BMAL1_activation`: `y6` → `y7`. | PER2 ist im Speziesnamen ausdrücklich vorhanden, aber gemeinsam mit CRY aggregiert. Es gibt kein freies PER2, keine getrennte CRY-Dynamik und keine eigene CLOCK-Spezies. Das Modell liefert einen reduzierten Clock-Baustein, keinen PER2-p53-Bindungsmechanismus. |
| [BIOMD0000001006, Ciliberto et al. 2005](https://www.biomodels.org/BIOMD0000001006), PMID 15725723 | 10 / 21 | `p53_total`, `p53`, `p53_ub`, `p53_ub_ub`; `Mdm2_cyt`, `Mdm2_p_cyt`, `Mdm2_p_nuc`, `MDM2_total`. p53-Zustände sind mit UniProt P04637, MDM2-Zustände mit Q00987 annotiert. `p53_ubiquitination_1` erzeugt `p53_ub`, kinetisch abhängig von `p53` und `Mdm2_p_nuc`. `p53_ubiquitination_2`: `p53_ub` → `p53_ub_ub`, mit `Mdm2_p_nuc` als Modifikator. `Mdm2_cyt_production` hängt von `p53_total` ab. | Geeignet zur Beschreibung des p53-MDM2-Feedbacks und der DNA-Schadensantwort. PER2, CRY und Clock-Zustände fehlen in dieser Datei. Auch ein expliziter p53:MDM2-Bindungskomplex fehlt; die Wirkung wird kinetisch erfasst. |
| [BIOMD0000000073, Leloup & Goldbeter 2003](https://www.biomodels.org/BIOMD0000000073), PMID 12775757 | 16 / 48 | `species_8` = `Pc`, `species_4` = `Cc`, `species_10` = `PCc`; `reaction_13`, "Cc and Pc produce complex Per_Cry": `species_4 + species_8` → `species_10`. `species_12` = `PCn`, `species_3` = `Bn`; `reaction_23`, "Per_Cry and Clock_Bmal form inactive complex": `species_12 + species_3` → `species_15` (`In`). | Expliziter Beleg für PER:CRY und den inaktiven Komplex mit dem Clock-Bmal-Zweig. PER wird aggregiert: `Pc` trägt mehrere UniProt-Referenzen, darunter O15055, O15534 und P56645. Das ist keine Auflösung separater PER1-/PER2-/PER3-Zustände. CLOCK ist kein separater dynamischer Reaktionspartner. |
| [BIOMD0000000216, Hong et al. 2009](https://www.biomodels.org/BIOMD0000000216), PMID 19424508 | 6 / 17 | `M`, `TF`, `CP`, `CP2`, `IC`, `CPtot`. `r6`: `2 CP` → `CP2`; `r7` umgekehrt; `r12`: `CP2 + TF` → `IC`; `r10`: `IC` → `CP2 + TF`. `r9` baut `CP` ab, `r14` baut `CP2` ab. | Der Abstract beschreibt Chk2-abhängigen Abbau freier PER-Proteine nach DNA-Schaden und erwähnt PER1 in Mus sowie FRQ in Neurospora. Die Datei modelliert abstrahierte Clock-Komponenten. Sie enthält keine p53-, MDM2-, Chk2- oder spezifisch benannte PER2-Spezies. `CP2` bedeutet hier Dimer (`2 CP`), nicht das Gen PER2. |
| [BIOMD0000000839, Almeida et al., Modellname 2019; Publikation 2020](https://www.biomodels.org/BIOMD0000000839), PMID 31539528 | 8 / 20 | `BMAL1`, `CRY`, `PER`, `PERCRY`, außerdem `ROR`, `REV`, `DBP`, `E4BP4`. `v9_3`: `PER + CRY` → `PERCRY`; `v9_4` umgekehrt. `v4_2` baut BMAL1 mit PERCRY als Modifikator ab; `v11_3` baut PERCRY mit BMAL1 als Modifikator ab. | Clock-Feedback mit expliziter PER:CRY-Bindung. `PER` ist generisch, keine separate PER2-Spezies. Die Beschreibung spricht von CLOCK:BMAL1; eine unabhängige CLOCK-Spezies ist nicht vorhanden. Kein p53-/MDM2-Zweig. |

Reaktionspfeile geben die gespeicherten Referenzen wieder. Das Feld `reversible` und die Kinetik müssen zusätzlich berücksichtigt werden; die Tabelle behauptet keine elementaren Massenwirkungsschritte. Insbesondere die Quelle → Komplex-Reaktion in BIOMD170 ist eine zusammengefasste Synthese, keine explizite Bindungsreaktion zweier freier Proteine.

### Regeln und Annotationen nicht übergehen

In BIOMD170 laufen regulatorische Einflüsse über Assignment Rules: `trans_per2_cry` hängt von `y7` und `y3` ab, `trans_Bmal1` von `y3`. Leere Modifikatorfelder in den zugehörigen Transkriptionsreaktionen bedeuten daher nicht fehlende Regulation. `reactions.tsv` zeigt direkte kinetische Symbole; indirekte Abhängigkeiten über Regeln sind separat in `models.json` als `rule_mathml` erhalten und werden nicht automatisch transitiv aufgelöst.

In BIOMD1006 ist `p53 = p53_total - p53_ub - p53_ub_ub` eine Assignment Rule. Auch `MDM2_total` und `IR` sind regeldefiniert. Diese Größen dürfen beim späteren Aufbau eines gekoppelten Modells nicht einfach als zusätzliche unabhängige Konzentrationen integriert werden. BIOMD216 hat entsprechend `CPtot = CP + 2 CP2 + 2 IC`.

Die Annotationen werden als Original-URIs ausgegeben, nicht als fehlerfreie Proteinidentifizierung behandelt. Beispielsweise trägt BIOMD216 für `CP`/`CP2` O15516 und für `TF` O00327/P49759, während die Publikationsbeschreibung mit abstrahierten Clock-Komponenten arbeitet. Eine unabhängige UniProt-Prüfung dieser Zuordnungen wurde hier nicht vorgenommen. Die Interpretation als spezifisches PER2 wäre durch Namen, Reaktionsstruktur und Annotation allein nicht gerechtfertigt. Auch in BIOMD170 ersetzt der explizite PER2-Name keine getrennte Modellierung sämtlicher PER2-Funktionen.

## Biologische Taxa

| Modelle | Explizite Modellannotation | Interpretation |
|---|---|---|
| BIOMD170, BIOMD73, BIOMD216 | `taxonomy/40674`, Mammalia | Säugetiermodelle. Kein Beleg für ausschließliche Gültigkeit in menschlichen Zellen. BIOMD170 diskutiert im Abstract Mausmutanten. Die Erwähnung von Neurospora im Abstract von BIOMD216 macht die SBML-Datei nicht zu einem Neurospora-Modell. |
| BIOMD1006 | `taxonomy/9606`, Homo sapiens | Menschlich annotiertes p53-MDM2-Modell. Die Annotation allein belegt keine Übertragbarkeit auf beliebige Tumoren oder Patientinnen und Patienten. |
| BIOMD839 | Kein `hasTaxon` in den API-Modellannotationen und keine Taxonomie-URI in der SBML-Modellannotation | Der Abstract beschreibt eine Säugetieruhr; eine engere biologische Art wird aus diesen Dateien nicht abgeleitet. |

Taxa beziehen sich auf Organismen, SBML-Spezies auf Modellvariablen. Ein humanes KEGG-Pathway-Kürzel oder eine einzelne Proteinreferenz ersetzt keine Modell-Taxonannotation. Ein gemeinsames Modell müsste außerdem Zelltyp, DNA-Schadensregime, Einheiten und Zeitskalen abgleichen.

## Was folgt für die Behauptungen aus Task 1?

BIOMD170 und BIOMD1006 liefern konkrete Ausgangsmodule für Clock- und p53-MDM2-Feedback. BIOMD73 und BIOMD839 helfen bei einer expliziteren Darstellung der Clock-Komplexbildung. BIOMD216 zeigt einen verwandten mechanistischen Ansatz zur Verbindung von DNA-Schaden und Clock-Phasenänderung, aber keinen Nachweis der in Task 1 gefragten p53-PER2-Kopplung.

Für die Arbeiten von Gotoh et al. 2014/2015 müsste ein Modell mindestens die PER2-p53-Assoziation und ihren Einfluss auf p53-Stabilität bzw. Transkriptionsaktivität unterscheiden. Für Liu et al. 2018 wäre zusätzlich die MDM2-abhängige PER2-Degradation zu prüfen. Solche Reaktionen sind in den fünf geprüften Dateien nicht belegt. Ein hypothetisches Verbinden der Modelle wäre eine neue Modellannahme und kein aus BioModels reproduziertes Ergebnis. Auch die zeitverzögerte Kopplung aus Task 1(e) wurde damit nicht reproduziert.

Diese statische Prüfung belegt vorhandene Modellbestandteile. Sie prüft weder Oszillationsperioden noch Phasenverschiebungen, Parameteridentifizierbarkeit oder klinische Chronotherapie-Behauptungen. Die Reproduktionsangaben in den BioModels-Beschreibungen stammen von den Autoren bzw. Kuratoren; hier wurden sie nicht durch eine Simulation bestätigt.

## Reproduktion und Prüfungen

Vom Projektverzeichnis aus:

```sh
python3 part1/task3/c/inspect_models.py --fetch
python3 part1/task3/c/inspect_models.py
python3 part1/task3/c/check_outputs.py
```

`--fetch` erlaubt nur fehlende Cache-GETs; vorhandene Antwortbytes werden anhand der Receipts geprüft und nicht überschrieben. Ohne Flag wird keine Netzwerkfunktion aufgerufen. Die Standardausführung rekonstruiert die Nachweistabellen aus vorhandenen Quellen. Die ursprünglichen Dateien unter `part1/task1/sbml` und `part1/task3/b/cache` bleiben Eingaben; `inputs.json` hält ihre Hashes fest. `check_outputs.py` prüft diese Hashes vor einer byteidentischen Offline-Neuerzeugung aller sechs Ergebnisdateien sowie ausgewählte konkrete Reaktionsnachweise.

Alle drei Befehle wurden mit Exit 0 ausgeführt. Die Offline-Prüfung meldet:

```text
PASS: 1101 input hashes; 90 metadata candidates; 3 cached searches; 5 SBML models; 47 species; 123 reactions; references valid. No simulation.
PASS: source hashes, receipts, deterministic offline regeneration, named species/reaction evidence, assignment rules and BIOMD170 newline-only difference.
```

Die lokale BIOMD170-Datei stimmt byteweise nicht mit dem API-SHA-256 überein. Nach Entfernen des abschließenden Zeilenumbruchs stimmt der Hash exakt; das wird im Test geprüft. Die vier übrigen SBML-Dateien stimmen direkt mit den API-Hashes überein. Es gibt hier also keinen belegten inhaltlichen Versionsunterschied. Die Prüfungen sind XML-/Referenz- und Evidenzprüfungen, keine vollständige libSBML-Konsistenzprüfung und kein dynamischer Modelltest.
