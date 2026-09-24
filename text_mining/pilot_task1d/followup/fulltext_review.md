# Aufgabe 1(d): gezielte Prüfung der Folge- und Gegenbefunde

Aktualisierung nach direktem HTML-Abruf am 20.09.2026: Der [vorrangige Gaddameedhi-Nachtrag](html_addendum.md) ersetzt die untenstehende Beschaffungslücke und Abschnitt 1 einschließlich seiner Einordnung in der Abschlusstabelle. Gaddameedhi2012 ist jetzt im Haupttext geprüft: direkte Nichtreproduktion spezifischer PER1-/IR-Befunde in denselben benannten humanen Zelllinien (Fig. 8/9), zugleich verminderte UV-Apoptose nach PER1/2-Knockdown in Mausfibroblasten (Fig. 7). Kein pauschaler Nullbefund und keine totale Falsifikation. Aktueller Umfang: zwei geprüfte Haupttexte, drei verbleibende Originalvolltextlücken; acht Netzabfragen einschließlich HTML. Der folgende API-Bericht bleibt als historischer Audittrail erhalten.

Stand: 20.09.2026. Die angeforderte Volltext-Nachprüfung ist mit sieben neuen Netzabfragen beendet. Ein Originalhaupttext war über die erlaubten APIs erhältlich: Dickmeis2007. Für Gaddameedhi2012, Gauger2005, Ozturk2009 und Gery2007 bleiben Volltextlücken. Deshalb ist eine volltextgestützte abschließende Beurteilung der wichtigsten DNA-Schadens-Gegenbefunde hier nicht möglich. Die Lücken werden nicht durch Einzelheiten aus Sekundärzitaten oder Vorwissen gefüllt.

Für die Darstellung von Aufgabe 1(d) ergibt sich eine begrenzte, aber klare Aussage: Die ausgewählten Arbeiten tragen keine pauschale Schlussfolgerung, jeder Verlust einer circadianen Uhrfunktion steigere Krebs oder beeinträchtige jede DNA-Schadensantwort. Die verfügbaren Abstracts berichten Gegenbefunde in anderen genetischen oder zellulären Kontexten. Der gelesene Dickmeis-Volltext erweitert die Uhr-Zellzyklus-Kopplung um hormonelle Voraussetzungen; er bestätigt oder widerlegt nicht Matsuos spezifische WEE1-Regulation in regenerierender Mausleber. Eine unabhängige direkte Bestätigung einer der drei spezifischen Seed-Aussagen ist mit dieser Auswahl nicht nachgewiesen. Historische Erstpriorität bleibt offen.

## Beschaffung und Evidenzgrenzen

Der vorher angelegte Plan steht in fulltext_plan.md; die begründete EFetch-Ergänzung wurde vor Anfrage 7 dokumentiert. Keine Zugangsdaten, keine automatischen Weiterleitungen oder Retries, kein Verlagszugriff. Die OpenAlex-Konfliktkante Gauger2005 -> Gery2006 wurde weder verwendet noch zur Einordnung herangezogen.

| Anfrage, UTC am 20.09.2026 | HTTP | Inhalt und Status |
|---|---:|---|
| 14:54:03, Gaddameedhi Europe PMC | 500 | 150 Bytes, Internal Server Error |
| 14:54:04, PMC-ID-Converter Gauger/Gery | 200 | 508 Bytes, beide Identifier nicht in PMC gefunden |
| 14:54:04, Ozturk Europe PMC | 500 | 150 Bytes, Internal Server Error |
| 14:54:04, Dickmeis Europe PMC | 200 | 149302 Bytes, Artikel-XML mit Haupttext |
| 14:54:29, Gaddameedhi BioC | 200 | 6148 Bytes, "No result can be found" |
| 14:54:30, Ozturk BioC | 200 | 6148 Bytes, "No result can be found" |
| 14:55:14, PMC EFetch für beide Prioritätsartikel | 200 | 15020 Bytes, zwei bibliografische Einträge mit Abstract; beide ohne body |

Exakte URLs, UTC-Zeitstempel einschließlich Ende, Antwortheader, SHA256 und Bytes stehen in fulltext_manifest.json sowie den einzelnen *.meta.json-Dateien. Unveränderte Antwortbytes liegen in fulltext_raw/*.response. HTTP 200 wurde nicht mit erfolgreichem Volltextabruf gleichgesetzt. Die fehlende Bereitstellung über diese APIs bedeutet nicht, dass ein Artikel nirgendwo öffentlich lesbar wäre. Das nicht verbrauchte Budget von fünf Anfragen wurde nicht für weitere Zugangswege verwendet.

Gelesene Dickmeis-Version: PMC1828142.2, PMID 17373855, DOI 10.1371/journal.pbio.0050078. Geprüft wurden Einleitung, Resultate, Diskussion, Methoden und die relevanten im XML enthaltenen Abbildungslegenden. Abbildungsbilder und separate Supplementdateien wurden nicht heruntergeladen; Verweise auf Supplementresultate werden nur als Aussagen im Haupttext behandelt. fulltext_raw/dickmeis_epmc.txt ist eine nummerierte Lesefassung; XML bleibt die Strukturquelle. Sie enthält technisch doppelte Legendentexte, keine zusätzlichen Experimente.

## 1. Gaddameedhi et al. 2012: wichtigste direkte Gegenprüfung, Volltext offen

[Originalquelle PMC3466558](https://pmc.ncbi.nlm.nih.gov/articles/PMC3466558/), [DOI](https://doi.org/10.4161/cc.21771), PMID 22918252. Autoren: Gaddameedhi, Reardon, Ye, Ozturk, Sancar. Identität und Autorengruppe wurden im EFetch-Eintrag bestätigt; der dort gelieferte Text endet nach Abstract/Metadaten, nicht nach einer Methodensektion.

Geprüfte spezifische Behauptung: Mutationen in den positiven oder negativen Armen der molekularen Uhr müssten eine veränderte zelluläre Antwort auf DNA-Schädigung bewirken. Das Abstract benennt Maus-Zelllinien mit Veränderungen in Bmal1, CLOCK, Cry1/2 oder Per1/2 und UV, ionisierende Strahlung sowie Mitomycin C als Schädigungen.

Beleg G12, Abschnitt Abstract, fulltext_raw/priority_efetch.response, article mit PMID 22918252: "cells mutated in these genes are indistinguishable from wild-type in their response to UV, ionizing radiation and mitomycin C."

Klassifikation: gezielte empirische Gegenprüfung einer allgemeinen zellautonomen Uhr-DNA-Schadens-Kopplung, aber hier nur abstractgestützt. Gegenüber Fu2002/Gery2006 handelt es sich um eine andere Autorengruppe und teilweise andere Modelle. Gaddameedhi/Ozturk/Sancar überlappen mit Ozturk2009; die beiden Arbeiten zählen nicht als nachgewiesen unabhängige Bestätigungen voneinander.

Was damit begrenzt wird: die Verallgemeinerung, Uhrmutationen müssten in kultivierten Maus-Zellen stets einen DNA-Schadensphänotyp erzeugen. Nicht widerlegt sind dadurch Fus Tumorentwicklung nach Gammastrahlung im Gesamtorganismus und Gerys konkrete PER1-Manipulation in humanen Krebszellen. Auch eine fehlende Differenz in den untersuchten Tests ist kein allgemeiner Äquivalenznachweis.

Offen bleiben genaue Allelbezeichnungen, Ausgangsgewebe und Immortalisierung der Zelllinien, genetische Hintergründe, Dosen, Messzeitpunkte, einzelne Reparatur-/Checkpoint-/Apoptoseassays, Stichprobengrößen und statistische Nachweisgrenzen. Das Abstract nennt DNA-Schadensantwort als Sammelendpunkt; Details werden nicht ergänzt. Die gewünschte belastbare Volltextklassifikation ist für diese Prioritätsarbeit nicht abgeschlossen.

## 2. Gauger und Sancar 2005: anderer Uhrverlust, Volltext offen

[Europe PMC, PMID 16061665](https://europepmc.org/article/MED/16061665), [DOI 10.1158/0008-5472.CAN-05-1119](https://doi.org/10.1158/0008-5472.CAN-05-1119). Die vorhandene Europe-PMC-Antwort enthält keine PMCID; der neue PMC-ID-Converter bestätigt "Identifier not found in PMC". Über den vereinbarten PMCID-Weg wurde kein Volltext gefunden.

Beleg G05, Abschnitt Abstract, raw/clarify_cry_cancer.json, PMID 16061665: "We tested Cry1-/- Cry2-/- mice and fibroblasts derived from these mice".

Bekannter Kontext: Cry1/Cry2-Doppelverlust bei Mäusen, abgeleitete Fibroblasten; ionisierende Strahlung, in den Zellversuchen auch UV. Gemeldete Endpunkte sind strahleninduzierte Morbidität/Mortalität der Mäuse sowie Zellschädigung und DNA-Schadens-Checkpointantwort. Das Abstract berichtet keine Unterschiede zu Wildtyp und schließt daraus auf fehlende erhöhte spontane bzw. strahleninduzierte Krebsprädisposition. Die negative Tumoraussage ist mangels Volltext nicht anhand von Histologie, Inzidenztabelle oder Beobachtungsdauer nachgeprüft.

Klassifikation: Gegenbefund zur allgemeinen Gleichsetzung von Uhrverlust und Tumoranfälligkeit in anderem Genkontext. Gegenüber Fu2002 eine andere Autorengruppe, aber kein gleiches Per2-Allel und kein bestätigter identischer Versuchsaufbau. Damit wird der konkrete Per2-Befund nicht widerlegt. Die Knockout-Schreibweise ist bekannt; molekulare Allelnamen, Mausstamm, Geschlecht, Alter, Bestrahlungsdosis und Kohortengröße bleiben offen. Die zeitlich widersprüchliche OpenAlex-Verknüpfung zu Gery2006 ist für diese Aussage ohne Bedeutung und wird nicht benutzt.

## 3. Ozturk et al. 2009: Schutzbefund im p53-mutierten Kontext, Volltext offen

[Originalquelle PMC2634797](https://pmc.ncbi.nlm.nih.gov/articles/PMC2634797/), [DOI 10.1073/pnas.0813028106](https://doi.org/10.1073/pnas.0813028106), PMID 19188586. EFetch liefert Version PMC2634797.2 mit Abstract, aber ohne Haupttext. Autoren: Ozturk, Lee, Gaddameedhi, Sancar.

Bekannter Kontext: Mäuse mit p53-Mutation, zusätzliche Cry-Mutation und p53-mutierte Zellen unter genotoxischem Stress. Berichtet werden späterer früher Krebsbeginn, verlängerte mediane Lebensdauer und erhöhte Apoptoseempfindlichkeit als Teilmechanismus. Beleg O09, Abschnitt Abstract, fulltext_raw/priority_efetch.response, PMID 19188586: "extends their median lifespan ≈50%".

Klassifikation: Erweiterung des Cry-Kontexts um einen p53-mutierten Hintergrund und Gegenbefund zur pauschalen Tumorförderung durch Uhrverlust. Die Arbeit stammt aus derselben Sancar-Autorengruppe wie Gauger2005 und ist daher keine unabhängige Replikation dieser Arbeit. Gegenüber Fu2002 sind Gen und p53-Kontext verschieden.

Nicht belegt ist, dass Cry-Verlust allgemein vor Krebs schützt, dass jede p53-Mutation gleich reagiert oder dass der Per2-Bestrahlungsbefund falsifiziert wurde. Im zugänglichen Originalabstract stehen keine präzisen p53-/Cry-Allele, keine vollständige Genotypkombination, kein Maushintergrund, keine Tumorhistologie und keine Stressdosen. Insbesondere wird aus "p53 mutation" hier kein bestimmter Null- oder Missense-Genotyp erfunden. Ein höheres medianes Überleben ist zudem nicht automatisch eine quantifizierte Verringerung jeder Tumorinzidenz.

## 4. Gery et al. 2007: stützende PER1-Erweiterung, Volltext offen

[Europe PMC, PMID 17332281](https://europepmc.org/article/MED/17332281), [DOI 10.1158/1078-0432.CCR-06-1730](https://doi.org/10.1158/1078-0432.CCR-06-1730). Keine PMCID in vorhandenen Daten oder neuem ID-Converter-Ergebnis; kein Originalhaupttext über den vereinbarten Weg.

Bekannter Kontext: humane NSCLC-Proben und Zelllinien, geringe PER1-Expression und forcierte PER1-Expression, Untersuchungen epigenetischer Regulation. Beleg G07, Abschnitt Results des Abstracts, raw/clarify_per1_silencing.json: "Forced expression of Per1 in NSCLC cell lines led to significant growth reduction and loss of clonogenic survival."

Klassifikation: funktionell stützende Erweiterung der PER1-Wachstumshemmung aus Gery2006 auf einen genauer benannten Tumortyp. Überlappende Autoren, unter anderem Gery, Komatsu und Koeffler; keine unabhängige Bestätigung. Der Beleg wiederholt nicht die spezifische ATM/Chk2-Interaktion oder die DNA-Schadensapoptose unter demselben Reiz. Zellliniennamen, Konstrukte, Dosis/Expressionshöhe, Kontrollgestaltung und genaue Stichprobengrößen bleiben wegen fehlender Methoden offen. Keine bekannte exakte Mutation aus dem Abstract.

## 5. Dickmeis et al. 2007: unabhängige konzeptionelle Erweiterung von Matsuo

[Originalquelle PMC1828142](https://pmc.ncbi.nlm.nih.gov/articles/PMC1828142/), [DOI 10.1371/journal.pbio.0050078](https://doi.org/10.1371/journal.pbio.0050078), PMID 17373855. Quelle aller folgenden Volltextbelege: fulltext_raw/dickmeis_epmc.response, Lesefassung dickmeis_epmc.txt.

Die Originalreferenz 10 (XML-ID pbio-0050078-b010) nennt Matsuo et al. 2003 mit PMID 12934012 und DOI 10.1126/science.1086271. Das ist eine im Originaltext geprüfte Verbindung, keine OpenAlex-Annahme. Dickmeis, Lahiri, Nica, Vallone, Santoriello, Neumann, Hammerschmidt und Foulkes sind die Autoren; Ueli Schibler ist im XML als Editor geführt. Es gibt keine Autorenüberschneidung mit Matsuo, Yamaguchi, Mitsui, Emi, Shimoda und Okamura. Dies stützt die Einordnung als andere Arbeitsgruppe, beweist allein aber keine vollständige institutionelle oder experimentelle Unabhängigkeit.

### Modell, Allele und Endpunkte

Zebrafischlarven, hauptsächlich Tag 6 nach Befruchtung. Im Resultatabschnitt zur okulären Photorezeption sind chokh/rx3-Allele chkt25181 (schwach) und chkt25327 (stark) angegeben, typografisch chk mit hochgestelltem Allelsuffix. Beide sind blind; nur das starke Allel zeigt deutlich abgeschwächte S-Phasenrhythmen. lakritz/ath5 wird als Nullmutation bezeichnet und dient als weitere Blindheitskontrolle. Weitere untersuchte Mutanten betreffen lia/fgf3, pia/ascl1a, aal/eya1 und pit1; genaue molekulare Allelbezeichnungen werden für diese Vergleiche im gelesenen Haupttext nicht angegeben. Ein definierter genetischer Zuchtstamm ist dort ebenfalls nicht ausgewiesen; Vergleich jeweils mit Wildtyp-Geschwistern. Es handelt sich nicht um einen Per-/Cry-Uhrgenknockout.

Methoden, Textblöcke 87–89: Haltung ab Tag 2 bei 25 °C unter 12 h Licht/12 h Dunkel bis Tag 6; BrdU-Pulse bei ZT3, ZT9, ZT15 und ZT21. Gezählt werden BrdU-positive Kerne im Bereich zwischen Schwimmblase und Anus (Abb. 1), ein S-Phasenmarker, kein Tumorendpunkt. Die Methoden nennen 20 Minuten BrdU-Inkubation, Abb.-5-Legende für die kürzere Behandlungsserie 15-Minuten-Pulse. Diese Angabe wird nicht stillschweigend vereinheitlicht. Je nach Mutante wurden zehn bereits sortierbare Mutanten/Geschwister pro Flasche oder 25 Larven aus heterozygoten Kreuzungen verwendet; das ist keine globale Stichprobengröße für jede Abbildung.

Weitere Endpunkte: clock/per4-RNA-Rhythmen, Hypophysenmarker, Cortisolkonzentration und BrdU-Rhythmus nach Dexamethason. Das Rescue verwendet 25 μM Dexamethason, zunächst von Tag 2 bis Tag 6. Beleg D4, Methoden, Textblock 89: "a final concentration of 25 μM". Keine DNA-Schadensbehandlung oder Krebsinduktion; hormonelle und entwicklungsbiologische Perturbation.

### Was die Originalresultate tragen

1. Starkes rx3-Allel: verringerte S-Phasenamplitude gegenüber Geschwistern. Beleg D1, Results / Ocular Photoreception..., Textblock 22, Abb. 1C: "amplitude reduced from 4.0-fold to 2.3-fold". Blindheit allein erklärt diesen Unterschied nicht, weil schwaches rx3 und lak normale Rhythmen zeigen.
2. Die gemessenen Uhrenmarker bleiben rhythmisch. Beleg D2, Results / chokh/rx3 Mutant Fish Show Normal Clock Gene Expression, Textblock 30, Abb. 2A: "rhythmic expression of clock and per4 in both rx3 alleles is equivalent to that of their wild-type siblings." Dies prüft zwei Marker in Larvenextrakten, nicht jede Zelle und jeden Aspekt der Uhr.
3. Kortikotropendefizit und niedrigeres Cortisol begleiten den Phänotyp; die Mutantenserie trennt Hypophysenlinien. Im starken rx3-Allel ist Cortisol an ZT1 und ZT17 niedriger (Textblock 50, dort p < 0,0001). Dexamethason rettet die hohe Amplitude in starken rx3- und aal-Larven. Beleg D3, Results / The GR Agonist Dexamethasone..., Textblock 57, Abb. 4: "dexamethasone treatment fully restores high-amplitude circadian cell cycle rhythms in the mutants". Abb. 4 nennt vier unabhängige Experimente für rx3 und zwei für aal innerhalb dieser Arbeit; das sind keine unabhängigen Replikationspublikationen.
4. Konstante Hormonzufuhr genügt für das Rescue. Die Diskussion nennt als alternatives Modell permissive Glukokortikoidsignale oder zeitliche Steuerung der Signalantwort durch die Uhr (Textblock 76). Diese Modelle sind mechanistische Deutungen, nicht bereits identifizierte molekulare WEE1-Wirkpfade.

### Was gegenüber Matsuo wirklich bestätigt oder widerlegt wird

Klassifikation: unabhängige konzeptionelle Erweiterung der Uhr-Zellzyklus-Kopplung unter anderem Organismus-, Gewebe- und Eingriffskontext. Im Larvenmodell reichen erhaltene Rhythmen der gemessenen Uhrgene ohne ausreichendes endokrines Signal nicht für normale S-Phasenamplitude. Damit wird eine rein zellautonome Erklärung als allgemein hinreichende Erklärung eingeschränkt.

Beleg D7, Discussion, Textblock 84: "our results call for a re-evaluation of existing models that account for control of circadian cell cycle timing purely via the direct regulation of gene expression by peripheral clock components."

Matsuos konkrete Aussage betrifft direkte WEE1-Regulation und Cyclin-B1/Cdc2-vermittelte Mitosetaktung in regenerierender Mausleber. Dickmeis misst larvale S-Phasenrhythmen, keine Wiederholung von WEE1-Promotorbindung, WEE1-Expression oder hepatischer Mitose nach demselben Eingriff. Der Artikel liefert daher weder eine unabhängige Bestätigung genau dieser WEE1-Aussage noch deren Widerlegung. Die benötigte Replikation dieses spezifischen Mechanismus bleibt offen.

### Grenzen der mechanistischen Interpretation

Ein Rescue mit Glukokortikoidagonist identifiziert nicht automatisch den direkten molekularen Angriffspunkt. Beleg D5, Discussion, Textblock 74: "more indirect systemic effects certainly cannot be excluded." In steroidverarmter Zellkultur wird im selben Absatz sogar ein fehlendes Dexamethason-Rescue erwähnt: Beleg D6, "treatment with dexamethasone does not rescue the attenuation (unpublished data)." Dieser Befund ist nur als nicht gezeigte Beobachtung berichtet; er wird hier nicht wie eine abbildungsbelegte unabhängige Studie gewertet.

Die Abb.-5-Serie zeigt einen Einfluss des Behandlungsbeginns: Dexamethason am Vorabend kann die Rhythmusamplitude erhöhen, eine spätere Gabe nicht. Ob Mindestexpositionsdauer oder Tageszeit den Unterschied bestimmt, bleibt nach eigener Diskussion offen. Supplement S3 wird im Haupttext als Rescue nach Übergang in Dauerdunkel beschrieben; das zugehörige Bild wurde nicht geprüft. Es wurden weder Rohmesswerte neu analysiert noch Randomisierung, Verblindung oder statistische Power vollständig bewertet. Ein begrenzter negativer Markertest ist kein Beweis, dass alle peripheren Uhren unverändert funktionieren.

## Aussageprüfung für die Abgabe

| Ausgangsaussage | Ergebnis dieser Nachprüfung | Belastbarkeit |
|---|---|---|
| Fu2002: Per2-Mutation, Tumorentwicklung/DNA-Schadensantwort nach Bestrahlung | Cry-Verlust liefert laut Gauger/Ozturk abweichende Resultate in anderen Kontexten; keine direkte Per2-Falsifikation | Abstracts; Volltexte beider Folgearbeiten offen |
| Gery2006: PER1 und DNA-Schadensapoptose/Checkpointbezug | Gaddameedhi ist eine gezielte Gegenprüfung allgemeiner Uhrmutationsfolgen in Maus-Zelllinien; kein belegter identischer Replikationsaufbau | Prioritätsarbeit nur Abstract; Allel-/Assayabgleich offen |
| Gery2006: wachstumshemmende PER1-Funktion | Gery2007 stützt dies im NSCLC-Kontext | Abstract; gleiche Autorengruppe, keine unabhängige Replikation |
| Matsuo2003: Uhr reguliert WEE1/Mitose in Mausleber | Dickmeis ergänzt systemische Glukokortikoidbedingungen der Zellzyklusrhythmik im Zebrafisch | Haupttext geprüft; spezifischer WEE1-Mechanismus nicht repliziert |

Die geprüften Resultate rechtfertigen Kontextbindung statt einer universellen Krebswirkung von Uhrgenen. Eine Behauptung, die historischen Kernexperimente seien insgesamt reproduziert oder falsifiziert, wäre nach diesem Material zu stark. Die historische Prioritätsfrage erfordert ältere Originalarbeiten und wird durch diese gezielte Nachprüfung nicht entschieden.

## Offline-Verifikation und Reproduktion

fulltext.py verwendet nur die Python-Standardbibliothek, höchstens zwölf Anfragen, 40 Sekunden Timeout pro Anfrage und keine automatischen Weiterleitungen. Bestehende Antworten werden bei gleicher URL wiederverwendet. fetch_exitcode=0 bedeutet allein, dass eine Antwort oder ein Fehler gespeichert wurde; den Beschaffungserfolg bestimmen HTTP- und Inhaltsstatus.

Die sieben exakten Abrufbefehle stehen in fulltext_commands.sh. Das Skript läuft bei vorhandenem Cache ohne neue Netzabfragen. Alte raw/-Dateien wurden vor dem ersten neuen Abruf gehasht; verify_fulltext.py prüft Unverändertheit, neue Antwort-Hashes/Bytezahlen, Artikelidentität, fehlende bodies und elf kurze Zitate gegen die jeweils richtige Evidenzebene. Der Zitattest normalisiert nur Leerraum. Er prüft weder biologische Richtigkeit noch Vollständigkeit der Literatur.

Verifikationsbefehle vom Workspace-Root:

```sh
python3 text_mining/pilot_task1d/followup/verify_fulltext.py
python3 text_mining/pilot_task1d/followup/validate.py
```

Ausgeführt und bestanden: `python3 text_mining/pilot_task1d/followup/verify_fulltext.py` (PASS, Exitcode 0), `python3 text_mining/pilot_task1d/followup/validate.py` (PASS, Exitcode 0) und `sh text_mining/pilot_task1d/followup/fulltext_commands.sh` (Cache-Replay ohne neue Anfragen, PASS, Exitcode 0). Ausgabe: 7/12 Anfragen, 60 alte Rohdateien unverändert, ein Volltext, vier Volltextlücken, elf wörtliche Belege verifiziert. Der alte Abstract-Pilot besteht weiterhin mit 142 Records und 99 eindeutigen Berichten. Dessen Validierung meldet die bekannte OpenAlex-Konfliktkante weiterhin als offen; sie dient hier nicht als Evidenz. Ergebnisse und Exitcodes stehen in fulltext_verification.log. records.csv und report.md bleiben als historischer Abstract-Pilot unverändert; dieser Volltext-Nachtrag ersetzt sie nicht stillschweigend. Keine qmd-Dateien wurden bearbeitet.
