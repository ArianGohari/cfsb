# Vorrangiger Nachtrag: Gaddameedhi2012 im Originalvolltext

Stand: 20.09.2026, nach der API-Volltextprüfung. Dieser Nachtrag ersetzt die Gaddameedhi-Einordnung im Abstract-Pilot (report.md/records.csv) und in Abschnitt 1 sowie der Abschlusstabelle von fulltext_review.md. Dortige Angaben "nur Abstract", "Volltext offen" und die auf Maus-Zelllinien beschränkte Einordnung sind für diesen Artikel überholt. Die alten Texte und Rohantworten dokumentieren den damaligen Erkenntnisstand, nicht das heutige Urteil.

## Korrigierte Kernaussage für Aufgabe 1(d)

Gaddameedhi et al. (2012) berichten eine gezielte Nichtreproduktion spezifischer PER1-Befunde aus Gery et al. (2006), einschließlich Versuchen in denselben benannten humanen Krebszelllinien. In NCI-H460 fanden sie unter ihren Bedingungen nach PER1-Knockdown oder Überexpression keine Veränderung der IR-induzierten Checkpoint-/Apoptoseantwort (Fig. 8); in NCI-H460 und HCT-116 keine veränderte klonogene IR-Empfindlichkeit (Fig. 9). Das ist mehr als ein Gegenbefund in bloß anderem Organismuskontext. Eine protokollidentische Replikation oder endgültige Falsifikation aller Gery-Aussagen ist damit nicht nachgewiesen.

Zugleich enthält dieselbe Arbeit einen positiven, kontextabhängigen Befund: PER1/2-Knockdown vermindert UV-induzierte Apoptosemarker in primären Maus-Hautfibroblasten (Fig. 7). Die pauschale Lesart "Uhrmutationen bzw. PER-Verlust haben keine Wirkung auf DNA-Schadensantworten" wird durch die eigenen Resultate nicht gedeckt. Genetische Knockouts und akute Knockdowns, Maus- und Humanzellen sowie UV und IR müssen getrennt bleiben.

## Quelle, Abruf und Audittrail

Original: Gaddameedhi S, Reardon JT, Ye R, Ozturk N, Sancar A. Effect of circadian clock mutations on DNA damage response in mammalian cells. Cell Cycle 2012;11:3481–3491. [PMCID PMC3466558](https://pmc.ncbi.nlm.nih.gov/articles/PMC3466558/), PMID 22918252, [DOI 10.4161/cc.21771](https://doi.org/10.4161/cc.21771).

Der übergeordnete Assistent meldete seinen erfolgreichen öffentlichen HTML-Abruf. Daraufhin wurde vor einem eigenen Abruf html_addendum_plan.md angelegt. Der HTML-Text wurde selbst abgerufen und gelesen, nicht aus dem Parent-Hinweis rekonstruiert.

- Exakte URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC3466558/
- UTC-Anfang: 2026-09-20T15:03:35.729337+00:00; Ende: 2026-09-20T15:03:36.244592+00:00.
- HTTP 200, 198404 Bytes, SHA256 cebc5432cd4077f1ceab9e5be25ac06c8ee17cf4e1572bbfa7f243b755526012.
- Archiv: html_raw/gaddameedhi_html.response; URL/Status/Header in html_raw/gaddameedhi_html.meta.json; nummerierte Lesefassung in html_raw/gaddameedhi_html.txt.
- Eine neue Anfrage von höchstens drei genehmigten; mit den sieben vorherigen Volltextanfragen insgesamt acht von ursprünglich zwölf. Keine Weiterleitung, kein Retry, kein Supplement-/Bildabruf.

Der vorherige Fehler war eine zu enge Zugangsprüfung: API-Fehler und Abstract-only-EFetch wurden korrekt dokumentiert, aber der reguläre HTML-Zugang war noch nicht geprüft. Jetzt ist die Beschaffungslücke für Gaddameedhi geschlossen. Zwei Haupttexte sind in dieser Folgeprüfung zugänglich und gelesen (Dickmeis und Gaddameedhi); Gauger, Ozturk und Gery2007 bleiben im hier beschafften Bestand ohne Originalhaupttext. Der HTML-Erfolg ersetzt oder verändert keine historische API-Antwort. Die OpenAlex-Konfliktkante wird nicht verwendet.

Gelesen wurden die relevanten Results, Discussion, Materials and Methods und die Textlegenden der Abbildungen 1–9. Die Bilddateien und Supplemente wurden nicht gesondert heruntergeladen oder visuell neu ausgewertet. Quantifizierungsbehauptungen stammen aus Text/Legenden; keine eigene Densitometrie oder Reanalyse.

## Direkte PER1-Nichtreproduktion: Fig. 8

Results, Abschnitt "Effect of PER1 downregulation or overexpression on ATM-Chk2 mediated DNA damage checkpoints and apoptosis", Leseblöcke 91–95. Originalreferenz 4 benennt Gery2006 mit DOI 10.1016/j.molcel.2006.03.038 (Leseblock 144). Die Referenzbeziehung wurde im Originalartikel geprüft.

H1, Block 92: "the NCI-H460 human cancer cell line that was used in the previous study." Gaddameedhi prüft damit ausdrücklich das zuvor verwendete humane Lungenkrebsmodell. H2, derselbe Absatz: "downregulation of PER1 does not affect IR-induced ATM signaling as measured by Chk2 and p53 phosphorylation, nor does it affect apoptosis as measured by PARP-1 cleavage."

Überexpression wurde separat getestet. H3, Block 95, Fig. 8C/D: "they were indistinguishable from the control, vector-transfected cells at two different IR doses used". Überproduktion von PER1 wird im Resultattext ausdrücklich bestätigt. Der Nullbefund bezieht sich auf die dort geprüften Signal- und Spaltungsmarker; er ist kein direkter Beweis fehlender physischer PER1-ATM/Chk2-Bindung. Eine neue Bindungsanalyse wird in diesem Versuch nicht beschrieben.

Protokoll laut Methods und Fig.-8-Legende:

- NCI-H460 aus ATCC, RPMI-1640 mit 10% FBS; siRNA gegen PER1 versus non-target siRNA; Überexpression mit V5-markiertem murinem Per1 versus pCDNA3-Leervektor in humanen Zellen.
- H9, Fig. 8, Block 94: "irradiated with 0, 10 or 30 Gy of IR and allowed to grow for 48 h". Immunoblots 48 Stunden nach IR; Fig. 8C nennt 72 Stunden Überexpression. Der allgemeine Methodenteil nennt dagegen 48 Stunden Transfektion. Diese Zeitangaben werden nicht stillschweigend gleichgesetzt.
- Chk2-/p53-Phosphorylierung beim Knockdown, Chk2-Phosphorylierung bei der Überexpression und PARP-Spaltung als Apoptosemarker; laut Legende mindestens drei unabhängige Experimente mit Mittelwert/Standardabweichung. Dies sind Wiederholungen innerhalb derselben Arbeit.

Klassifikation: direkte, von einer anderen Autorengruppe durchgeführte Nichtreproduktion der berichteten funktionellen PER1-Abhängigkeit von IR-Signaling und Apoptose im selben benannten Zelllinienmodell, unter dem hier beschriebenen Protokoll. Die Autorenlisten von Gery2006 und Gaddameedhi2012 überschneiden sich nicht. Dies belegt keine identischen Zellbestände oder vollständige methodische Gleichheit.

## Klonogenes Überleben: Fig. 9

Results, "Effect of PER1 levels on clonogenic survival to IR of human cancer cell lines", Blöcke 96–99. NCI-H460 und HCT-116 werden ausdrücklich als bereits in der früheren Arbeit verwendete Zelllinien bezeichnet. H4, Block 97: "neither downregulation nor overexpression of PER1 affects the survival of these two human cancer cell lines against IR."

PER1-siRNA oder Expressionsvektor, anschließend IR und Koloniebildung. Fig. 9A nennt 48 Stunden siRNA, Aussaat von 500 Zellen je Vertiefung, acht Stunden Anheften, 7–10 Tage Wachstum, Kolonien mit mehr als 50 Zellen. Fig. 9B nennt HCT-116, ebenfalls 48 Stunden siRNA; Mittelwerte aus drei biologischen Experimenten. Der allgemeine IR-Survival-Methodenteil nennt 75–100 lebensfähige Zellen pro Vertiefung, triplikate Ansätze und Dosen 0, 2, 2,5, 4, 5, 6, 7,5, 8 und 10 Gy. Nicht alle diese Dosen werden hier ohne Bildprüfung jedem Fig.-9-Panel zugeordnet. Die unterschiedlichen Aussaatangaben sind als allgemeines versus figurspezifisches Protokoll erhalten.

Klassifikation: direkte vergleichende Gegenprüfung der PER1-abhängigen IR-Empfindlichkeit in den benannten humanen Zelllinien, ergänzend zu den Proteinmarkern aus Fig. 8. Ein nicht nachgewiesener Unterschied ist kein formaler Äquivalenznachweis; Konfidenzgrenzen für eine biologisch relevante Minimaldifferenz oder eine entsprechende Poweranalyse werden hier nicht abgeleitet.

## Positiver Befund, den das Abstract verdeckt: Fig. 7

Results, "Effect of clock gene downregulation on apoptosis", Blöcke 86–89. H5, Block 87: "PER1/2 downregulation reduces apoptosis". Konkret sinken PARP-1- und Caspase-3-Spaltung in primären Maus-Hautfibroblasten nach PER1/2-Downregulation bei allen getesteten UV-Dosen. CRY1 ist dabei ebenfalls vermindert; eine isolierte, von anderen Uhrkomponenten unabhängige PER-Wirkung ist damit nicht bewiesen.

H10, Fig. 7, Block 89: "irradiated with 0, 5, 10 or 25 J/m2 UVC, allowed to grow for 24 h". siRNA-behandelte primäre Maus-Hautfibroblasten, mindestens drei unabhängige Experimente; cleaved PARP und cleaved Caspase-3 als Marker. Die allgemeinen Methoden nennen 48 Stunden siRNA vor UV/IR. Es handelt sich um akute Herunterregulation im Apoptoseversuch, nicht um eine Tumorkohorte oder bloß den konstitutiven Per1/Per2-Doppelknockout aus den Survivalexperimenten.

Weitere Differenzierung: H6, Block 87: "CLOCK and BMAL1 downregulation moderately enhances apoptosis at low UV dose but not at the high dose". Dessen Bedeutung bezeichnen die Autoren als unklar. Nach CRY1/2-Downregulation steigt PER1/2, ohne dass daraus verstärkte Apoptose folgt. Es gibt somit weder eine durchgängige Nullwirkung noch eine einfache monotone Beziehung "mehr PER bedeutet mehr Apoptose".

Klassifikation: kontextabhängiger funktioneller PER1/2-Befund, richtungskonsistent mit einer proapoptotischen Funktion, aber keine spezifische Replikation von Gerys PER1-IR-ATM/Chk2-Befund. Mausfibroblasten, kombiniertes PER1/2-Knockdown, UV und 24-Stunden-Endpunkt unterscheiden sich vom humanen PER1-/IR-Versuch. Fig. 7 und Fig. 8 widersprechen sich deshalb nicht automatisch.

## Knockout-Survival, Reparatur und Checkpoint getrennt halten

Die Arbeit enthält daneben primäre Maus-Embryofibroblasten (Clock−/−, Bmal1−/−) und Hautfibroblasten (Cry1−/−Cry2−/−, Per1−/−Per2−/−), verglichen mit als isogen bezeichneten Wildtypen. Genotypen sind genannt; genaue molekulare Allelnamen, Mausstamm und Geschlecht sind im gelesenen Methodenteil nicht ausgeführt. Diese Details werden nicht aus zitierten Mausarbeiten ergänzt.

Fig. 1/4/5 berichten keine veränderte klonogene Empfindlichkeit gegenüber UV, IR bzw. Mitomycin C. Fig. 2/3 prüfen CPD- und (6–4)-Photoproduktentfernung nach 5 J/m² UVC über 0–24 Stunden. Das sind andere Endpunkte als die siRNA-Apoptosemarker. H7, Results zur Checkpointantwort, Block 83: "different basal levels of checkpoint and apoptosis proteins that made comparison with the wild-type problematic after genotoxic stress." Deshalb wechselten die Autoren für diese Signal-/Apoptoseprüfungen zur akuten siRNA-Behandlung primärer Hautfibroblasten. Fig. 6 berichtet unveränderte Chk1-Phosphorylierung nach 5 J/m² UVC bei 0, 0,5 und 1 Stunde, nicht eine vollständige Prüfung aller Checkpoints unter allen Bedingungen.

## Grenzen der Neubewertung

Der Gery2006-Originalhaupttext wurde in diesem Nachtrag nicht zusätzlich beschafft. Gleiche Zellliniennamen und frühere Claims werden durch Gaddameedhis ausdrückliche Angaben und die geprüfte Originalreferenz gestützt; ein unabhängiger Schritt-für-Schritt-Abgleich beider Originalprotokolle bleibt aus. Offene Vergleichspunkte sind Zellpassage/-authentifizierung, Konstrukte und siRNA-Sequenzen, Effizienz/Expressionshöhe, Transfektions- und Erntezeitpunkte, Strahlenquelle/-dosis und mögliche Zellsynchronisierung. Die zeitlichen und Aussaatunterschiede innerhalb von Gaddameedhis Methoden/Legenden wurden oben ausgewiesen.

H8, Discussion / Cell biology and in vivo biochemistry, Block 115: "these systems have serious limitations with regard to studying outputs that are clock-controlled at animal level but not at tissue culture". Die Autoren selbst begrenzen die Übertragbarkeit von Zellkultur auf den Organismus. Die Diskussion zitiert außerdem andere positive und negative Studien; deren Aussagen werden hier nicht als eigene Volltextprüfung dieser anderen Arbeiten ausgegeben.

Für Aufgabe 1(d) ist daher die Formulierung "gezielte Nichtreproduktion spezifischer funktioneller PER1-/IR-Befunde in denselben benannten Krebszelllinien, bei verbleibenden Protokollgrenzen" gerechtfertigt. Nicht gerechtfertigt sind "PER1 hat keine DNA-Schadensfunktion", "Gery vollständig falsifiziert" oder "Fu2002 widerlegt". Der positive murine PER1/2-/UV-Apoptosebefund muss daneben stehen. Historische Erstpriorität und Vollständigkeit werden weiterhin nicht beansprucht.

## Offline-Verifikation

html_evidence.json enthält zehn kurze Zitate mit exakter Leseblocknummer und Abschnitt. verify_html_addendum.py prüft sie gegen die aus dem archivierten HTML abgeleiteten Blöcke und gegen diesen Bericht, außerdem SHA256/Bytes/Artikelidentität, das Anfragebudget, die Verweise in den historischen Records und die Unverändertheit aller zuvor archivierten raw/- und fulltext_raw/-Dateien.

Befehle vom Workspace-Root:

```sh
python3 text_mining/pilot_task1d/followup/html_addendum.py fetch
python3 text_mining/pilot_task1d/followup/html_addendum.py text
python3 text_mining/pilot_task1d/followup/pilot.py export
python3 text_mining/pilot_task1d/followup/verify_html_addendum.py
python3 text_mining/pilot_task1d/followup/validate.py
```

fetch verwendet bei vorhandener identischer URL den Cache; text, export und beide Prüfungen sind offline. Alte Abstract-Extraktion und Aussagefelder in records.csv bleiben historisch erhalten; current_review_ref/current_review_status machen für PMID 22918252 deutlich, dass dieser Nachtrag Vorrang hat. fulltext_eligibility in diesen alten Suchrecords bleibt ein historischer Review-Workflowstatus und ist nicht der heutige Beschaffungsstatus. Keine Hauptreview-Einschlussentscheidung wird hier neu behauptet.

Ausgeführt: `python3 text_mining/pilot_task1d/followup/html_addendum.py fetch` und `python3 text_mining/pilot_task1d/followup/html_addendum.py text`, beide Exitcode 0 (HTTP 200, 198404 Bytes; 230 Leseblöcke). `python3 text_mining/pilot_task1d/followup/pilot.py export`: Exitcode 0, 142 Records/99 eindeutige Berichte. `python3 text_mining/pilot_task1d/followup/verify_html_addendum.py` und `python3 text_mining/pilot_task1d/followup/validate.py`: jeweils PASS, Exitcode 0. Zehn blockgenaue Zitate, Identität/Hash/Byteumfang, Parsercheck und Nachtragverweis geprüft; alle 76 vorherigen Rohartefakte unverändert. Ausgabe in html_verification.log. Der alte Validator erwähnt weiterhin die offene OpenAlex-Konfliktkante, die in dieser Neubewertung nicht verwendet wird.
