# API-Pilot zu Aufgabe 1(d): historische Primärarbeiten

Stand: 20.09.2026 (UTC). Vier Zielarbeiten identifiziert; ausgewertet wurden ihre tatsächlich gelesenen Abstracts aus der öffentlichen Europe-PMC-API. Kein Volltext wurde abgerufen. Dies ist ein begrenzter explorativer Referenzpilot, kein vollständiger historischer Review und kein globaler PRISMA-Lauf.

## Auftrag und lokale Ausgangsquellen

Gelesen wurden [project.md, Aufgabe 1(d)](../../../project.md), [protocol.md](../../docs/prisma/protocol.md), [tracking.md](../../docs/prisma/tracking.md), das [Quelleninventar](../../../part1/task1/sources/sources.csv) mit seinen README-Dateien sowie die relevanten Passagen und Literaturangaben im [lokalen Zou-Markdown](../../../part1/task1/sources/markdown/zou_2020_circadian_cell_cycle_checkpoints/zou_2020_circadian_cell_cycle_checkpoints.md).

Zou nennt Matsuo (Zeilen 49/177), Gery (51/153) und Gréchez-Cassiau (49/157). Diese Referenzen dienen als Fundweg, nicht als Ersatz für die Originalabstracts. Für Fu 2002 wurde im lokalen Zou-Markdown kein entsprechender Eintrag gefunden; der Kandidat stammt aus dem assistentenseitig formulierten Rechercheplan/Delegationsauftrag, nicht vom Nutzer. Das Inventar enthält die vier hier gesuchten Arbeiten noch nicht.

Provenienzkorrektur: Diese Herkunftsangabe berichtigt auch die Fu-`seed`-Felder in `plan.json` und `manifest.json` sowie deren Fassungen unter `attempt1/`. Die beim Abruf eingefrorenen Dateien bleiben zur Erhaltung der ursprünglichen Hashes unverändert; ihre Formulierung "Suchkandidat aus Nutzerauftrag" ist damit ausdrücklich korrigiert. `evidence.json` und die daraus erzeugte `records.csv` enthalten die präzisierte Herkunft. API-Rohantworten und Suchparameter bleiben unverändert.

Das Projektprotokoll ist ein Entwurf. Sein Vorschlag eines 20–50-Paper-Piloten für technische Tests und Promptentwicklung wird hier nicht umgesetzt: Der konkrete Auftrag ist ein kleiner Referenzpilot für vier historische Arbeiten. Abstractbefunde bleiben gemäß Protokoll außerhalb der Primärsynthese. Weder Tracking noch Inventar oder biologische Graphen wurden geändert.

## Suchplan und tatsächliche Abrufe

[plan.json](plan.json) enthält die vorab festgelegten Parameter; [manifest.json](manifest.json) enthält die vor dem ersten Request geschriebenen URLs, anschließend UTC-Zeitpunkte, HTTP-Status, Response-Header, Trefferzahlen und Rohdatenhashes. Das Skript verwendet nur Python-Standardbibliotheken. Keine Keys, kein OpenAlex, keine Verlagsdownloads und keine Umgehung von Zugangssperren.

Endpoint: `https://www.ebi.ac.uk/europepmc/webservices/rest/search`. Jeweils GET, `format=json`, `resultType=core`, `pageSize=10`, `cursorMark=*`; Standardsortierung des Dienstes (Relevanz), eine Seite pro Query. Keine Sprach-, Species-, Publikationstyp- oder OA-Beschränkung. Kein Datumsfilter für die drei DOI-Abfragen; Fu ist auf `FIRST_PDATE` im Kalenderjahr 2002 begrenzt. Socket-Timeout 30 Sekunden, keine automatischen Retries. DOI-Suchen prüfen bekannte Referenzen und messen keine Suchsensitivität.

### Erster Versuch und dokumentierte Korrektur

Der erste Versuch vom 20.09.2026, 13:59:50.258043 bis 13:59:51.213328 UTC, enthielt in allen Queries `AND SOURCE:MED`. Die drei DOI-Queries entsprachen sonst den untenstehenden. Die Fu-Query war `AUTH_LAST:Fu AND FIRST_PDATE:[2002-01-01 TO 2002-12-31] AND (period2 OR per2) AND SOURCE:MED`.

Alle vier Antworten waren HTTP 200 mit `hitCount=0` und null abgerufenen Records. Das sind keine belastbaren negativen Literaturbefunde. Der Quellenfeldname `SOURCE` war als Syntaxfehler verdächtig (Europe PMC verwendet `SRC`). Der erste Plan, das Skript, sämtliche Responses und das Manifest bleiben unverändert in [attempt1/](attempt1/).

Die [vorab dokumentierte Änderung](amendment.json) entfernt den Quellenfilter und verwendet bei Fu außerdem Freitext `Fu` statt `AUTH_LAST:Fu`. Welcher Anteil des Fu-Ergebnisses auf welche Änderung entfällt, wurde nicht isoliert getestet. Das Gesamtbudget wurde einmalig auf acht Requests begrenzt. Es folgten keine weiteren Suchen.

### Korrigierter Versuch

Alle folgenden Zeiten sind Requestbeginn am 20.09.2026 in UTC; genaue Endzeitpunkte stehen im Manifest. Alle sechs gelieferten Records stammen laut Antwort aus `MED`.

| search_id | Vollständiger Suchstring | UTC | HTTP | hitCount | Abgerufen |
|---|---|---|---|---:|---:|
| matsuo2003 | `DOI:10.1126/science.1086271` | 14:00:29.122574 | 200 | 1 | 1 |
| gery2006 | `DOI:10.1016/j.molcel.2006.03.038` | 14:00:29.486586 | 200 | 1 | 1 |
| grechez2008 | `DOI:10.1074/jbc.M705576200` | 14:00:29.660594 | 200 | 1 | 1 |
| fu2002 | `Fu AND FIRST_PDATE:[2002-01-01 TO 2002-12-31] AND (period2 OR per2)` | 14:00:29.822698 | 200 | 3 | 3 |

Ende: 14:00:30.069519 UTC. Die gemeldeten Treffer dieser konkreten Queries wurden vollständig gespeichert; daraus folgt keine Vollständigkeit der historischen Literatur. Alle acht HTTP-Requests waren erfolgreich, keine Netzfehler oder HTTP-Fehler beobachtet. Der erste Versuch war ein Suchproblem bei formal erfolgreichem Abruf.

[records.csv](records.csv) enthält alle sechs Records vor Deduplikation, einschließlich der zwei nicht ausgewählten Fu-Suchtreffer. Die stabilen IDs sind `search_id:Position`; `paper_id` ist `source:id`. Deduplikation v1: gleiche `source:id`, erste Fundstelle in Planreihenfolge bleibt; hier keine Duplikate. Keine Zuordnung zu unabhängigen Studien. Die Zahlen gelten ausschließlich für diesen Pilot, nicht für den Projektbestand.

## Historische Befunde aus gelesenen Originalabstracts

Die vier Texte beschreiben eigene Experimente; die API führt jeweils `Journal Article`, nicht `Review`. Die Einstufung als Originalarbeit beruht zusätzlich auf den experimentellen Aussagen im Abstract. Finkielstein ist in keiner der vier vollständigen API-Autorenlisten enthalten; auch die angegebenen Erstautorenaffiliationen liegen außerhalb ihres Labors. Eine vollständige personelle oder institutionelle Unabhängigkeitsanalyse wurde nicht durchgeführt.

### Fu et al. (2002): mPer2 und Tumorsuppression im Mausmodell

Loning Fu, Helene Pelicano, Jinsong Liu, Peng Huang, Cheng Lee. *The circadian gene Period2 plays an important role in tumor suppression and DNA damage response in vivo.* Cell (2002). [DOI 10.1016/s0092-8674(02)00961-3](https://doi.org/10.1016/s0092-8674(02)00961-3), [PMID 12372299](https://europepmc.org/article/MED/12372299).

Die Identität des Suchkandidaten ist anhand Autor, Titel, Jahr und PER2-/Tumorinhalt bestätigt. Quellenebene: Originalabstract, Feld `abstractText` in [raw/fu2002.json](raw/fu2002.json), Record `MED:12372299`.

> "We report here that mice deficient in the mPer2 gene are cancer prone."

> "After gamma radiation, these mice show a marked increase in tumor development and reduced apoptosis in thymocytes."

Fu et al. berichten erhöhte Tumorentwicklung nach Gammabestrahlung bei mPer2-defizienten Mäusen sowie reduzierte Thymozytenapoptose. Der Abstract beschreibt außerdem deregulierte zeitliche Expression von Cyclin D1, Cyclin A, Mdm-2 und Gadd45alpha sowie c-myc-Regulation durch circadiane Regulatoren. Das ist ein früher, konkret identifizierter Bericht zur Tumorsuppressionshypothese im Mausmodell. Es ist kein hier nachgewiesener Erstbefund und keine allgemeingültige Aussage über PER2 bei menschlichen Tumoren. Allel, Strahlendosis, Stichprobengrößen und Effektgrößen wurden nicht aus einem Volltext geprüft.

### Matsuo et al. (2003): circadiane Kontrolle von wee1 und Mitose

Takuya Matsuo, Shun Yamaguchi, Shigeru Mitsui, Aki Emi, Fukuko Shimoda, Hitoshi Okamura. *Control mechanism of the circadian clock for timing of cell division in vivo.* Science (2003). [DOI 10.1126/science.1086271](https://doi.org/10.1126/science.1086271), [PMID 12934012](https://europepmc.org/article/MED/12934012).

Quellenebene: Originalabstract, `abstractText` in [raw/matsuo2003.json](raw/matsuo2003.json).

> "Here, we show in the regenerating liver (of mice) that the circadian clock controls the expression of cell cycle-related genes that in turn modulate the expression of active Cyclin B1-Cdc2 kinase, a key regulator of mitosis."

> "Among these genes, expression of wee1 was directly regulated by the molecular components of the circadian clockwork."

Der experimentelle Kontext ist regenerierende Mausleber, ergänzt durch Einzelzellbeobachtungen zur Unabhängigkeit der Uhr vom Zellzyklus. Die Uhr–wee1-Verbindung und die mitoserelevante Cyclin-B1-Cdc2-Aktivität sind im Abstract beschrieben; ein Tumorendpunkt ist dort nicht ausgewiesen.

Die spezifische Zuordnung CLOCK:BMAL1 → Wee1 steht im gelesenen Zou-Markdown (Zeile 49), aber nicht ausdrücklich im Matsuo-Abstract. Sie bleibt hier sekundär belegt. Auch Zous Aussage zu cry1-defizienten Mäusen wurde nicht am Originalvolltext geprüft. Aus der im Abstract beschriebenen unidirektionalen Kontrolle folgt keine universelle Unidirektionalität in anderen Zellkontexten.

### Gery et al. (2006): Per1 und DNA-Schadensantwort

Sigal Gery, Naoki Komatsu, Lilit Baldjyan, Andrew Yu, Danielle Koo, H. Phillip Koeffler. *The circadian gene per1 plays an important role in cell growth and DNA damage control in human cancer cells.* Molecular Cell (2006). [DOI 10.1016/j.molcel.2006.03.038](https://doi.org/10.1016/j.molcel.2006.03.038), [PMID 16678109](https://europepmc.org/article/MED/16678109).

Quellenebene: Originalabstract, `abstractText` in [raw/gery2006.json](raw/gery2006.json).

> "Overexpression of Per1 sensitized human cancer cells to DNA damage-induced apoptosis; in contrast, inhibition of Per1 in similarly treated cells blunted apoptosis."

> "In addition, Per1 interacted with the checkpoint proteins ATM and Chk2."

Gery et al. untersuchten humane Krebszellen mit erhöhter bzw. gehemmter Per1-Expression und DNA-Schädigung. Der Abstract berichtet auch Wachstumsreduktion nach ektopischer Expression in Zelllinien und reduzierte Per1-Level in Patientenproben. Zellliniennamen und Schadensprotokoll fehlen im Abstract. Die genannte Interaktion ist kein ausreichender Beleg für direkte molekulare Bindung. Zous genauere Beschreibung als Koimmunpräzipitation bleibt eine sekundäre Methodenangabe.

### Gréchez-Cassiau et al. (2008): BMAL1, p21 und Hepatozytenproliferation

Aline Gréchez-Cassiau, Béatrice Rayet, Fabienne Guillaumond, Michèle Teboul, Franck Delaunay. *The circadian clock component BMAL1 is a critical regulator of p21WAF1/CIP1 expression and hepatocyte proliferation.* Journal of Biological Chemistry (2008). [DOI 10.1074/jbc.m705576200](https://doi.org/10.1074/jbc.m705576200), [PMID 18086663](https://europepmc.org/article/MED/18086663).

Das Ausgabejahr ist 2008; die API nennt als Erstpublikation den 17.12.2007. Beide Angaben bleiben in der CSV erhalten. Groß-/Kleinschreibung der DOI unterscheidet sich zwischen Zou und API, bezeichnet aber denselben Identifier.

Quellenebene: Originalabstract, `abstractText` in [raw/grechez2008.json](raw/grechez2008.json).

> "p21WAF1/CIP1 circadian expression is dramatically increased and no longer rhythmic in clock-deficient Bmal1-/- knock-out mice."

> "This phenotype could be reversed using small interfering RNA-mediated knockdown of p21WAF1/CIP1."

Der zweite Beleg bezieht sich auf die unmittelbar zuvor beschriebene verminderte Proliferation p21-überexprimierender Bmal1-/- Primärhepatozyten. Weitere Kontexte sind periphere Mausorgane und serumgeschockte differenzierte Skelettmuskelzellen. Der Abstract ordnet die p21-Transkriptionsrhythmik antagonistischen REV-ERBalpha/beta- und RORalpha4/gamma-Aktivitäten zu. Eine direkte BMAL1-Bindung am p21-Promotor lässt sich daraus nicht ableiten. Die siRNA-Umkehr ist ein Experiment innerhalb dieser Arbeit, keine unabhängige Replikation. Ein Tumorendpunkt wird nicht beschrieben.

## Weitere Records und offene Teile von 1(d)

[Shigeyoshi et al. (2002), PMID 11895480](https://europepmc.org/article/MED/11895480), DOI 10.1046/j.1356-9597.2001.00503.x, hat Weili Fu als Koautor und untersucht laut gelesenem Abstract die Wiederherstellung von Verhaltensrhythmen in period-null-Drosophila durch murine Period-Homologe. Diese Arbeit ist nicht die gesuchte Tumorarbeit von Loning Fu.

[PMID 12051200](https://europepmc.org/article/MED/12051200) ist laut Titel und API-Publikationstyp eine Kongressabstract-Sammlung zu Chemotherapie und Infektionen. Die Antwort enthält weder DOI noch Autorenliste oder Abstract. Eine mögliche Volltextverfügbarkeit wurde nicht genutzt. Der Datensatz bleibt als nicht ausgewählter Suchtreffer erhalten; daraus wird kein fachlicher Volltextausschluss abgeleitet.

Der Pilot belegt die Existenz und Abstractaussagen der vier Zielarbeiten. Er beantwortet die Prioritäts- und Replikationsfragen aus 1(d) noch nicht. Die Auswahl beginnt mit vorgegebenen Referenzen und deckt weder mögliche ältere Arbeiten noch spätere Bestätigungen oder Gegenbefunde systematisch ab. Zitate in Zou, ähnliche Titel oder unterschiedliche Autoren reichen nicht für eine Prioritäts-, Replikations- oder Falsifikationsbehauptung. Für alle vier Arbeiten bleiben diese Bewertungen `not_assessed`.

Ein anschließender, separat geplanter Lauf müsste ältere Kandidaten sowie spätere methodisch vergleichbare Arbeiten suchen und deren Volltexte nach Spezies, Allel, Zelltyp, Perturbation und Endpunkt vergleichen. Fehlender Volltextzugriff ist kein fachlicher Ausschluss. `isOpenAccess=N` und fehlende PMCIDs in diesen vier API-Records beweisen auch nicht, dass überhaupt keine legal zugänglichen Volltexte existieren.

## Reproduktion und Prüfung

Python 3.11 oder neuer genügt. Aus dem Projektverzeichnis:

```sh
python3 text_mining/pilot_task1d/history/pilot.py export
python3 text_mining/pilot_task1d/history/pilot.py check
python3 text_mining/pilot_task1d/history/test_pilot.py
```

`export` rekonstruiert die CSV offline aus Rohantworten und der transparenten manuellen Auswertung in [evidence.json](evidence.json). `check` prüft Plan-/Skript-/Rohdatenhashes, Requests, UTC-Reihenfolge, Trefferzahlen, Limits, CSV-Gleichheit und wörtliche Abstractzitate. Außerdem vergleicht es SHA-256 und Dateimenge außerhalb `history/` mit [workspace_before.json](workspace_before.json): alle 89 vorbestehenden Dateien müssen unverändert sein. Git steht in diesem Arbeitsbereich nicht zur Verfügung.

Die Abrufbefehle waren in beiden dokumentierten Versuchen:

```sh
python3 text_mining/pilot_task1d/history/pilot.py fetch
```

Beide Abrufe endeten mit Exitcode 0. Vor dem zweiten Versuch wurden die ersten Artefakte nach `attempt1/` archiviert und der Suchplan dokumentiert korrigiert. `fetch` verweigert einen erneuten Lauf bei vorhandenem `raw/`, um die archivierten Antworten nicht zu überschreiben. Für einen ausdrücklich gewünschten späteren Netzlauf zuerst Skript und Plan in ein neues Unterverzeichnis innerhalb `history/` kopieren und dort `fetch` ausführen. API-Daten können sich verändern; bitgenau reproduzierbar ist die Offline-Auswertung des gespeicherten Stands.

Prüfergebnis: Alle drei oben genannten Offline-Befehle bestanden mit Exitcode 0. Export: sechs Records. Integritätscheck: vier Zielarbeiten, korrekte Zitate und unveränderte 89 Ausgangsdateien; keine neuen Dateien außerhalb `history/`. Der Test prüft zusätzlich Syntax, Seitenlimit, Leertreffer, simulierte Netzwerk- und HTTP-Fehler, fehlende Retries, Überschreibschutz, das Archiv des Erstversuchs und lokale Reportlinks. Die simulierten Fehler sind keine tatsächlich beobachteten Abruffehler. Exakte Befehle, UTC-Zeitpunkte, Exitcodes und Ausgaben stehen in [verification.json](verification.json).
