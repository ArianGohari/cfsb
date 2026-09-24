# Aufgabe 1(d): begrenzter Folgearbeiten-Pilot

Aktualisierung 20.09.2026: Für Gaddameedhi2012 gilt der [vorrangige HTML-Volltextnachtrag](html_addendum.md). Fig. 8/9: gezielte Nichtreproduktion spezifischer PER1-/IR-Befunde in denselben benannten humanen Zelllinien. Fig. 7: verminderte UV-Apoptose nach PER1/2-Knockdown in Mausfibroblasten. Die folgende Abstract-Auswertung ist historisch und darf nicht als pauschale Nullwirkung aller DNA-Schadensantworten übernommen werden. Auch records.csv verweist über current_review_ref auf den Nachtrag.

Stand: 20.09.2026. Sieben empirische Folgearbeiten wurden anhand ihrer Abstracts ausgewertet. Sie zeigen stützende PER1-Befunde, zusätzliche systemische Bedingungen der Uhr-Zellzyklus-Kopplung und abweichende Folgen von Uhrgenverlust. Eine direkte Replikation oder Widerlegung des gesamten Fu2002- oder Matsuo2003-Befunds ist damit nicht nachgewiesen. Historische Priorität bleibt offen.

Nur dieses followup-Verzeichnis wurde bearbeitet. project.md (1d), protocol.md und tracking.md wurden gelesen; history/ wurde nicht verwendet. Dieser unabhängige Recherchelauf ist kein Beleg für die Unabhängigkeit der zugrunde liegenden Studien. Keine qmd-Änderungen, kein Haupteinschlussbestand, kein primärer Graph.

## Abruf und Auswahl

Der Suchplan steht in plan.md und wurde vor dem ersten API-Abruf angelegt. Abruffenster: 2026-09-20T14:07:38.367959+00:00 bis 2026-09-20T14:10:33.818893+00:00. 30 HTTP-Anfragen, alle HTTP 200, keine Keys oder Zugangsdaten. OpenAlex war erreichbar; ein Ausfall-Fallback war nicht nötig. Europe PMC lieferte die Abstract-Evidenz, OpenAlex die bibliografischen Kanten.

manifest.json enthält exakte API-URLs, Query, UTC, HTTP-Status, Trefferzahl, abgerufenen Umfang, Sortierungsangaben und SHA256. raw/ enthält unveränderte JSON-Antworten und Metadaten je Anfrage. Bei allen Suchen wurde nur die erste Seite abgerufen. Die folgenden Trefferzahlen sind Quellmeldungen, keine relevanten Berichte und keine Studienzahlen.

| Europe-PMC-Suche | Gemeldet | Abgerufen |
|---|---:|---:|
| fu2002 / matsuo2003 / gery2006 | 0 / 2 / 0 | 0 / 2 / 0 |
| clarify_fu / clarify_matsuo / clarify_gery | je 1 | je 1 |
| per2_tumor | 6890 | 20 |
| per1_damage | 2294 | 20 |
| wee1_cycle | 762 | 20 |
| clock_resistance | 2647 | 20 |
| cry_p53 | 1687 | 20 |
| period_loss | 30844 | 20 |
| clarify_period_cancer | 42 | 5 |
| clarify_cry_cancer | 6 | 5 |
| clarify_clock_damage | 16 | 5 |
| clarify_glucocorticoid / clarify_per1_silencing | je 1 | je 1 |

Die erste Autorensuche löste die Seeds nicht zuverlässig auf. Die zwei Matsuo-Treffer waren fachfremd; sie bleiben als Suchrecords erhalten. Drei genaue Titelsuchen verifizierten danach die Identitäten. Die verbleibenden fünf Klärungsabfragen zielten auf frühe empirische Arbeiten; die beiden DOI-Abfragen stammen aus der gelesenen OpenAlex-Zitationsseite von Gery2006. Die Suche nach "period" lieferte fünf fachfremde klinische Treffer. Sie wurden nicht als Uhrgenbefunde verwendet.

Abweichung vom Plan: Für Europe PMC wurde kein expliziter Sortierparameter gesetzt. Die geplante Relevanzsortierung ist daher nicht gesichert; der Dienststandard lieferte in den breiten Suchen überwiegend neue Arbeiten. Das Manifest benennt diesen Standard ausdrücklich. Die breiten Suchen enthielten viele Reviews und wurden nicht vollständig auf Abstract-Ebene gescreent. Das Klärungsbudget von acht Abfragen war anschließend ausgeschöpft; keine zusätzliche Suche nach einem passenden PER2-Gegenbefund wurde erzwungen.

records.csv enthält 142 Europe-PMC-Records vor Deduplikation: 99 eindeutige Berichte, 43 Duplikatrecords. Behalten wird deterministisch die erste Record-ID nach sortierter search_id, anhand PMID, ersatzweise DOI/Quell-ID. Sieben Berichte sind explorativ ausgewählt, drei als Seeds geprüft; 89 bleiben not_processed. Diese Restmenge ist kein fachlicher Ausschluss. OpenAlex-Treffer sind separat in raw/ und manifest.json erhalten und nicht mit diesen Europe-PMC-Zahlen vermischt. Alle Volltexteignungsentscheidungen bleiben not_processed. Studienzahl und Biasbewertung sind offen.

## Historische Ausgangspunkte

Identitäten wurden über Titel, Autoren, Jahr, DOI und PMID in Europe PMC sowie Titel/Jahr/DOI in OpenAlex geprüft.

| Seed | Verifizierte IDs | Gelesene Aussage und Grenze |
|---|---|---|
| Fu et al. 2002 | PMID [12372299](https://europepmc.org/article/MED/12372299); DOI [10.1016/S0092-8674(02)00961-3](https://doi.org/10.1016/S0092-8674(02)00961-3); [W2161548459](https://openalex.org/W2161548459) | mPer2-defiziente Mäuse, Gammastrahlung, mehr Tumorentwicklung und weniger Thymozytenapoptose. Abstract: "these mice show a marked increase in tumor development and reduced apoptosis in thymocytes." Exaktes Allel und Dosis hier unbekannt. |
| Matsuo et al. 2003 | PMID [12934012](https://europepmc.org/article/MED/12934012); DOI [10.1126/science.1086271](https://doi.org/10.1126/science.1086271); [W1997179110](https://openalex.org/W1997179110) | Regenerierende Mausleber, Uhrkontrolle von Zellzyklusgenen/Cyclin B1-Cdc2. Abstract: "expression of wee1 was directly regulated by the molecular components of the circadian clockwork." Kein Tumorversuch im Abstract beschrieben. |
| Gery et al. 2006 | PMID [16678109](https://europepmc.org/article/MED/16678109); DOI [10.1016/j.molcel.2006.03.038](https://doi.org/10.1016/j.molcel.2006.03.038); [W2163183531](https://openalex.org/W2163183531) | Humane Krebszellen, PER1-Überexpression/Hemmung, DNA-Schadensapoptose und ATM/Chk2-Interaktion. Abstract: "Overexpression of Per1 sensitized human cancer cells to DNA damage-induced apoptosis". Zelllinien und Stressdosis hier unbekannt. |

Diese Seeds sind historische Kandidaten für bestimmte Aussagen, keine geprüften Erstentdeckungen. Frühere Literatur wurde nicht ausreichend gesucht, um Priorität zuzuweisen.

## Zitationsverbindungen

Die OpenAlex-cites-Abfragen meldeten 1264 (Fu), 1142 (Matsuo) und 625 (Gery) Werke; abgerufen wurden jeweils die ersten 25 nach publication_date:asc. Diese frühe Seite kann späte Folgearbeiten nicht abdecken. Für die sieben ausgewählten Arbeiten wurden deshalb zusätzlich einzelne DOI-Work-Objekte mit referenced_works abgerufen.

| Folgearbeit | Fu2002 | Matsuo2003 | Gery2006 |
|---|---|---|---|
| Gauger 2005 | vorhanden | vorhanden | zeitlich widersprüchliche API-Kante |
| Gery 2007 | vorhanden | vorhanden | vorhanden |
| Dickmeis 2007 | vorhanden | vorhanden | vorhanden |
| Ozturk 2009 | vorhanden | vorhanden | vorhanden |
| Hoffman 2010, PMID 20334671 | nicht in Referenzliste | vorhanden | nicht in Referenzliste |
| Gaddameedhi 2012 | vorhanden | nicht in Referenzliste | vorhanden |
| Yu 2013 | nicht in Referenzliste | vorhanden | nicht in Referenzliste |

"Vorhanden" bezeichnet nur einen Eintrag in der gespeicherten OpenAlex-Referenzliste. Fehlende Kanten sind kein Beweis fehlender Originalzitate. Gauger2005 -> Gery2006 ist chronologisch unplausibel und bleibt als Metadatenkonflikt offen; die Originalreferenzliste wurde nicht im Volltext geprüft. Auch ein fachfremder Titel auf der Gery-Zitationsseite mahnt zur Vorsicht bei der API-Verknüpfung. Aus keiner Kante wird Replikation, Bestätigung oder Priorität abgeleitet.

## Sieben ausgewählte empirische Folgearbeiten

Alle folgenden Aussagen beruhen auf vollständig gelesenen, gespeicherten Abstracts, nicht auf Volltexten. Kurze Zitate werden offline gegen den Originalstring geprüft. Kontextlücken bleiben ausdrücklich offen. Die Auswahl erfolgte qualitativ nach thematischer Nähe, experimentellen Befunden und unterschiedlichen Kontexten; kein validiertes Screeningmodell, keine Effektgrößensynthese.

### 1. Gauger MA et al. (2005)

Cryptochrome, circadian cycle, cell cycle checkpoints, and cancer.

Cry1/Cry2-Verlust erhöhte im untersuchten Mausmodell die spontane bzw. strahleninduzierte Krebsprädisposition laut Abstract nicht; Strahlenmorbidität/-mortalität und zelluläre Checkpointantwort waren gegenüber Wildtyp unverändert.

Kontext: Maus Cry1-/- Cry2-/- und daraus gewonnene Fibroblasten; ionisierende Strahlung, bei Fibroblasten auch UV. Strahlendosis und genetischer Hintergrund im Abstract nicht genannt.

Einordnung: Gegenbefund zur pauschalen Annahme, jeder Uhrverlust fördere Tumoren. Andere Gene als Fu2002, daher keine direkte Widerlegung von PER2.

Abstract-Beleg: "the mutant mice are indistinguishable from the wild-type controls with respect to radiation-induced morbidity and mortality."

PMID [16061665](https://europepmc.org/article/MED/16061665); DOI [10.1158/0008-5472.can-05-1119](https://doi.org/10.1158/0008-5472.can-05-1119). Rohquelle: `raw/clarify_cry_cancer.json`.

### 2. Ozturk N et al. (2009)

Loss of cryptochrome reduces cancer risk in p53 mutant mice.

Cry-Mutation verzögerte den frühen Krebsbeginn bei p53-mutierten Mäusen und verlängerte die mediane Lebensdauer um etwa 50%; erhöhte Apoptose nach genotoxischem Stress wurde als Teilmechanismus berichtet.

Kontext: Maus mit p53-Mutation plus Cry-Mutation; p53-mutierte Zellen unter genotoxischem Stress. Exakte Allele, Tumorhistologie und Stressdosis im Abstract nicht ausgewiesen.

Einordnung: Abweichender Tumorbefund bei Uhrgenverlust im p53-mutierten Kontext; kein PER2-Replikationsversuch und keine universelle Schutzwirkung bewiesen.

Abstract-Beleg: "the Cry mutation protects p53 mutant mice from the early onset of cancer and extends their median lifespan approximately 50%"

PMID [19188586](https://europepmc.org/article/MED/19188586); DOI [10.1073/pnas.0813028106](https://doi.org/10.1073/pnas.0813028106). Rohquelle: `raw/clarify_cry_cancer.json`.

### 3. Gaddameedhi S et al. (2012)

Effect of circadian clock mutations on DNA damage response in mammalian cells.

Mutierte Maus-Zelllinien zeigten gegenüber Wildtyp keine unterscheidbare DNA-Schadensantwort auf UV, ionisierende Strahlung und Mitomycin C.

Kontext: Maus-Zelllinien mit Mutationen in Bmal1, CLOCK, Cry1/2 oder Per1/2; Gewebekultur. Einzelne Zelllinien, Allele und Dosen aus dem Abstract unbekannt.

Einordnung: Empirische Einschränkung einer allgemeinen zellautonomen Uhr-DNA-Schadens-Kopplung. Unterschied zu humanen Tumorzellen bei Gery und zum Gesamtorganismus bei Fu; keine automatische Widerlegung.

Abstract-Beleg: "cells mutated in these genes are indistinguishable from wild-type in their response to UV, ionizing radiation and mitomycin C."

PMID [22918252](https://europepmc.org/article/MED/22918252); DOI [10.4161/cc.21771](https://doi.org/10.4161/cc.21771). Rohquelle: `raw/clarify_clock_damage.json`.

### 4. Gery S et al. (2007)

Epigenetic silencing of the candidate tumor suppressor gene Per1 in non-small cell lung cancer.

PER1 war in NSCLC-Proben und Zelllinien vermindert; forcierte Expression verringerte Wachstum und klonogenes Überleben. Epigenetische Mechanismen wurden untersucht.

Kontext: Humane nichtkleinzellige Lungenkarzinome und NSCLC-Zelllinien; forcierte PER1-Expression, Bisulfitsequenzierung und ChIP. Zellliniennamen und externer DNA-Schadensreiz im Abstract nicht genannt.

Einordnung: Stützende funktionelle Folgearbeit zu Gery2006, mit überlappenden Autoren. Keine unabhängige Replikation des ATM/Chk2- oder Bestrahlungsbefunds.

Abstract-Beleg: "Forced expression of Per1 in NSCLC cell lines led to significant growth reduction and loss of clonogenic survival."

PMID [17332281](https://europepmc.org/article/MED/17332281); DOI [10.1158/1078-0432.ccr-06-1730](https://doi.org/10.1158/1078-0432.ccr-06-1730). Rohquelle: `raw/clarify_per1_silencing.json`.

### 5. Dickmeis T et al. (2007)

Glucocorticoids play a key role in circadian cell cycle rhythms.

Reduzierte bzw. fehlende kortikotrope Hypophysenzellen schwächten Zellproliferationsrhythmen trotz unveränderter Uhrgenexpression; ein tonischer Glukokortikoidagonist rettete hochamplitudige Rhythmen.

Kontext: Zebrafischmutanten und Larven; Kortikotropen-/Cortisoldefizit und Glukokortikoidagonist. Allelnamen im Abstract unbekannt; kein Tumorexperiment.

Einordnung: Erweiterung der Uhr-Zellzyklus-Kopplung um systemische Signale. Keine Wiederholung der direkten WEE1-Regulation in regenerierender Mausleber bei Matsuo2003.

Abstract-Beleg: "high-amplitude rhythms can be rescued by exposing mutant larvae to a tonic concentration of a glucocorticoid agonist."

PMID [17373855](https://europepmc.org/article/MED/17373855); DOI [10.1371/journal.pbio.0050078](https://doi.org/10.1371/journal.pbio.0050078). Rohquelle: `raw/clarify_glucocorticoid.json`.

### 6. Hoffman AE et al. (2010)

Phenotypic effects of the circadian gene Cryptochrome 2 on cancer-related pathways.

CRY2-siRNA erhöhte nach chemischem Mutagen die unreparierte DNA-Schadenslast (P=0,040), ohne signifikante Änderung der Zellzyklusverteilung, Checkpoints oder Apoptose.

Kontext: Humane MCF-7-Brustkrebszellen; CRY2-siRNA; chemisches Mutagen im Abstract nicht benannt; Comet-Assay und Durchflusszytometrie.

Einordnung: Gemischte Schadensantwort-Endpunkte nach Verlust eines weiteren Uhrgens; keine direkte PER1/PER2-Replikation. Zelltyp und Knockdown unterscheiden sich von Maus-Knockouts.

Abstract-Beleg: "no significant influence of CRY2 knockdown on cell cycle distributions, cell cycle checkpoints in response to mutagen challenge, or apoptotic response was detected."

PMID [20334671](https://europepmc.org/article/MED/20334671); DOI [10.1186/1471-2407-10-110](https://doi.org/10.1186/1471-2407-10-110). Rohquelle: `raw/clarify_cry_cancer.json`.

### 7. Yu H et al. (2013)

Cryptochrome 1 overexpression correlates with tumor progression and poor prognosis in patients with colorectal cancer.

CRY1-Hochregulation förderte Proliferation und Migration von HCT116-Zellen; Herunterregulation hemmte Koloniebildung und Migration von SW480-Zellen. Hohe CRY1-Expression war klinisch mit schlechterem Überleben assoziiert.

Kontext: Humane kolorektale Karzinome (168 Primärproben), HCT116 und SW480; Hoch-/Herunterregulation von CRY1. Tiermodell erwähnt, aber Spezies/Details im Abstract nicht genannt; kein externer Stressreiz angegeben.

Einordnung: Weitere kontextabhängige pro-tumorale Uhrgenfunktion; klinische Assoziation und Zellintervention getrennt halten. Kein Nachweis, dass CRY1-Verlust generell vor Krebs schützt.

Abstract-Beleg: "down-regulation of Cry1 inhibited the colony formation and migration of SW480 cells."

PMID [23626715](https://europepmc.org/article/MED/23626715); DOI [10.1371/journal.pone.0061679](https://doi.org/10.1371/journal.pone.0061679). Rohquelle: `raw/clarify_cry_cancer.json`.

## Grenzen und nächste fachliche Prüfung

Die stärksten Gegenbefunde betreffen unterschiedliche Uhrgene, p53-Hintergründe oder kultivierte Zellen. Sie begrenzen die pauschale These "Uhrverlust fördert Krebs", widerlegen aber nicht allein die konkrete PER2-Beobachtung nach Gammastrahlung. Gery2007 stützt eine wachstumshemmende PER1-Funktion, prüft im gelesenen Abstract jedoch nicht dieselbe ATM/Chk2-DNA-Schadenskette. Dickmeis2007 ergänzt die Zellzykluskopplung um hormonelle Bedingungen, ohne Matsuos direkte WEE1-Regulation zu replizieren.

Quellenabdeckung, Dienstsortierung, knappe Seitenlimits und manuelle Auswahl verzerren diesen Pilot. Die sieben Veröffentlichungen sind keine sieben nachgewiesen unabhängigen Studien. Überlappende Autoren bei Gery2006/2007 und den Sancar-Arbeiten werden nicht als unabhängige Bestätigung gezählt. Für eine belastbare Reproduktionsaussage fehlen Volltexte, Allel-/Hintergrundabgleich, Stressdosen, Stichprobengrößen, Endpunktvergleich und Qualitätsbewertung. Priorität bleibt offen. Der Pilot ist begrenzt beendet, die systematische Aufgabe nicht.

## Reproduktion und Validierung

Vom Workspace-Root aus:

```sh
sh text_mining/pilot_task1d/followup/reproduce.sh
python3 text_mining/pilot_task1d/followup/validate.py
```

reproduce.sh dokumentiert alle genauen Suchbefehle. Bei vorhandenen Rohdateien verwendet es den Cache, rekonstruiert Manifest/CSV und validiert ohne erneuten Netzwerkabruf. Ein Live-Neulauf ist nur in einer ausdrücklich neu angelegten Kopie ohne raw/ vorgesehen; eingefrorene Rohdaten nicht löschen. extraction.json ist die manuelle, nachvollziehbare Abstract-Extraktion. report.md enthält deren Interpretation; API-Abruf und manuelle wissenschaftliche Bewertung sind getrennt.

Die Pilot-CLI beendet erfolgreiche Verarbeitung auch bei protokollierten HTTP-Fehlern mit 0; deshalb muss der HTTP-Status im Manifest zusätzlich geprüft werden. In diesem Lauf waren alle 30 Antworten HTTP 200. Die Prüfdatei kontrolliert Hashes, Abrufumfang, eindeutige Record-IDs, Dublettenverweise, DOI/PMID-Abgleich und wörtliche Abstract-Belege. Sie kann die biologische Interpretation nicht automatisch validieren.

Ausgeführt: `sh text_mining/pilot_task1d/followup/reproduce.sh`, PASS, Exitcode 0; `python3 text_mining/pilot_task1d/followup/validate.py`, PASS, Exitcode 0. Ausgabe: 30 Anfragen, 142 Records, 99 eindeutige Berichte, sieben ausgewählte Abstracts; Hashes, IDs, Belege und Deduplikation gültig. verification.log enthält die Ausgabe. Der zeitliche OpenAlex-Konflikt bleibt trotz technischer Validierung offen.

Lokale Vorprüfung: `git status --short; ls -la text_mining/pilot_task1d` hatte als zusammengesetzter Shellbefehl Exitcode 0 durch das erfolgreiche ls; git selbst meldete "not a git repository". Daher keine Git-basierte Änderungsprüfung. Alle Schreibbefehle waren auf followup/ beschränkt.
