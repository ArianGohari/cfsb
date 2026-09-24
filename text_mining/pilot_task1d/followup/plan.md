# Suchplan vor API-Abruf

Begrenzter, unabhängiger Pilot zu Aufgabe 1(d), 2026-09-20. Grundlage: project.md, protocol.md und tracking.md, jeweils lokal gelesen. Keine Änderung am Hauptprotokoll, keine abschließende systematische Suche. Historische Priorität bleibt offen.

1. Europe PMC: drei Seed-Suchen nach Autor, Jahr und Mechanismus (Fu 2002 PER2, Matsuo 2003 Zellzyklus, Gery 2006 PER1), jeweils höchstens fünf Treffer, resultType=core. Titel, Autor, Jahr und DOI/PMID gegen Kandidaten prüfen.
2. OpenAlex: Seeds anhand bestätigter DOI auflösen; je Seed eine Seite zitierender Arbeiten, höchstens 25 Treffer, Publikationsdatum aufsteigend. Eine Zitationskante belegt keine Replikation. Bei HTTP-/Netzwerkfehlern keine Keys suchen und keine Wiederholschleife; Fehlerantwort sichern. Europe PMC bietet dann öffentliche bibliografische/Abstract-Evidenz, ersetzt aber keine OpenAlex-Kante.
3. Danach sechs gezielte Europe-PMC-Suchen (2004 bis 2026-09-20), je höchstens 20 Treffer, Relevanzsortierung des Dienstes: PER2/Tumorsuppression; PER1/DNA-Schaden; WEE1/Uhr/Zellzyklus; Uhrgenverlust/Tumorresistenz; cryptochrome/p53/Krebs; Period-Verlust/Krebs. Empirische Folgearbeiten nach thematischer Passung und unterschiedlichen Kontexten auswählen, nicht nach Bestätigungsrichtung. Reviews nur Suchhilfe. Ziel 4–8 Berichte, keine Studienzahl.
4. Höchstens acht ergänzende gezielte Europe-PMC-Abfragen zur Identitäts-/Abstractklärung, je fünf Treffer. Optional maximal acht OpenAlex-DOI-Abfragen, um Referenzlisten ausgewählter Berichte auf Seed-Kanten zu prüfen; bei genereller Sperre auslassen.

Maximal 39 HTTP-Anfragen: 3 Seed + 3 OpenAlex-Auflösungen + 3 Zitationsseiten + 6 thematische + 8 Klärungen + 8 Kantenprüfungen. Keine Pagination, keine automatischen Retries, Timeout 35 Sekunden pro Anfrage. Keine Sprach-/Speciesfilter, keine Volltextpflicht, keine Volltextdownloads in diesem Abstract-Piloten. Spätere Treffer nach dem Stichtag nicht vorgesehen. Begrenzungen sind technische Auswahlgrenzen, keine fachlichen Ausschlüsse.

Rohantworten unverändert speichern; Manifest mit exakter URL/Query, UTC, HTTP-Status, Trefferzahl, abgerufenem Umfang und Abschlussstatus. records.csv enthält alle abgerufenen Europe-PMC-Suchrecords vor Deduplikation, deterministisch erste PMID (sonst DOI, sonst Quell-ID) behalten. Ausgewählte Ergebnisse erhalten Kontext, kurze wörtliche Abstract-Belege und Links. Nicht ausgewertete Records bleiben not_processed. Manuelle Extraktion im Bericht, keine Biasbewertung oder abschließende Volltexteignung. Keine Übernahme in den primären Graphen.

Reproduzierbarkeit: Python-Standardbibliothek; gespeicherte Antworten offline erneut auswertbar. Live-Neulauf nur explizit, um den eingefrorenen Abruf nicht zu überschreiben.
