# API-Pilot für Aufgabe 1(d)

## Aktueller Abschlussstand der schriftlichen Antwort

Aufgabe 1(d) ist in [task1.qmd](../../part1/task1/task1.qmd) ergänzt. Die Recherche bleibt begrenzt; ein vollständiger systematischer Review und globale Erstprioritäten sind nicht belegt.

Die [historische Nachprüfung](history/fulltext_review.md) ergänzt ältere Beiträge und den Originalvolltext von Anderson 2000. Die [Folgeprüfung](followup/fulltext_review.md) enthält Dickmeis 2007 im Volltext. Der anschließend erfolgreiche öffentliche HTML-Abruf von Gaddameedhi 2012 ist im [vorrangigen Nachtrag](followup/html_addendum.md) dokumentiert.

Wichtige Korrektur gegenüber dem unten archivierten Abstract-Pilot: Gaddameedhi 2012 berichtet eine gezielte Nichtreproduktion funktioneller PER1-Strahlenantworten in denselben benannten humanen Krebszelllinien wie Gery 2006 (Abb. 8–9). Die Arbeit enthält zugleich einen positiven PER1/2-Knockdown-Befund zur UV-Apoptose in Mausfibroblasten (Abb. 7). Eine pauschale Nullwirkung oder vollständige Falsifikation folgt daraus nicht. Drei Originalhaupttexte sind nun geprüft; die übrigen Quellenebenen und Zugriffslücken sind in der QMD gekennzeichnet.

## Archivstand: erster Abstract-Pilot

Die folgenden Abschnitte dokumentieren den früheren Stand. Aussagen über fehlende Volltexte und die noch nicht ergänzte QMD gelten nur für diesen Zeitpunkt; die oben verlinkten Nachprüfungen haben Vorrang.

Stand: 20.09.2026. Zwei Subagents haben öffentliche APIs abgefragt: Europe PMC für bibliografische Daten und Abstracts, OpenAlex zusätzlich für Zitationsverbindungen. Die fünf vorhandenen Papers bleiben unverändert. Die QMD-Datei wurde nicht ergänzt, da dies zunächst eine explorative Recherche ist.

## Ergebnisse

| Teil | Ergebnis | Dokumentation |
|---|---|---|
| Historische Ausgangspunkte | Vier ausgewählte Originalarbeiten: Fu 2002, Matsuo 2003, Gery 2006, Gréchez-Cassiau 2008 (online 2007). Sechs Suchrecords gespeichert. | [Historischer Bericht](history/report.md), [Records](history/records.csv), [Manifest](history/manifest.json) |
| Spätere Untersuchungen | Sieben ausgewählte empirische Folgearbeiten; 142 Europe-PMC-Suchrecords, 99 eindeutige Berichte in diesem Teilbestand. | [Folgebericht](followup/report.md), [Records](followup/records.csv), [Manifest](followup/manifest.json) |

Die Teilbestände überschneiden sich und wurden nicht global dedupliziert. Ihre Zahlen dürfen nicht zu PRISMA-Gesamtzahlen addiert werden. Ausgewertet wurden Abstracts, keine Originalvolltexte. API-Abfragen, Rohantworten, Auswahl und inhaltliche Interpretation sind getrennt dokumentiert. Die Auswahl ist keine validierte automatische Screening-Pipeline.

## Was sich für 1(d) bereits abzeichnet

- [Fu et al. 2002](https://europepmc.org/article/MED/12372299) berichten erhöhte Tumorentwicklung nach Gammabestrahlung bei mPer2-defizienten Mäusen. Das ist ein identifizierter früher Befund, kein durch diesen Pilot nachgewiesener Erstbefund.
- [Matsuo et al. 2003](https://europepmc.org/article/MED/12934012) verbinden Uhrkontrolle mit wee1 und Mitose in regenerierender Mausleber. [Gréchez-Cassiau et al. 2008](https://europepmc.org/article/MED/18086663) untersuchen BMAL1, p21 und Hepatozytenproliferation. Diese Zellzyklusbefunde sind nicht automatisch Tumornachweise.
- [Gery et al. 2006](https://europepmc.org/article/MED/16678109) berichten PER1-Effekte auf DNA-Schadensapoptose in humanen Krebszellen. [Gery et al. 2007](https://europepmc.org/article/MED/17332281) stützen eine wachstumshemmende PER1-Funktion in Lungenkrebszellen, sind aber keine unabhängige Replikation der gesamten Schadenssignalkette.
- [Gauger et al. 2005](https://europepmc.org/article/MED/16061665), [Ozturk et al. 2009](https://europepmc.org/article/MED/19188586) und [Gaddameedhi et al. 2012](https://europepmc.org/article/MED/22918252) begrenzen die pauschale Aussage, Uhrgenverlust müsse stets Krebs oder eine gestörte DNA-Schadensantwort verursachen. Untersuchte Gene, p53-Hintergründe und Systeme unterscheiden sich. Diese Ergebnisse allein widerlegen deshalb nicht Fu 2002 oder Gery 2006.

## Grenzen und offene Prüfungen

Der Pilot umfasst begrenzte erste Ergebnisseiten und gezielte Nachsuchen. Ein anfänglich ungeeigneter Suchfilter im historischen Teil sowie unzuverlässige Seed-Suchen und eine nicht gesicherte Sortierung im Folgeteil sind dokumentiert. Die Auswahl darf nicht als vollständige historische Suche dargestellt werden.

OpenAlex lieferte außerdem eine chronologisch unplausible Zitationskante von Gauger 2005 zu Gery 2006. Sie bleibt als Metadatenkonflikt markiert und wird nicht als verifiziertes Zitat verwendet. Eine Zitationskante beweist ohnehin keine Replikation.

Nächster fachlicher Schritt: Originalvolltexte der historischen Arbeiten und ausgewählten Folgearbeiten beschaffen und Allele, Zellmodelle, Stressbedingungen und Endpunkte vergleichen. Erst danach lassen sich belastbare Aussagen zu Reproduktion oder Widerlegung formulieren. Historische Priorität benötigt zusätzlich eine breitere Rückwärtssuche. Die beiden Berichte enthalten die jeweiligen Lücken und wörtlichen Abstract-Belege.

## Verifikation

Vom Projektverzeichnis aus wurden nach Abschluss beider Teilaufgaben ausgeführt:

```sh
python3 text_mining/pilot_task1d/history/test_pilot.py
python3 text_mining/pilot_task1d/followup/validate.py
```

Beide bestanden, gemeinsamer Shell-Exitcode 0. Geprüft wurden unter anderem Fehlerpfade und Überschreibschutz im historischen Teil sowie Rohdatenhashes, Identifier, Belegzitate und Deduplikation im Folgeteil. Diese Prüfungen bestätigen keine biologische Interpretation.

Die zusätzliche globale Baseline-Prüfung `history/pilot.py check` meldete nach Anlage des Folgeteils Exitcode 1: Sie zählt dessen neu angelegte Dateien als Änderungen außerhalb von `history/`. Laut Teilbericht blieben vorbestehende Dateien unverändert. Diese bereichsübergreifende Prüfung ist daher nicht als bestanden ausgewiesen; die bereichsspezifischen Prüfungen oben bestanden. Kein abschließender PRISMA-Hauptlauf und keine QMD-Ergebnisübernahme durchgeführt.
