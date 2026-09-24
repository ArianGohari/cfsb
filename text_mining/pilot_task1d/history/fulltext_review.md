# Aufgabe 1(d): historische Beiträge und Grenzen der Prioritätsprüfung

Stand: 20.09.2026, begrenzter Abschlussstand nach zwölf neuen Netzabfragen. Die vier historischen Kandidaten bleiben auf Abstractniveau: Alle vier öffentlichen Verlagsabrufe lieferten HTTP 403. Zugänglich war der Originalvolltext von Anderson et al. (2000), einer älteren Referenz aus Fu (2002). Weitere Vorgänger wurden anhand ihrer Originalabstracts geprüft. Damit lassen sich spezifische Beiträge und ältere Forschungslinien trennen; eine globale Erstentdeckung ist für keinen Kandidaten nachgewiesen.

Der bisherige [Report](report.md), seine Rohdaten und CSV bleiben unverändert. Fu 2002 stammt als Suchkandidat aus dem assistentenseitig formulierten Rechercheplan/Delegationsauftrag, nicht vom Nutzer. Dieser Nachtrag ändert auch keine QMD. Alle neuen Abruf- und Prüfartefakte liegen unter [fulltext/](fulltext/).

## Ergebnis für die historische Darstellung

Im hier gezielt geprüften Bestand sind folgende spezifische Beiträge belegt, jeweils in dem unten genannten Kontext und auf der angegebenen Quellenebene:

| Arbeit | Spezifischer hier belegter Beitrag | Was daraus nicht folgt |
|---|---|---|
| Fu et al. 2002 | mPer2-defiziente Mäuse: Tumorneigung, verstärkte Tumorentwicklung nach Gammabestrahlung und veränderte DNA-Schadensantwort (Originalabstract) | Erste Entdeckung irgendeiner Beziehung zwischen Uhr, Licht und Krebs; universelle PER2-Tumorsuppression beim Menschen |
| Matsuo et al. 2003 | Circadiane Kontrolle von wee1 und mitoserelevanter Cyclin-B1-Cdc2-Aktivität in regenerierender Mausleber (Originalabstract) | Erste Beobachtung tageszeitlicher Zellteilungsrhythmen; hier volltextgeprüfte CLOCK/BMAL1-Promotorbindung |
| Gery et al. 2006 | Funktionelle Per1-Perturbation und DNA-schadensinduzierte Apoptose in humanen Krebszellen, Interaktion mit ATM/Chk2 (Originalabstract) | Erste Beziehung irgendeines PER-Gens zu Krebs; aus diesem Abstract allein bewiesene direkte Proteinbindung |
| Gréchez-Cassiau et al. 2008, online 2007 | Bmal1-Verlust, erhöhte/arrhythmische p21-Expression und verminderte Hepatozytenproliferation; Umkehr durch p21-siRNA (Originalabstract) | Erste Entdeckung circadianer Zellzyklusregulation oder zwingend erste Identifikation rhythmischen p21; unabhängige Replikation durch den Rescue innerhalb derselben Arbeit |

"Hier belegt" bezeichnet den überprüften Beitrag im begrenzten Quellenbestand. Es bedeutet nicht "weltweit zuerst". Die Auswahl war kandidaten- und referenzgeleitet; sie war keine Suche nach sämtlichen Vorläufern. Neuheitsformulierungen der Autoren werden unten als deren Anspruch zitiert, nicht als geprüfte wissenschaftshistorische Rangfolge übernommen.

## Quellenzugang und tatsächlich gelesene Texte

| Text | Gelesene Teile | Quellenebene und Beschränkung |
|---|---|---|
| Fu 2002 | Vollständiges `abstractText` im vorhandenen API-Record; Crossref-Referenzmetadaten | Kein Originalvolltext, keine Einleitung/Diskussion/Methoden oder Originalreferenzseiten gelesen |
| Matsuo 2003 | Vollständiges `abstractText`; Crossref-Referenzmetadaten | Kein Originalvolltext; ergänzend lokale Zou-Passage Zeile 49 als Sekundärdarstellung |
| Gery 2006 | Vollständiges `abstractText`; Crossref-Referenzmetadaten | Kein Originalvolltext; lokale Zou-Passage Zeile 51 nur sekundär |
| Gréchez-Cassiau 2008 | Vollständiges `abstractText`; Crossref-Referenzmetadaten | Kein Originalvolltext; Ausgabejahr 2008 und API-Erstpublikation 17.12.2007 getrennt |
| Anderson 2000 | Abstract; Introduction `para0005–0010`; Materials and methods `para0015–0035`; Results `para0040–0055`; Table 1; Legenden Fig. 1–3; Discussion `para0060–0090`; Referenzen 1–23 | Originalvolltext als JATS-XML. Abbildungsbilder selbst nicht abgerufen oder visuell geprüft; keine Rohversuchsdaten nachgerechnet |
| Neun weitere ältere Treffer | Acht vorhandene Originalabstracts vollständig; bei Jaffe 1954 nur Titel/Metadaten | Keine Volltextprüfung dieser Arbeiten |

Die [Belegdatei](fulltext/evidence.json) verknüpft jedes unten verwendete wörtliche Zitat mit Datei, PMID und Abschnitt. Textnormalisierung beim XML besteht ausschließlich im Zusammenführen von Textknoten und Whitespace. [Lesefassung Anderson](fulltext/anderson_fulltext.txt), [unveränderte XML-Antwort](fulltext/raw/anderson_fulltext.body).

## Fu 2002: PER2-spezifischer Beitrag innerhalb älterer Uhr–Tumor-Forschung

Loning Fu, Helene Pelicano, Jinsong Liu, Peng Huang und Cheng Lee: *The Circadian Gene Period2 Plays an Important Role in Tumor Suppression and DNA Damage Response In Vivo*. [DOI](https://doi.org/10.1016/S0092-8674(02)00961-3), [PMID 12372299](https://europepmc.org/article/MED/12372299). Quellenebene: [Originalabstract](raw/fu2002.json).

> "After gamma radiation, these mice show a marked increase in tumor development and reduced apoptosis in thymocytes."

Die Arbeit verbindet einen definierten circadianen Genkontext, mPer2-Defizienz, mit Tumorentwicklung und DNA-Schadensantwort im Mausmodell. Der Abstract nennt außerdem veränderte zeitliche Expression von Cyclin D1, Cyclin A, Mdm-2 und Gadd45alpha sowie dereguliertes c-myc. Das ist ein genspezifischer experimenteller Beitrag. Mutationsallel, Strahlendosis, Gruppengrößen und genaue Abfolge der Experimente wurden hier nicht anhand des Volltexts geprüft.

Ein Anspruch "Fu entdeckte 2002 den Zusammenhang von circadianer Uhr und Krebs" wäre zu breit. In Fus [Crossref-Referenzliste](fulltext/raw/fu_refs.body) stehen bereits Anderson 2000 (BIB2), Barbason 1995 (BIB6) und Hansen 2001 (BIB21). Der bibliografische Fundweg allein beweist ihre Befunde noch nicht; Anderson wurde deshalb im Originalvolltext gelesen, Hansen im Originalabstract. Die exakte Barbason-Titelabfrage lieferte keinen zuordenbaren Record. Barbason bleibt unaufgelöst und wird nicht inhaltlich als Originalbeleg verwendet.

### Anderson et al. (2000): Lichtregime und Mammatumoren, vor Fu

L. E. Anderson, J. E. Morris, L. B. Sasser und R. G. Stevens: *Effect of constant light on DMBA mammary tumorigenesis in rats*. [DOI 10.1016/S0304-3835(99)00320-1](https://doi.org/10.1016/S0304-3835(99)00320-1), [PMID 10695987 / PMCID PMC7127503](https://europepmc.org/articles/PMC7127503). Dies ist eine experimentelle Originalarbeit, keine Review-Aussage. Identität im abgerufenen XML anhand Titel, PMID und DOI bestätigt.

Ab dem 26. Lebenstag wurden je 50 weibliche Sprague-Dawley-Ratten nach gewichtsbasiert randomisierter Zuordnung entweder konstantem Licht (LL, 24:0) oder einem 8:16-Licht-Dunkel-Zyklus (LD) ausgesetzt. Beide Gruppen erhielten am Tag 52 intragastrisch 8 mg DMBA. Wöchentliche Palpation und Nekropsie am Tag 141 erfassten Mammatumoren (Materials and methods, `para0020–0035`).

Results, `para0050`:

> "gross inspection of mammary tissue in each rat revealed tumors in eight rats in the LL group and tumors in 19 rats in the LD group"

Table 1 bestätigt 8/50 gegenüber 19/50 Tieren mit Tumoren; der Ergebnistext nennt insgesamt 9 gegenüber 49 Tumoren. Dauerlicht erhöhte unter diesem Protokoll die Tumorlast also nicht. Die Autoren interpretieren den Befund als beschleunigte Differenzierung des Mammagewebes und ein dadurch verpasstes Empfindlichkeitsfenster für die DMBA-Gabe (`para0070`). Diese entwicklungsbiologische Erklärung ist ihre Interpretation; das Experiment perturbiert weder Per2 noch einen anderen spezifischen Uhrgen-Locus.

Discussion, `para0075`:

> "The results of this study are inconsistent with the results reported by Shah et al. [14], in which constant light resulted in increased tumor yield."

Die explizite Gegenüberstellung wurde im Originaltext gelesen. Shah et al. (1984) selbst wurden jedoch nicht abgerufen: Die Darstellung ihres Ergebnisses bleibt sekundär. Anderson diskutiert Unterschiede in Rattenstamm, DMBA-Dosis und vor allem Beginn der Lichtbelastung: eigene Exposition ab Tag 26 gegenüber Exposition der Muttertiere ab Konzeption und der Nachkommen ab Geburt in der zitierten Arbeit (`para0080`). Deshalb wird hier weder eine direkte Replikation noch eine endgültige Falsifikation von Shah behauptet. Erst recht ist Anderson 2000 keine Replikation oder Widerlegung des späteren Per2-Mausexperiments von Fu.

Discussion, `para0085`:

> "There are, however, important differences in mammary development and tumorigenesis between rat and human."

Anderson führt in der Einleitung auch Jöchle 1964 sowie weitere ältere Licht-/Melatonin-Arbeiten an (Referenzen 10–15). Diese Literaturangaben wurden gelesen, ihre Originalarbeiten nicht. Sie markieren eine noch ältere Forschungslinie, begründen aber keine hier geprüfte Erstentdeckung von 1964. Anderson selbst ist hier ein volltextbelegter älterer Beitrag zum Licht–Tumor-Zusammenhang, kein bewiesener PER2-Mechanismus und kein Nachweis, dass Dauerlicht generell schützt.

### Weitere ältere Originalabstracts

Hansen (2001), *Increased breast cancer risk among women who work predominantly at night*, [DOI](https://doi.org/10.1097/00001648-200101000-00013), [PMID 11138824](https://europepmc.org/article/MED/11138824): populationsbasierte Fall-Kontroll-Studie mit 7035 dänischen Brustkrebsfällen und individuell gematchten Kontrollen, rekonstruierte Beschäftigungsverläufe.

> "The odds ratio for breast cancer among women who worked at night at least half of a year was 1.5 (95% confidence interval, 1.2 to 1.7)"

Das ist eine beobachtete Assoziation vor Fu, kein experimenteller Nachweis, dass PER2-Verlust menschlichen Brustkrebs verursacht. Fu zitiert Hansen laut Crossref BIB21.

Filipski et al. (2002), *Host circadian clock as a control point in tumor progression*, [DOI](https://doi.org/10.1093/jnci/94.9.690), [PMID 11983758](https://europepmc.org/article/MED/11983758), API-Erstpublikation 01.05.2002, also vor Fus API-Datum 01.10.2002. Fundweg ist Gréchez-Cassiau bib44, nicht eine hier gefundene Fu-Referenz. Gelesen wurde das strukturierte Originalabstract einschließlich Methods und Results: SCN-Läsionen versus Sham-Operation bei Mäusen, transplantiertes Glasgow-Osteosarkom bzw. Pankreasadenokarzinom.

> "Both types of tumors grew two to three times faster in mice with SCN lesions than in sham-operated mice"

Damit ist auch eine experimentelle Beziehung zwischen dem circadianen System des Wirts und Tumorprogression schon vor Fu belegt. SCN-Zerstörung und Wachstum transplantierter Tumoren sind andere Perturbationen und Endpunkte als Per2-Defizienz und strahlenassoziierte Tumorentwicklung. Filipski nimmt Fu deshalb nicht automatisch den spezifischen mPer2-Beitrag vorweg.

## Matsuo 2003: Mechanismus statt Entdeckung von Teilungsrhythmen

Takuya Matsuo, Shun Yamaguchi, Shigeru Mitsui, Aki Emi, Fukuko Shimoda und Hitoshi Okamura: *Control Mechanism of the Circadian Clock for Timing of Cell Division In Vivo*. [DOI](https://doi.org/10.1126/science.1086271), [PMID 12934012](https://europepmc.org/article/MED/12934012). Quellenebene: [Originalabstract](raw/matsuo2003.json).

> "Among these genes, expression of wee1 was directly regulated by the molecular components of the circadian clockwork."

Der spezifische Beitrag betrifft die Kontrolle von Zellzyklusgenen und aktiver Cyclin-B1-Cdc2-Kinase in regenerierender Mausleber; ergänzend wird ein vom Zellzyklus unabhängig oszillierendes Uhrwerk in Einzelzellen beschrieben. Der Abstract allein nennt CLOCK/BMAL1 nicht ausdrücklich. Diese Zuordnung ist im [lokalen Zou-Markdown, Zeile 49](../../../part1/task1/sources/markdown/zou_2020_circadian_cell_cycle_checkpoints/zou_2020_circadian_cell_cycle_checkpoints.md) sekundär beschrieben, wurde aber in diesem Lauf nicht an Matsuos Originalmethoden und Promotorexperimenten geprüft. Eine unidirektionale Kopplung wird nicht auf alle Zelltypen oder Zustände verallgemeinert.

[Matsuos Crossref-Liste](fulltext/raw/matsuo_refs.body) führt wesentlich ältere Arbeiten an. Die Einträge enthalten auch Methodenhinweise, unveröffentlichte Daten und Danksagungstext; ihre Zahl ist keine Zahl unabhängiger Studien.

Buchi et al. (1991), *Circadian rhythm of cellular proliferation in the human rectal mucosa*, [DOI](https://doi.org/10.1016/0016-5085(91)90019-H), [PMID 2065918](https://europepmc.org/article/MED/2065918), Fundweg Matsuo `e_1_3_2_5_2`. Gelesener Originalabstract: 24 Untersuchungen bei 16 gesunden Männern, nüchtern bzw. ernährt, wiederholte Rektumbiopsien und ex-vivo-Thymidineinbau.

> "Both fasted and fed subjects showed significant circadian rhythms in thymidine incorporation, which peaked at about 7 AM."

Das zeigt eine ältere tageszeitliche Rhythmik eines DNA-Synthese-Maßes. Es belegt noch keine CLOCK/BMAL1–WEE1-Kausalkette.

Bjarnason, Jordan und Sothern (1999), *Circadian variation in the expression of cell-cycle proteins in human oral epithelium*, [DOI](https://doi.org/10.1016/S0002-9440(10)65306-0), [PMID 10027418](https://europepmc.org/article/MED/10027418), Fundweg Fu BIB9 und Gréchez-Cassiau bib17. Im gelesenen Originalabstract: sechs gesunde Personen, Mundschleimhautbiopsien alle vier Stunden, immunhistochemische Erfassung von p53, Cyclin E/A/B1 und Ki-67.

> "The finding of a circadian variation in the nuclear expression of p53 protein corresponding to late G1 is novel."

Das ist ein ausdrücklicher Neuheitsanspruch der Autoren für diesen p53-Befund. Er wurde nicht gegenüber sämtlicher Literatur vor 1999 verifiziert. Die Beobachtung ist älter als Matsuos Mechanismusarbeit, aber keine direkte PER2–p53-Bindungsuntersuchung.

Bjarnason et al. (2001), *Circadian expression of clock genes in human oral mucosa and skin: association with specific cell-cycle phases*, [DOI](https://doi.org/10.1016/S0002-9440(10)64135-1), [PMID 11337377](https://europepmc.org/article/MED/11337377), Fundweg Matsuo `e_1_3_2_32_2` sowie Gréchez-Cassiau bib13. Originalabstract: acht gesunde, tagsüber aktive Männer; Biopsien über 24 Stunden, Uhrgen-RNA und Thymidylatsynthaseaktivität.

> "This is the first human study to show a circadian profile of expression for all five clock genes as documented in rodents, suggesting their functional importance in man."

Auch dies ist ein eng formulierter Autorenanspruch, keine hier abschließend bestätigte Weltpriorität. Die mögliche Uhr–Zellzyklus-Verknüpfung wird aus zeitlichen Mustern abgeleitet; Matsuos spezifischer Mechanismus wird damit nicht bereits experimentell nachgewiesen.

Jaffe (1954), *Diurnal mitotic periodicity in regenerating rat liver*, [DOI](https://doi.org/10.1002/ar.1091200408), [PMID 14350262](https://europepmc.org/article/MED/14350262), ist über Matsuo `e_1_3_2_9_2` bibliografisch identifiziert. Die API liefert keinen Abstract. Daher nur ein älterer Recherchehinweis, kein hier gelesener Originalbefund und keine Grundlage für einen Erstentdeckungsanspruch.

## Gery 2006: Per1-Perturbation, nicht erste PER–Krebs-Assoziation

Sigal Gery, Naoki Komatsu, Lilit Baldjyan, Andrew Yu, Danielle Koo und H. Phillip Koeffler: *The circadian gene per1 plays an important role in cell growth and DNA damage control in human cancer cells*. [DOI](https://doi.org/10.1016/j.molcel.2006.03.038), [PMID 16678109](https://europepmc.org/article/MED/16678109). Quellenebene: [Originalabstract](raw/gery2006.json).

> "In addition, Per1 interacted with the checkpoint proteins ATM and Chk2."

Der Abstract berichtet verstärkte DNA-schadensinduzierte Apoptose nach Per1-Überexpression, Abschwächung nach Hemmung und Wachstumsreduktion nach ektopischer Expression in humanen Krebszelllinien. Dies ist der hier belegte spezifische funktionelle Beitrag. Die genaue Zelllinienauswahl, Dosierungen und Bindungsassays sind mangels Volltext nicht geprüft; die Koimmunpräzipitationsbeschreibung in Zou, Zeile 51, bleibt sekundär.

[Gerys Crossref-Referenzen](fulltext/raw/gery_refs.body) enthalten bereits Fu 2002 (bib9), Matsuo 2003 (bib17) und Chen 2005 (bib7). Chen et al.: *Deregulated expression of the PER1, PER2 and PER3 genes in breast cancers*, [DOI](https://doi.org/10.1093/carcin/bgi075), [PMID 15790588](https://europepmc.org/article/MED/15790588). Gelesener Originalabstract: 55 Brustkrebsfälle taiwanischer Frauen, Immunhistochemie, methylierungsspezifische PCR und Sequenzierung.

> "Our results reveal disturbances in the expression of the three period (PER) genes in most (>95%) of the breast cancerous cells in comparison with the nearby non-cancerous cells."

Die klinische PER-Expressionsassoziation geht damit Gery voraus. Sie ist aber keine vorausgehende Durchführung von Gerys Per1-Perturbations- und DNA-Schadensexperimenten. Aus den Zitierbeziehungen wird weder eine Priorität für ATM/Chk2-Bindung noch eine unabhängige Replikation abgeleitet.

## Gréchez-Cassiau 2008: funktionelle BMAL1–p21-Verknüpfung

Aline Gréchez-Cassiau, Béatrice Rayet, Fabienne Guillaumond, Michèle Teboul und Franck Delaunay: *The circadian clock component BMAL1 is a critical regulator of p21WAF1/CIP1 expression and hepatocyte proliferation*. [DOI](https://doi.org/10.1074/jbc.M705576200), [PMID 18086663](https://europepmc.org/article/MED/18086663). Quellenebene: [Originalabstract](raw/grechez2008.json); online 17.12.2007, Ausgabejahr 2008.

In Bmal1-/- Mäusen ist p21-Expression erhöht und nicht mehr rhythmisch. Der Abstract nennt antagonistische REV-ERBalpha/beta- und RORalpha4/gamma-Aktivitäten bei der p21-Transkriptionsregulation sowie reduzierte Proliferation p21-überexprimierender primärer Bmal1-/- Hepatozyten. Auf diesen letzten Phänotyp bezieht sich:

> "This phenotype could be reversed using small interfering RNA-mediated knockdown of p21WAF1/CIP1."

Die funktionelle Verknüpfung samt Rescue ist hier der spezifische Beitrag. Rhythmische Expression wurde auch in peripheren Mausorganen und serumgeschockten differenzierten Muskelzellen untersucht. Der Abstract belegt keine direkte BMAL1-Bindung am p21-Promotor und keinen Tumorendpunkt.

Die [Crossref-Liste](fulltext/raw/grechez_refs.body) enthält neben den anderen drei Kandidaten Grundschober 2001 (bib18) und Hirayama 2005 (bib20). Grundschober et al., *Circadian regulation of diverse gene products revealed by mRNA expression profiling of synchronized fibroblasts*, [DOI](https://doi.org/10.1074/jbc.M107499200), [PMID 11598123](https://europepmc.org/article/MED/11598123): Originalabstract zu synchronisierten Rattenfibroblasten, 9957 Transkripten, vierstündlicher Probenahme über 76 Stunden und 85 robust rhythmischen Genen.

> "Our pathway analysis of the mRNA profiling data strongly suggests a direct link between circadian rhythm and cell cycle."

Dieses Profiling belegt einen früheren molekularen Forschungsstand. Der gelesene Abstract spezifiziert p21 jedoch nicht. Ob p21 bereits in seinen Volltexttabellen vorkommt, bleibt ungeprüft. Deshalb wird Gréchez-Cassiau hier nicht zur ersten Entdeckung rhythmischen p21 erklärt.

Hirayama et al. (2005), *Common pathways in circadian and cell cycle clocks: light-dependent activation of Fos/AP-1 in zebrafish controls CRY-1a and WEE-1*, [DOI](https://doi.org/10.1073/pnas.0502610102), [PMID 16000406](https://europepmc.org/article/MED/16000406): gelesener Originalabstract, Zebrafisch-Z3-Zellen, Lichtantwort und AP-1-Hemmung.

> "Light induces the expression of zWee1, a cell cycle gene essential for G2/M transition, and zCry1a, a clock gene of the feedback regulatory loop."

Damit existierte vor Gréchez-Cassiau bereits eine andere mechanistische Uhr-/Zellzyklus-Verbindung. Sie ist weder dieselbe BMAL1–p21-Untersuchung noch eine kontextgleiche Replikation von Matsuos Mausleberexperiment.

## Reproduziert oder falsifiziert?

Dieser Lauf ist ein Prioritäts- und Vorgängercheck. Er bewertet keine zusätzlichen späteren Replikationsserien. Der gelesene Anderson-Volltext enthält einen expliziten Widerspruch zu einem älteren berichteten Ergebnis; wegen unterschiedlicher Protokolle und fehlender Lektüre des Shah-Originals wird daraus keine abschließende Falsifikation gemacht. Eine siRNA-Umkehr innerhalb Gréchez-Cassiau ist ein funktionelles Kontrollexperiment, keine unabhängige Replikation.

Für die vier Kandidaten lautet der belastbare Abschluss dieses Teilauftrags daher: spezifische Originalabstract-Beiträge identifiziert und gegen ältere Forschungslinien abgegrenzt; globale Priorität und unabhängige Reproduktion/Falsifikation hier nicht abschließend festgestellt. Die separate spätere Literaturauswertung anderer Arbeitsbereiche wird dadurch nicht ersetzt oder umgeschrieben. Die fehlenden Volltexte werden nicht als fachlicher Ausschluss behandelt.

## Abrufprotokoll, Grenzen und Reproduktion

[Plan vor Abruf](fulltext/plan.md), [Referenzsuchplan](fulltext/reference_search_plan.json), [begründete Suchkorrektur](fulltext/search_amendment.json), [Auswahl des letzten Volltexts](fulltext/fulltext_selection.json). Pro GET wurde die URL mit Zweck und UTC vorab in [requests.jsonl](fulltext/requests.jsonl) geschrieben. Je Request stehen Antwortstatus, Header, UTC-Endzeit, Bytezahl und SHA-256 in einer gleichnamigen `.meta.json`; die unveränderten Antwortbytes liegen unter `fulltext/raw/`. Die OA-Fundwege von Fu/Gery/Matsuo wurden aus bereits vorhandenen lokalen OpenAlex-Antworten übernommen, nicht neu abgefragt; Kopien stehen unter `fulltext/input/`.

Alle Abrufe am 20.09.2026 UTC:

| Nr. | ID / Quelle | Beginn UTC | HTTP | Ergebnis |
|---:|---|---|---:|---|
| 1 | fu_pdf / gespeicherte OA-URL | 14:40:49.770971 | 403 | Keine PDF; Fehlerbody gespeichert |
| 2 | gery_pdf / gespeicherte OA-URL | 14:40:49.879848 | 403 | Keine PDF; Fehlerbody gespeichert |
| 3 | grechez_pdf / gespeicherte OA-URL | 14:40:49.953622 | 403 | Keine PDF; Fehlerbody gespeichert |
| 4 | matsuo_page / Verlagsseite | 14:40:50.043750 | 403 | Kein Artikelvolltext; Fehlerbody gespeichert |
| 5 | fu_refs / Crossref DOI-Lookup | 14:41:04.401114 | 200 | Referenzmetadaten |
| 6 | matsuo_refs / Crossref DOI-Lookup | 14:41:04.904263 | 200 | Referenzmetadaten |
| 7 | gery_refs / Crossref DOI-Lookup | 14:41:05.275696 | 200 | Referenzmetadaten |
| 8 | grechez_refs / Crossref DOI-Lookup | 14:41:05.723948 | 200 | Referenzmetadaten |
| 9 | prior_tumor / Europe PMC | 14:42:21.157514 | 200 | hitCount 0, abgerufen 0 |
| 10 | prior_cycle / Europe PMC | 14:42:21.431364 | 200 | hitCount 0, abgerufen 0 |
| 11 | prior_quoted / Europe PMC | 14:43:22.869072 | 200 | hitCount 10, abgerufen 10 |
| 12 | anderson_fulltext / Europe PMC | 14:43:55.739368 | 200 | Identifizierter Originalvolltext, JATS-XML |

Die 403-Antworten belegen eine Blockade dieses Abrufpfads, nicht zwingend eine Paywall oder das weltweite Fehlen legaler Kopien. Es gab keine Weiterleitungen, Retries, Authentifizierung oder Cookie-/Browser-Wechsel. Drei bekannte HTTP-OA-URLs wurden vor dem Abruf auf HTTPS umgestellt. Keine Umgehung von Sperren.

Die beiden Nulltreffersuchen enthielten unquotierte DOI-Klammern. Nach einer dokumentierten Korrektur auf quotierte DOI-Werte ergab die gemeinsame Abfrage zehn Records. Das spricht für ein Suchsyntaxproblem; ein isolierter Syntaxvergleich wurde nicht durchgeführt. Die Korrektur verwendet einmalig `pageSize=20` statt 10, `resultType=core`, `format=json`, `cursorMark=*`, Relevanzsortierung des Dienstes und keine weiteren Filter. Alle zehn Treffer wurden gelesen; der nur bibliografisch identifizierte Jaffe und der nicht gefundene Barbason werden nicht zu gelesenen Abstracts umgedeutet. Es gab keine zweite Seite und keine breitere Ersatzsuche. Das sind lokale Abrufzahlen, keine globalen PRISMA-Zahlen.

Anderson wurde für den letzten Request gewählt, weil nur dieser Treffer ausdrücklich `isOpenAccess=Y` auswies. Bjarnason 1999/2001 und Hirayama 2005 haben zwar PMCIDs, aber `isOpenAccess=N` in der Antwort. PMCID allein garantiert keine abrufbare API-Volltextversion. Nach dem letzten GET endet die Recherche.

Offline-Verifikation aus dem Projektverzeichnis:

```sh
python3 text_mining/pilot_task1d/history/fulltext/test_fulltext.py
python3 text_mining/pilot_task1d/history/test_pilot.py
```

Der neue Test prüft das Zwölf-Request-Budget, URL-/UTC-Zuordnung, Rohdatenhashes, Suchparameter und Trefferzahlen, PMID/DOI des Volltexts, alle Zitatstellen, lokale Reportlinks sowie unveränderte Hashes der 21 vorbestehenden history-Artefakte. Der alte globale `pilot.py check` wird bewusst nicht benutzt: Änderungen parallel bearbeiteter Bereiche sind kein Fehler dieses Teilauftrags. [verification.json](fulltext/verification.json) hält die tatsächlichen Exitcodes und Ausgaben fest. Kein Test erzeugt Netzverkehr.

Der Abrufcode [retrieve.py](fulltext/retrieve.py) verwendet nur Python-Standardbibliotheken und akzeptiert `ID HTTPS_URL PURPOSE`. Auf dem gespeicherten Stand sind weitere Abrufe durch das Budget gesperrt. Die protokollierten Antworten erlauben die Offline-Prüfung; ein erneuter Netzlauf wäre ein neuer, gesondert zu autorisierender Rechercheauftrag.
