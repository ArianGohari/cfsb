# PRISMA im Projekt

Stand: 2026-09-16. Diese Dokumentation beschreibt das geplante Vorgehen, keinen bereits durchgeführten Review. Die Pipeline ist noch nicht implementiert. Sie unterstützt Aufgabe 1(g); die PRISMA-Berichterstattung betrifft das gesamte Projekt und seine Literaturauswertung.

## Was PRISMA leistet

PRISMA ist eine Reporting-Leitlinie für systematische Reviews. Sie macht Forschungsfrage, Suche, Auswahl, Datenerhebung, Synthese und Grenzen nachvollziehbar. Sie ist weder ein Workflow-Framework noch ein Qualitätssiegel. Ein Flussdiagramm allein belegt keine PRISMA-konforme Berichterstattung.

Als Arbeitsgrundlage dienen PRISMA 2020 und PRISMA-S für die Literatursuche. Wenn das Projekt vor allem Mechanismen und Forschungslücken kartiert, könnte PRISMA-ScR besser passen. Der Review-Typ ist vor dem Hauptlauf mit dem Professor festzulegen; wir behaupten derzeit weder eine abgeschlossene Checkliste noch Konformität.

- [Projektprotokoll](protocol.md): Forschungsfrage, vorgeschlagener Suchrahmen, Kriterien, offene Entscheidungen und Änderungen.
- [Tracking und Zählregeln](tracking.md): Suchtreffer, phasenbezogene Entscheidungen und Ableitung der PRISMA-Zahlen.
- [Pipeline-Entwurf](../README.md): Extraktion, Datenmodell, LLM-Provenance und Graph-Build.

## Bezug zur Checkliste

Die Zuordnung unten ist eine Planungshilfe, keine vollständig ausgefüllte Checkliste. Im Abschlussbericht erhält jedes anwendbare Item eine konkrete Fundstelle. Nicht durchgeführte Verfahren werden als solche angegeben; tatsächlich nicht anwendbare Items werden begründet, nicht still weggelassen.

| PRISMA-2020-Items | Geplanter Nachweis | Stand |
|---|---|---|
| 1–4: Titel, Abstract, Begründung, Frage | Projektbericht und Protokoll | Frage als Entwurf; Bericht offen |
| 5–7: Kriterien, Quellen, Suchstrategien | Protokoll, Suchmanifest mit vollständigen Queries und Limits | Kriterien vorgeschlagen; Queries offen |
| 8: Auswahl | Phasenprotokoll, LLM-/Promptstand, dokumentierte Zahl menschlicher Prüfender | Vollautomatischer Hauptlauf geplant |
| 9–10: Datenerhebung und Variablen | Pipeline-Schema, Belegstellen, Regeln für fehlende Angaben | Entwurf vorhanden |
| 11, 14–15: Bias und Evidenzsicherheit | Begründete Auswahl eines geeigneten Bewertungsverfahrens | Noch nicht festgelegt |
| 12–13: Effektmaße und Synthese | Geplante kontextbezogene Evidenztabellen/Graphen; quantitative Synthese nur bei passender Frage und Daten | Keine Meta-Analyse geplant |
| 16–17: Auswahlresultate und Studienmerkmale | Flussdiagramm, Ausschlussliste, eingeschlossene Berichte und Studienzuordnung | Noch keine Ergebnisse |
| 18–22: Bias, Einzelergebnisse und Synthesen | Ergebnisbericht entsprechend tatsächlich durchgeführter Bewertung/Synthese | Offen |
| 23: Diskussion | Grenzen von Suchraum, Quellen, Automation und biologischer Evidenz | Im Abschlussbericht |
| 24: Registrierung und Protokoll | Zugängliches, datiertes Protokoll, Registrierungsstatus, Änderungsnachweise | Entwurf; keine Registrierung dokumentiert |
| 25–27: Unterstützung, Interessen, Verfügbarkeit | Projektbericht, Code-/Datenverweise und Lizenzgrenzen | Offen |

PRISMA-S ergänzt die Suchdokumentation: Plattform und Datenquelle, genaue Strategien je Quelle, Suchdatum, Limits, ergänzende Suchwege, Trefferzahlen und Deduplikation dokumentieren. Europe PMC allein kann eine begrenzte Projektwahl sein; ihre ausreichende Abdeckung darf nicht vorausgesetzt werden. Die Quellenwahl und ihre Grenzen müssen begründet werden.

## Automation und wissenschaftliche Bewertung

PRISMA 2020 verlangt in Items 8 und 9 Angaben zum Auswahl- und Datenerhebungsprozess einschließlich Automatisierung. Unser Hauptlauf verwendet LLMs statt menschlicher Einzelfallentscheidungen. Deshalb werden Modell, Prompt, Kriterien, Input, Output, Fehler und Enthaltungen gespeichert. Falls tatsächlich keine Menschen screenen, wird das mit null menschlichen Screening-Reviewern angegeben; ein zweites LLM zählt nicht als menschlicher Reviewer.

Drei Ebenen bleiben getrennt:

1. Technische QC: Sind IDs, Zitate und Offsets gültig?
2. Extraktionsqualität: Versteht das Modell Argumente, Mechanismus und Kontext richtig?
3. Wissenschaftliche Evidenzqualität: Wie belastbar sind Versuchsdesign und berichtete Ergebnisse?

`auto_pass` beantwortet nur die festgelegten automatischen Prüfungen. Es ist kein Risk-of-Bias-Urteil und keine Evidenzsicherheitsbewertung. Eine unabhängige Testmenge kann außerhalb des unbeaufsichtigten Laufs erstellt werden. Ohne sie bleibt fachliche Qualität ausdrücklich nicht evaluiert. Ob das für die Projektanforderungen genügt, ist vor der finalen Auswertung zu klären.

## Zwei Dokumentationssichten, kein neuer biologischer Graph

Die fünf Parquet-Tabellen und die zwei Architekturdiagramme bleiben erhalten. PRISMA-Protokolle liegen außerhalb der Graphdatenbank. Das offizielle PRISMA-Flussdiagramm wird später als Ergebnisartefakt pro Review-Lauf aus echten Zählwerten erzeugt, nicht als drittes Architekturdiagramm mit erfundenen Zahlen.

Das Flussdiagramm muss zur tatsächlichen Suche passen. Bei Nutzung der vorgegebenen Papers oder zusätzlicher Referenzsuche neben Datenbanksuchen wird die Vorlage für Datenbanken/Register und weitere Quellen geprüft. Quellen dürfen nicht doppelt als eingeschlossene Berichte gezählt werden.

## Offizielle Quellen

Die folgenden Quellen wurden am 2026-09-16 eingesehen. Die Beschreibungen hier sind projektbezogene Zusammenfassungen; maßgeblich bleiben die Originalunterlagen.

- [PRISMA 2020](https://www.prisma-statement.org/prisma-2020)
- [Checkliste und erweiterte Checkliste](https://www.prisma-statement.org/prisma-2020-checklist)
- [Offizielle Flussdiagramme](https://www.prisma-statement.org/prisma-2020-flow-diagram)
- [PRISMA-S: Dokumentation der Literatursuche](https://www.prisma-statement.org/prisma-search)
- [PRISMA-ScR: Scoping Reviews](https://www.prisma-statement.org/scoping)

Bei Verwendung oder Anpassung offizieller Checklisten/Diagramme ist die Originalquelle zu zitieren; die PRISMA-2020-Vorlagen werden unter CC BY 4.0 bereitgestellt.
