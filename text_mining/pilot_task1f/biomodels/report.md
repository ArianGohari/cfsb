# Aufgabe 1f: BioModels, circadiane Uhr und p53/MDM2/PER2

Stand: 20.09.2026 (UTC). Untersucht wurden die beiden tatsächlich vorhandenen Dateien unter `part1/task1/sbml/*.xml`, einschließlich XML-Metadaten, Species, Reaktionspartnern, Modifikatoren, kinetischen Gesetzen, Regeln und Events. Keine Simulation und kein vollständiger Modellvergleich.

## Ergebnis

Die lokalen SBML-Dateien beschreiben **zwei separate Subnetze**: ein circadianes PER2/CRY/BMAL1-Modell und ein p53/MDM2-DNA-Schadensmodell. In keiner der beiden Dateien ist die Kopplung PER2–p53–MDM2 implementiert. Insbesondere enthält die Uhrdatei weder p53 noch MDM2, die Checkpointdatei weder PER2 noch CRY/BMAL1. Das folgt aus den geparsten Modellbestandteilen, nicht aus den Dateinamen.

Beide konkreten BioModels-Einträge wurden über die öffentliche JSON-Schnittstelle bestätigt. Ob BioModels darüber hinaus ein passendes gekoppeltes Modell enthält, bleibt offen. Es wurde keine datenbankweite Suche durchgeführt; das Requestbudget ist ausgeschöpft. Aus diesem begrenzten Befund folgt keine Aussage, dass ein solches Modell nicht existiert.

## 1. Identität, Publikationen und Herkunft

| Merkmal | Uhrmodell | Checkpointmodell |
|---|---|---|
| Stabile BioModels-ID | [BIOMD0000000170](https://www.biomodels.org/BIOMD0000000170?format=json) | [BIOMD0000001006](https://www.biomodels.org/BIOMD0000001006?format=json) |
| Submission-ID | [MODEL8378813456](https://identifiers.org/biomodels.db/MODEL8378813456) | [MODEL2104140001](https://identifiers.org/biomodels.db/MODEL2104140001) |
| XML-Modell-ID | `Weimann2004_CircadianOscillator` | `Ciliberto2005___Steady_states_and_oscillations_in_the_p53_Mdm2_network` |
| Publikation | Becker-Weimann, Wolf, Herzel, Kramer (2004): *Modeling feedback loops of the Mammalian circadian oscillator.* Biophysical Journal 87(5), 3023–3034. [PMID 15347590](https://pubmed.ncbi.nlm.nih.gov/15347590/) | Ciliberto, Novak, Tyson (2005): *Steady states and oscillations in the p53/Mdm2 network.* Cell Cycle 4(3), 488–493. [PMID 15725723](https://pubmed.ncbi.nlm.nih.gov/15725723/) |
| Organismus-Annotation im lokalen XML | [Taxonomy 40674](https://identifiers.org/taxonomy/40674), Mammalia; keine Festlegung auf eine einzelne Säugerart | [Taxonomy 9606](https://identifiers.org/taxonomy/9606), Homo sapiens |
| Weitere Modellannotation | GO:0007623, KEGG hsa04710, MAMO:0000046 | GO:0042769, PW:0000718, BTO:0000414, MAMO:0000046 |
| SBML | Level 2 Version 1 | Level 2 Version 4 |
| API-Kurationsstatus | `CURATED` | `CURATED` |
| Lokaler Umfang | 7 Species, 17 Reaktionen, 3 Assignment Rules, 0 Events, 0 Initial Assignments | 10 Species, 21 Reaktionen, 4 Assignment Rules, 2 Events, 1 Initial Assignment |

Die IDs und PubMed-Verweise stehen im Uhr-XML in Zeilen 32–60 und im Ciliberto-XML in Zeilen 37–64. Die Publikationstitel und Autoren wurden zusätzlich aus den API-Antworten gelesen: [Request 09, Zeilen 9–40](request_09.body), [Request 10, Zeilen 9–37](request_10.body). Die Quellenlinks auf PubMed/identifiers.org wurden in dieser Recherche nicht zusätzlich abgerufen.

### Dateiversionen: wichtige Einschränkung

| Datei | SHA-256 lokal | SHA-256 laut aktueller API, `files.main[0].sha256sum` |
|---|---|---|
| `BIOMD0000000170_url.xml` | `f6f1bd3faf8223d8a32314e7422263568e88b1f662b9d2ee9f7e0300960d6328` | `ec4a5b68041d448cf34b82af4fc26a3b2e5c68b57b04b29a2cd28ad557bd7898` |
| `Ciliberto2005.xml` | `c412f691fb6dad00ebb96148ebdc52148b1f47949ad1dd139a0ea99c6ec6b389` | `c412f691fb6dad00ebb96148ebdc52148b1f47949ad1dd139a0ea99c6ec6b389` |

Die Ciliberto-Prüfsummen stimmen überein. Bei der Uhrdatei stimmen Identität und Publikationszuordnung überein, die Dateiprüfsumme aber nicht. Ursache und inhaltlicher Umfang der Abweichung sind ungeklärt. Die API führt spätere Revisionen auf; daraus lässt sich die konkrete Differenz nicht bestimmen. Es wurde kein aktuelles Remote-SBML heruntergeladen. Die folgenden Strukturangaben beziehen sich deshalb ausdrücklich auf die lokalen XML-Dateien.

## 2. Was das Uhrmodell tatsächlich enthält

Quelle: [lokales Uhr-SBML](../../../part1/task1/sbml/BIOMD0000000170_url.xml), Species Zeilen 113–236, Regeln 266–344, Reaktionen 345–848. Das vollständige maschinenlesbare Inventar steht in [local_inventory.json](local_inventory.json).

| Species-ID | XML-Name | Kompartiment |
|---|---|---|
| `y1` | Per2 or Cry mRNA | Cytoplasm |
| `y2` | PER2_CRY_complex_cytoplasm | Cytoplasm |
| `y3` | PER2_CRY_complex_nucleus | Nucleus |
| `y4` | Bmal1 mRNA | Cytoplasm |
| `y5` | BMAL1_cytoplasm | Cytoplasm |
| `y6` | BMAL1_nucleus | Nucleus |
| `y7` | Active BMAL1 | Nucleus |

PER2 wird hier zusammen mit CRY beschrieben: `y1` ist eine zusammengefasste mRNA-Variable, `y2` und `y3` sind PER2/CRY-Komplexe. Es gibt keine separate freie PER2-Protein-Species und keinen PER2:p53-Komplex. Die PER2/CRY-Species tragen die UniProt-Verweise O15055 und Q16526; BMAL1 ist mit Q8IUT4 annotiert.

Ausgewählte tatsächlich vorhandene Reaktionen, mit Richtung aus den Species References und Abhängigkeiten aus der MathML-Kinetik:

| Reaktions-ID | Inhalt | XML-Zeilen |
|---|---|---|
| `per2_cry_transcription` | Quelle → `y1`; Rate `Cytoplasm * trans_per2_cry` | 346–372 |
| `per2_cry_complex_formation` | Quelle → `y2`; `y1` ist Modifier, Rate `Cytoplasm * k2b * y1^q` | 401–435 |
| `per2_cry_nuclear_import` | `y2` → `y3`, abhängig von `k2t * y2` | 464–494 |
| `per2_cry_nuclear_export` | `y3` → `y2`, abhängig von `k3t * y3` | 495–525 |
| `cytoplasmic_per2_cry_complex_degradation` / `nuclear_per2_cry_complex_degradation` | Abbau von `y2` bzw. `y3`; kein MDM2-Term | 436–463 / 526–553 |
| `Bmal1_transcription` / `BMAL1_translation` | Quelle → `y4` bzw. Quelle → `y5`; Translation durch `y4` modifiziert | 554–580 / 609–639 |
| `BMAL1_activation` / `BMAL1_deactivation` | `y6` → `y7` bzw. `y7` → `y6` | 758–819 |

Die als Komplexbildung benannte Reaktion ist eine effektive Produktion, keine explizite Bindungsreaktion zweier separat modellierter Proteine. Weitere Reaktionen beschreiben mRNA-Abbau, BMAL1-Transport und BMAL1-Abbau; alle 17 sind im Inventar erfasst.

Die Uhr-Rückkopplung steckt auch in Regeln, nicht nur in Reaktions-Modifierlisten: `trans_per2_cry` hängt von aktivem BMAL1 (`y7`) und nukleärem PER2/CRY (`y3`) ab; `y3` erscheint im inhibitorischen Nenner. `trans_Bmal1` ist eine sättigende Funktion von `y3`. `y5_y6_y7` summiert die BMAL1-Formen. Das ist eine interne Uhr-Rückkopplung, keine Verbindung zum p53-Checkpoint.

## 3. Was das p53/MDM2-Modell tatsächlich enthält

Quelle: [lokales Ciliberto-SBML](../../../part1/task1/sbml/Ciliberto2005.xml), Species Zeilen 595–870, Initial Assignment 1268–1274, Regeln 1275–1337, Reaktionen ab 1339, Events 2210–2276.

| Species-ID | Kompartiment | Bedeutung im Modell |
|---|---|---|
| `DNA_damage` | Nuc | Schadensvariable |
| `IR` | Nuc | Bestrahlungseingang, per Assignment Rule gesetzt |
| `p53_total` | Nuc | Gesamt-p53 |
| `p53_ub` | Nuc | erste ubiquitinierte p53-Form |
| `p53_ub_ub` | Nuc | weiter ubiquitinierte p53-Form |
| `Mdm2_cyt` | Cyt | cytoplasmatisches Mdm2 |
| `Mdm2_p_cyt` | Cyt | phosphoryliertes Mdm2 im Cytoplasma |
| `Mdm2_p_nuc` | Nuc | phosphoryliertes Mdm2 im Kern |
| `p53` | Nuc | abgeleitet: `p53_total - p53_ub - p53_ub_ub` |
| `MDM2_total` | Cyt | abgeleitete Summe mit Volumenfaktor für nukleäres Mdm2 |

`IR`, `p53` und `MDM2_total` sind Boundary-Species mit Assignment Rules. Zehn Species bedeuten hier also nicht zehn unabhängige Reaktions-ODEs. Alle p53-Species sind im Kern lokalisiert; ein cytoplasmatischer p53-Pool oder PER2-vermittelter p53-Kernimport ist nicht enthalten.

| Reaktions-ID | Tatsächliche Modellierung | XML-Zeilen |
|---|---|---|
| `DNA_Damage` | Quelle → `DNA_damage`, mit `IR` als Modifier | 1339–1382 |
| `DNA_Repair` | `DNA_damage` → Senke, mit `p53_total` als Modifier | 1383–1428 |
| `p53_ubiquitination_1` | Quelle → `p53_ub`, mit `p53` und `Mdm2_p_nuc` als Modifikatoren | 1507–1552 |
| `p53_ubiquitination_2` | `p53_ub` → `p53_ub_ub`, mit `Mdm2_p_nuc` als Modifier | 1553–1600 |
| `p53_ub_ub_degradation` | Abbau von `p53_ub_ub`; Kinetik enthält `kd53 + kd53_0` | 1639–1680 |
| `p53_total_degradation_2` | zusätzlicher Verlust von Gesamt-p53, Rate abhängig von `p53_ub_ub` | 2083–2126 |
| `Mdm2_cyt_production` | Quelle → `Mdm2_cyt`, Synthesefunktion mit `p53_total` | 1760–1802 |
| `Mdm2_cyt_phosphorylation` | `Mdm2_cyt` → `Mdm2_p_cyt`, Kinetik abhängig von `p53_total` | 1803–1847 |
| `Mdm2_p_nuc_degradation` | Abbau von nukleärem Mdm2, Rate mit `kd2_0` | 2045–2082 |

Die erste Ubiquitinierung darf nicht als wörtliches `p53 → p53_ub` aus dem Reaktionsgraphen abgeschrieben werden: freies p53 wird algebraisch aus Gesamt-p53 und den ubiquitinierten Formen berechnet. Ebenso ist Mdm2-Transport in getrennte `*_translocation_out`- und `*_translocation_in`-Reaktionen zerlegt, teils mit Volumenfaktoren. Das Inventar bewahrt die tatsächlichen Partner und kinetischen Gesetze.

Die Regel `kd2_0 = kd2 + kd2_ * DNA_damage / (Jdam + DNA_damage)` verbindet DNA-Schaden mit Mdm2-Abbau. `IR = ampl * step`; zwei Events setzen `step` auf 1 bzw. 0 (Trigger `time > 10` mit Verzögerung 2 und `time > 20`). Das sind Bestrahlungsereignisse, kein circadianer Antrieb. Die Initialzuweisung `ModelValue_6 = vratio` betrifft den Volumenfaktor; auch dort gibt es keinen Uhrterm.

## 4. Verbindung zwischen Uhr und Checkpoint: Literatur versus SBML

Die biologische Verbindung ist in der vorhandenen Literatur beschrieben. Maßgebliche lokale Belegquelle ist [Zou et al. (2020), DOI 10.3389/fphys.2020.00327](https://doi.org/10.3389/fphys.2020.00327), [PMID 32372973](https://pubmed.ncbi.nlm.nih.gov/32372973/), [PMC7176909](https://pmc.ncbi.nlm.nih.gov/articles/PMC7176909/). Gelesen wurde die vorhandene [Markdown-Fassung](../../../part1/task1/sources/markdown/zou_2020_circadian_cell_cycle_checkpoints/zou_2020_circadian_cell_cycle_checkpoints.md); keine neuen Literatur-Requests. Diese Quelle ist ein Review, kein Nachweis für einen bestimmten BioModels-Eintrag.

- PER2 bindet p53 und schützt es vor MDM2-vermittelter Ubiquitinierung. Dazu passt [Gotoh et al. (2014), DOI 10.1091/mbc.E14-05-0993](https://doi.org/10.1091/mbc.E14-05-0993), PMID 25103245. Beleg im Review: Zeilen 37 und 90–100.
- Der Review beschreibt PER2-vermittelten p53-Kerntransport, unterschiedliche p53-Stabilität in Kern und Cytoplasma sowie Bindung an ubiquitiniertes p53. Das verfeinerte Modell umfasst laut Review 13 Differentialgleichungen und 18 Parameter und enthält eine PER-Rückkopplung sowie PER2–p53-Interaktion (Zeilen 90–100). Zugehörige Primärarbeit: [Gotoh et al. (2016), DOI 10.1073/pnas.1607984113](https://doi.org/10.1073/pnas.1607984113), *Model-driven experimental approach reveals the complex regulatory distribution of p53 by the circadian factor Period 2*; Literaturangabe in Zeile 154. Dafür wurde hier keine BioModels-ID verifiziert.
- Umgekehrt kann MDM2 PER2 ubiquitinieren und dessen Abbau fördern: [Liu et al. (2018), DOI 10.1126/scisignal.aau0715](https://doi.org/10.1126/scisignal.aau0715), PMID 30425162. Beleg im Review: Abschnitt ab Zeile 102, insbesondere Zeile 110. Das begründet eine biologische Rückwirkung auf die Uhr, beweist aber nicht, dass jedes PER2/p53-Modell diese Reaktion implementiert.

Die im Review für das vereinfachte p53-Modell verwendeten PER-Verläufe stammen aus dem Kim–Forger-Uhrmodell (Zeilen 71–86). Das unterscheidet sich von der hier lokal vorliegenden Becker-Weimann-Datei. Ein vorgeschriebener Uhrverlauf als Eingang ist zunächst eine gerichtete Kopplung; eine bidirektionale Modellkopplung erfordert zusätzlich eine explizite Rückwirkung auf Uhrvariablen.

Für die beiden geprüften SBML-Dateien fehlen sowohl PER2:p53-Bindung als auch PER2-abhängige p53-Transport-/Abbauraten und MDM2-abhängiger PER2-Abbau. Ihre gemeinsame Ablage erzeugt keine mathematische Kopplung. Sie eignen sich als getrennte Ausgangsmodelle; eine Verbindung müsste fachlich spezifiziert und separat implementiert werden. Eine automatische Zusammenführung oder Gleichsetzung der aggregierten PER2/CRY-Variablen mit freiem PER2 wäre nicht begründet.

## 5. Öffentliche Requests und Raw-Belege

Genau **10 HTTP-GET-Requests**, einschließlich jedes Redirect-Schritts. Keine automatischen Redirects, Retries, Schlüssel, Anmeldung, Cookies oder Blockumgehung. `curl -q` deaktivierte eine etwaige lokale curl-Konfigurationsdatei. Eingebettete Webseitenressourcen wurden nicht geladen. Vollständige UTC-Start-/Endzeiten, exakte Befehle, HTTP-Status, curl-Metadaten und Body-Prüfsummen stehen in [requests.jsonl](requests.jsonl).

Alle folgenden UTC-Zeiten sind am 20.09.2026; auf Sekunden gekürzt, ungekürzt im Log:

| Nr. | UTC-Start | GET-URL | HTTP / Inhalt | Raw |
|---|---|---|---|---|
| 01 | 15:54:28 | https://www.ebi.ac.uk/biomodels/ | 301 → https://biomodels.org/ | [Header](request_01.headers), [Body, 0 Bytes](request_01.body) |
| 02 | 15:54:29 | https://www.ebi.ac.uk/biomodels/BIOMD0000000170 | 301 → biomodels.org, gleicher Modellpfad | [Header](request_02.headers), [Body, 0 Bytes](request_02.body) |
| 03 | 15:54:29 | https://www.ebi.ac.uk/biomodels/BIOMD0000001006 | 301 → biomodels.org, gleicher Modellpfad | [Header](request_03.headers), [Body, 0 Bytes](request_03.body) |
| 04 | 15:54:56 | https://biomodels.org/ | 301 → https://www.biomodels.org/ | [Header](request_04.headers), [Body](request_04.body) |
| 05 | 15:54:57 | https://biomodels.org/BIOMD0000000170 | 301 → www.biomodels.org, gleicher Modellpfad | [Header](request_05.headers), [Body](request_05.body) |
| 06 | 15:54:57 | https://biomodels.org/BIOMD0000001006 | 301 → www.biomodels.org, gleicher Modellpfad | [Header](request_06.headers), [Body](request_06.body) |
| 07 | 15:55:35 | https://www.biomodels.org/BIOMD0000000170 | 200, HTML-Fehlerseite `Unsupported Media Type` | [Header](request_07.headers), [Body](request_07.body) |
| 08 | 15:55:35 | https://www.biomodels.org/BIOMD0000001006 | 200, HTML-Fehlerseite `Unsupported Media Type` | [Header](request_08.headers), [Body](request_08.body) |
| 09 | 15:56:22 | https://www.biomodels.org/BIOMD0000000170?format=json | 200, gültiges Modell-JSON | [Header](request_09.headers), [Body](request_09.body) |
| 10 | 15:56:23 | https://www.biomodels.org/BIOMD0000001006?format=json | 200, gültiges Modell-JSON | [Header](request_10.headers), [Body](request_10.body) |

Die API-Requests 09/10 verwendeten `Accept: application/json`. Die normale HTML-Darstellung wurde unter den verwendeten Requestbedingungen nicht erfolgreich verifiziert: Der Seitentitel in Zeile 108 der Antworten 07/08 meldet einen Medienformatfehler trotz HTTP 200. Die JSON-Antworten enthalten dagegen passende `publicationId`, `submissionId`, Publikation und Dateimetadaten. Alle curl-Prozesse endeten mit Exitcode 0; dieser Transporterfolg darf nicht mit einer inhaltlich brauchbaren HTML-Antwort verwechselt werden.

## 6. Prüfungen und Grenzen

Reproduzierbare Offline-Prüfung ab Workspace-Wurzel:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 text_mining/pilot_task1f/biomodels/verify.py
```

Ergebnis: PASS, Exitcode 0; Ausgabe in [verification.txt](verification.txt). Geprüft werden die unveränderten lokalen XML-Prüfsummen gegenüber dem Inventar, Strukturzahlen und Species-Mengen, gültige Reaktionsreferenzen, ausgewählte Kinetik-/Regelverbindungen, Initialzuweisung, API-Identitäten, Publikationen, alle Raw-Body-Prüfsummen und genau zehn Requests ohne automatische Redirects. [inspect_sbml.py](inspect_sbml.py) extrahiert die lokalen Dateien mit der Python-Standardbibliothek; die Prüfung selbst sendet keine Requests und schreibt keine Dateien.

Beim ersten Prüflauf schlug eine zu starke Annahme fehl: Ciliberto enthält eine Initialzuweisung. Sie wurde anschließend gelesen, im Inventar ergänzt und gezielt geprüft (`ModelValue_6 = vratio`). Der abschließende Lauf besteht. Kein SBML-Schema-/libSBML-Validierungstest, keine numerische Prüfung und keine Simulation wurden durchgeführt.

Geschrieben wurde ausschließlich in diesem neu angelegten Verzeichnis. Die vorhandenen SBML-Dateien wurden nur gelesen; ihre Prüfsummen blieben unverändert. Ein Git-Diff war nicht möglich, da dieses Arbeitsverzeichnis kein Git-Repository ist. Die API-Dateiprüfsumme des Uhrmodells weicht ab; die aktuelle Remote-Modellstruktur und mögliche weitere gekoppelte BioModels-Einträge bleiben ungeprüft.
