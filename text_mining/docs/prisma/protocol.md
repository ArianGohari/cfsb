# Projektprotokoll: circadiane Uhr und Krebs

Status: Entwurf vom 2026-09-16, noch nicht für den Hauptlauf eingefroren. Keine Registrierung dokumentiert. Dieses Protokoll beschreibt Aufgabe 1 mit Schwerpunkt auf der Literaturauswertung in (g); es ersetzt weder Modellvergleich noch Modellreproduktion.

## Forschungsfrage

Arbeitsfrage: Welche molekularen Beziehungen zwischen Komponenten der circadianen Uhr und Krebs-/Checkpoint-Regulation werden in der Literatur beschrieben, unter welchen experimentellen Bedingungen und mit welcher Art von Evidenz?

PER2, TP53/p53, MDM2 und CLOCK/BMAL1 sind Startbegriffe, keine abschließende Liste erlaubter Ergebnisse. Gen, Protein und Komplex dürfen nicht gleichgesetzt werden.

## Vor dem Hauptlauf festzulegen

- Review-Typ mit dem Professor: systematischer Review nach PRISMA 2020 oder kartierender Scoping Review nach PRISMA-ScR; PRISMA-S für die Suche ergänzen.
- Fachlicher Umfang, Suchzeitraum, Sprach- und Publikationstypbeschränkungen samt Begründung. Aktueller Vorschlag: englische Texte, Species nicht pauschal auf Menschen beschränken.
- Vollständige, getestete Suchstrings einschließlich Synonymen und Limits. Europe PMC ist als primäre Quelle vorgesehen; Quellenabdeckung begründen und bei Bedarf erweitern.
- Rolle der vorgegebenen Papers, Referenzsuche und Reviews. Alle ergänzenden Fundwege werden protokolliert.
- Validierte Prompt-/Modellversionen, Budgets, Auswahlregeln und Regeln für `unclear`.
- Verfahren zur Bewertung experimenteller Evidenz, Bias und gegebenenfalls Evidenzsicherheit. Noch offen; Extraktionsscores ersetzen es nicht.
- Goldstandard, Testsplit und Zielgrößen für Screening und Extraktion. Keine Mindestqualität ohne Messung behaupten.
- Wie Berichte derselben Studie zugeordnet werden und welche verbleibende Unsicherheit ausgewiesen wird.

Diese Entscheidungen sind Planungsarbeit vor dem Lauf. Sie führen nicht zu manuellen Haltepunkten für jedes Paper. Bis sie festgelegt sind, bleiben Läufe als Pilot/Exploration gekennzeichnet.

## Vorgeschlagene Kriterien

| ID | Kriterium | Anwendung |
|---|---|---|
| I1 | Molekulare Beziehung zwischen Uhrsystem und Krebs-/Checkpoint-Regulation | Voraussetzung für fachlichen Einschluss; bloße gemeinsame Erwähnung reicht nicht |
| I2 | Bericht erlaubt die Zuordnung einer relevanten Untersuchung oder eines Modells | Keine automatische Forderung nach einer bereits erfolgreich extrahierten Relation |
| E1 | Thema außerhalb des vereinbarten Umfangs | Fachlicher Ausschluss mit Beleg |
| E2 | Keine relevante molekulare Verbindung nach Beurteilung des verfügbaren Volltexts | Fachlicher Ausschluss; nicht aus einem leeren Extractor-Ergebnis ableiten |
| E3 | Publikationstyp außerhalb der vorab vereinbarten Primärsynthese | Reviews beispielsweise als Suchhilfe erhalten, aber nicht als Originalexperiment zählen |
| E4 | Sprache außerhalb des vorab vereinbarten Umfangs | Nur anwenden, wenn Sprachbeschränkung tatsächlich beschlossen wurde |

Die vorgeschlagene Primärsynthese umfasst experimentelle Originalarbeiten und mechanistische Modellarbeiten, getrennt nach Evidenzart. Reviews dienen zunächst der Orientierung und Referenzsuche. Diese Festlegung ist vor dem Hauptlauf zu bestätigen; Kriterien werden danach nur als begründete Protokolländerung angepasst, nicht durch das LLM.

Duplikat, fehlender Volltext, API-Ausfall, Budgetende und ungültige Modellantwort sind keine fachlichen Ausschlussgründe. Abstract-Unklarheit geht in die Beschaffung weiter. Nach Volltextprüfung unklare Berichte bleiben offen; sie werden weder automatisch eingeschlossen noch als Ausschluss versteckt.

## Suche und Auswahl

1. Pilot mit 20–50 nach dokumentierter Sortierung ausgewählten Papers für technische Tests und Promptentwicklung durchführen. Pilotdaten nicht als zurückgehaltene Qualitätsprüfung verwenden.
2. Protokoll, Queries, Kriterien und Prompts versionieren und für den Hauptlauf einfrieren.
3. Suchtreffer vor Deduplikation speichern. Quelltreffer auf kanonische Berichte abbilden, Fundwege erhalten.
4. Titel-/Abstract-Screening mit LLM durchführen. `include` bedeutet hier Weiterleitung zur Beschaffung, noch keinen endgültigen Review-Einschluss; `unclear` wird ebenfalls weitergeleitet.
5. Berichte beschaffen und Retrievalstatus getrennt von fachlicher Eignung erfassen. Abstract-Fallback kann explorative Extraktion ermöglichen, ersetzt aber keinen beschafften Volltext.
6. Einschlusskriterien am beschafften Volltext in einem eigenen LLM-Schritt prüfen und mit Textstand/Beleg protokollieren. Bei langen Texten alle relevanten Abschnitte nach dokumentierter Chunking-Strategie berücksichtigen; unvollständige Prüfung bleibt offen.
7. Nur endgültig eingeschlossene Berichte in die Primärsynthese übernehmen. Explorative Abstract-Ergebnisse bleiben separat und dürfen die Einschlusszahlen oder den primären Graphen nicht verändern.

LLM-Eignungsprüfung und Relationsextraktion sind getrennte Entscheidungen. Ein fachlich eingeschlossenes Paper ohne extrahierte Relation bleibt eingeschlossen und erscheint im Abdeckungsbericht.

## Datenerhebung und Synthese

Die [Pipeline-Dokumentation](../README.md) definiert die fünf Tabellen, mechanistischen Prädikate und Kontextfelder. Pro Evidence bleiben Dokument, Originaltext und maschinelle Interpretation nachvollziehbar. Fehlende Werte bleiben unbekannt, unsichere Normalisierung führt zur Enthaltung. Originalexperiment, Modellvorhersage und zitierte Aussage werden getrennt ausgewiesen.

Geplant sind Evidenztabellen und ein kontextgebundener Knowledge Graph, keine Meta-Analyse von Effektgrößen. Paperzahlen werden als Berichte gezählt; unabhängige Studien werden nur bei belegter Zuordnung ausgewiesen. Der Zusammenhang zwischen mehreren Berichten und einer Studie darf nicht aus gleichen Autoren oder einem ähnlichen Titel allein abgeleitet werden.

Modellvergleiche aus Aufgabe 1(b/e) und die Datenbankrecherche aus (f) werden im Projektbericht gesondert beschrieben. Wenn daraus weitere Literatur aufgenommen wird, muss deren Fundweg im selben Auswahlprotokoll erscheinen.

## Evaluation und Grenzen

Regelbaseline und LLM-Auswertung auf demselben eingefrorenen Testbestand vergleichen. Auch ausgeschlossene Treffer prüfen, um Screeningverluste zu messen. Papers beziehungsweise bekannte Studiengruppen nicht zwischen Promptentwicklung und Test aufteilen. Kosten, Enthaltungen und Ausfälle berichten.

Fachliche Qualitätsbewertung der Studien wird separat geplant und berichtet. Bei fehlender Evaluation ausdrücklich die Lücke nennen, keine PRISMA-Konformität oder Vollständigkeit aus einem korrekten Flussdiagramm ableiten. Quellen-, Sprach-, Zugriffs- und Automationsbias gehören in die Diskussion.

## Versionierung, Registrierung und Änderungen

Der Hauptlauf referenziert den Hash dieses Protokolls und seiner Kriterien. Öffentliche Zugänglichkeit und eventuelle Registrierung sind vor der Abgabe zu klären. Falls nicht registriert, wird das im Bericht ausdrücklich angegeben; eine Registrierung wird hier nicht behauptet.

| Datum | Stand | Änderung und Begründung |
|---|---|---|
| 2026-09-16 | Entwurf 1 | PRISMA-orientiertes Vorgehen ergänzt; getrennte Suchtreffer, Beschaffung und Volltext-Eignungsprüfung vorgesehen. Noch keine Auswertung erfolgt. |

Weitere Änderungen mit Datum, betroffenen Kriterien/Queries und Grund dokumentieren. Geänderte Entscheidungen erzeugen einen neuen Review-Stand; alte Ergebnisse werden nicht rückwirkend überschrieben.
