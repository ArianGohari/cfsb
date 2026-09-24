# Auditindex zu Aufgabe 1

Dieser Index fasst die technischen Begleitprüfungen zusammen, deren Originaldateien außerhalb des Quarto-Buchs im Projektordner `text_mining/` liegen.

## Literaturgeschichte {#literaturgeschichte}

Die begrenzte historische Recherche zu PER1, PER2 und Krebs ist unter `text_mining/pilot_task1d/` archiviert. Sie enthält das Suchprotokoll, die Volltextprüfung der historischen Quellen und eine gesonderte Gegenprüfung der PER1-Aussagen. Die Recherche ist keine vollständige systematische Review.

## Pathway- und Modellprüfung {#pathways}

Die BioModels-Prüfung liegt unter `text_mining/pilot_task1f/biomodels/`, die KEGG- und ConsensusPathDB-Prüfung unter `text_mining/pilot_task1f/pathways/`. Die Archive enthalten Abfrage-URLs, Rohantworten, Zeitpunkte und Offline-Prüfungen. Die Datenbankauswertung belegt getrennte dynamische Teilmodelle und einzelne Interaktionsannotationen, aber kein vollständig parametrisiertes Kopplungsmodell.

## Text-Mining-Lauf {#text-mining}

Der vollständige technische Lauf liegt unter `text_mining/data/runs/task1-full-20260921-complete/`. Er verarbeitete 5.986 Suchtreffer plus sechs Pflichtpublikationen. Nach der Bereinigung blieben 5.858 Papers; 2.033 Volltexte waren über den unterstützten Weg verfügbar. Alle Screeningentscheidungen blieben `unclear`, sodass Annotation und Relationsextraktion nicht erreicht wurden. Der leere Graph ist deshalb kein biologisches Nullergebnis.

Die Originaldateien `ERGEBNIS.md` und `verification.json` dokumentieren den Lauf. Die Verifikation prüfte unter anderem 19.956 Dateihashes, PRISMA-Kontrollidentitäten, Tabellenzeilen, SVG-Struktur und Knotenzahlen. Der technische Lauf ist abgeschlossen; die wissenschaftliche Auswertung bleibt als `incomplete` gekennzeichnet.
