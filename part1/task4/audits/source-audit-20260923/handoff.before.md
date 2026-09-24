# Übergabe: CFSB-Projekt

Stand: 22.09.2026. Diese Datei dokumentiert den bisherigen Arbeitsstand; vor der Fortsetzung aktuelle Dateien und Prozesse prüfen. Historische Prüfergebnisse sind keine erneute Prüfung des aktuellen Codes.

## Projekt und Arbeitsweise

Workspace: `/Users/arian/Projects/uni/ss26/cfsb/project`

Aufgabenblatt: `project.md`. Dieses ist die maßgebliche Aufgabenquelle.

Der Nutzer möchte Deutsch, kleine nachvollziehbare Schritte, möglichst einfache reproduzierbare Lösungen und Subagents für abgegrenzte Aufgaben. Für Literaturarbeit verlangt der Professor PRISMA.

- Text-Mining-Pipeline ausdrücklich ohne generatives LLM betreiben. PubTator als externer Annotationsdienst wurde bisher verwendet, per PMID-Abfrage ohne Upload lokaler Volltexte.
- Subagent-verfasste Literaturbewertungen und Referenzannotationen als maschinell/LLM-unterstützt kennzeichnen, nicht als menschlichen Goldstandard.
- Bestehende Rohdaten und archivierte Runs nicht überschreiben. Änderungen benötigen neue Run-Verzeichnisse.
- Technischen Erfolg, biologische Evidenz und wissenschaftliche Validierung getrennt behandeln.
- Keine eigenen biologischen Simulationen wurden bisher durchgeführt.
- Nach bisherigem Stand kein Git-Repository; vor Änderungen erneut prüfen.

## Task 1: Circadiane Uhr und Krebs

Ausarbeitung: `part1/task1/task1.qmd`, Teilaufgaben a–f vorhanden.

Thema: PER2, p53/TP53, MDM2, circadiane Uhr und Checkpoint-Regulation. Sechs vorgegebene PDFs liegen unter `part1/task1/sources/`: Zou2020, Gotoh2014, Gotoh2015, Selfridge2016, Liu2018 und Wang2022. Für die ersten fünf existieren Marker-Konvertierungen und deutsche Zusammenfassungen.

Wissenschaftliche Grenzen:

- Zou2020 ist Review/Modellsynthese, keine unabhängige experimentelle Replikation.
- PER2-Stabilisierung und gegenphasige p53-Verläufe müssen kompartimentspezifisch betrachtet werden.
- Wang2022 liefert DDE-Stabilitäts-/Hopf-Analyse, keine neuen Experimente.
- Gaddameedhi2012 reproduziert bestimmte PER1-Bestrahlungseffekte nicht; daraus folgt keine vollständige Widerlegung sämtlicher PER1-Funktionen.
- Wang-PDF ist lokal lizenziertes Material; keine Freigabe zum Remote-Upload annehmen.
- Die Ausarbeitung ist keine abgeschlossene systematische Literaturübersicht.

### Ursprünglicher großer Text-Mining-Lauf

Verzeichnis: `text_mining/data/runs/task1-full-20260921-complete/`

- 5.986 Suchtreffer plus sechs Seeds.
- Nach Bereinigung 5.858 Papers.
- 2.033 Volltexte beschafft, 3.825 nicht beschafft.
- Alle Volltextentscheidungen `unclear`; null eingeschlossene Papers und null extrahierte Relationen.
- Annotation und Extraktion wurden wegen des Screening-Gates nicht erreicht.
- Technisch vollständig, wissenschaftlich `INCOMPLETE`, kein biologisches Nullergebnis.

Dokumentation: `ERGEBNIS.md`, `verification.json` im Run.

Damals: 136 Tests bestanden, 19.956 Datei-Hashes und tatsächliche Exportzahlen geprüft.

Ein späteres Screening-Audit mit überarbeiteten Regeln selektiert 1.117 der 2.033 Texte als Kandidaten, 916 bleiben unklar. Das ist keine gemessene Screening-Präzision und kein erneuter Task-1-Extraktionslauf.

Audit: `text_mining/data/runs/task1-screening-audit-001/`

## Task 2: Parameterschätzung und Kombinationstherapien

Vorhanden:

- `part1/task2/task2.qmd`
- `part1/task2/task2.draft.qmd`

Die finale Datei existiert und enthält eine ausführliche quellenbezogene Ausarbeitung. Ein abschließender vollständiger Parent-Review dieser Datei ist nicht dokumentiert.

Quellen:

- Fröhlich2018, DOI `10.1016/j.cels.2018.10.013`
- Schmucker2021, DOI `10.1371/journal.pcbi.1009689`

PDFs und vollständige Marker-Konvertierungen: `part1/task2/sources/`

Marker-Konvertierungen wurden auf Seitenzahlen, vorhandenen Text, Bildverweise und unveränderte PDF-Hashes geprüft. Keine vollständige visuelle/Formelprüfung.

Wichtige Aussagen:

- Fröhlichs berichteter >37.000-facher Beschleunigungsfaktor betrifft einen bestimmten Benchmark, teilweise mit Extrapolation; keine allgemeine Garantie.
- Zusätzlich berichtete Parallelisierungsbeschleunigung separat behandeln.
- Vorhersagevalidierung und ihre Grenzen unterscheiden; bessere Korrelation bedeutet nicht automatisch bessere RMSE.
- Schmucker optimiert Behandlungen mittels CMA-ES/HMC, nicht erneut die ursprünglichen Modellparameter.
- Keine experimentelle Validierung der neu vorgeschlagenen Therapien behaupten.
- Keine eigenen Parameterschätzungen oder Benchmarks durchgeführt.

Der Subagent meldete eine erfolgreiche Pandoc-Prüfung mit MathJax.

## Task 3: vollständig ausgearbeitet, keine Simulation

Einstieg:

- `part1/task3/task3.qmd`
- `part1/task3/task3.html`

Die Hauptdatei bindet `a/answer.qmd`, `b/answer.qmd`, `c/answer.qmd` ein.

### 3(a): SBML und BioModels

Unter `part1/task3/a/`:

- Isolierte uv-Umgebung mit Python 3.14 und libSBML 5.21.2.
- `sbml_demo.py`, Tests, Validierungsberichte und archivierte BioModels-Abrufe.

Vorhandene Task-1-Modelle:

- BIOMD0000000170, Becker-Weimann2004: sieben Spezies, 17 Reaktionen.
- BIOMD0000001006, Ciliberto2005: zehn Spezies, 21 Reaktionen.

Beide ohne Error/Fatal eingelesen; ein beziehungsweise 57 Einheitenwarnungen. Warnungen sind dokumentiert, Originale unverändert.

Ciliberto-Download bytegleich; Becker-Weimann unterscheidet sich nur durch einen abschließenden Zeilenumbruch.

Parent-verifiziert, Exit 0, aus `part1/task3/a/`:

```sh
uv run --locked python sbml_demo.py validate
uv run --locked python -m unittest -v
```

Fünf Tests bestanden.

### 3(b): BioModels-Pathway-Statistik

Unter `part1/task3/b/`: Skripte, Rohcache, vier CSVs, acht SVGs und Bericht.

Snapshot vom 21.09.2026:

- 1.096 manuell kuratierte Einträge, alle Taxa/Themen.
- 237 Einträge mit gezählten Modell-Level-Pathway-Annotationen.
- 346 eindeutige Modell/Namespace/Pathway-Paare.
- Anfangs- und Abschlussenumeration derselben IDs.
- Nicht-SBML-Einträge im Inventar behalten.
- Fehlende API-Annotationsfelder bei sechs Modellen per SBML geprüft.

Häufigste IDs:

- Reactome `REACT_152`: 14 Modelle.
- KEGG `sce00010`: elf Modelle.

Modell-Ranglisten einschließlich Gleichständen stehen im Bericht/CSV. KEGG und Reactome jeweils maximal drei IDs je Modell.

Statistik von expliziten Annotationen, keine vollständige biologische Pathway-Abdeckung. Namespaces getrennt; alte/neue Reactome-IDs nicht semantisch zusammengeführt.

Parent-verifiziert, Exit 0, aus `part1/task3/`:

```sh
python3 b/census.py --offline
python3 b/verify_api.py --offline
python3 -m unittest discover -s b -p 'test_*.py' -v
```

Vier Tests bestanden.

### 3(c): Task-1-Proteine in Modellen

Unter `part1/task3/c/`:

- `answer.qmd`, `models_report.md`
- `inspect_models.py`, `check_outputs.py`
- Spezies-/Reaktionstabellen, Modelldaten und archivierte Suchantworten.

Fünf Modelle geprüft: BIOMD170, 1006, 73, 216, 839. Insgesamt 47 Spezies, 123 Reaktionen.

Ergebnis:

- Uhrbausteine mit PER/CRY/BMAL1 und separater p53–MDM2-Baustein vorhanden.
- Keine direkte PER2–p53-Kopplung in diesen fünf Dateien.
- Keine Aussage, dass weltweit oder in ganz BioModels kein gekoppeltes Modell existiert.
- Aggregiertes PER oder PER:CRY nicht als freies spezifisches PER2 ausgeben.
- `CP2` in BIOMD216 ist ein Dimer, nicht PER2.
- Cilibertos p53-Zustände liegen im Kernkompartiment; kein separater cytoplasmatischer p53-Pool.
- Die Antwort ordnet Task-1-Hypothesen den vorhandenen und fehlenden Mechanismen zu.

Parent-verifiziert, jeweils Exit 0, aus dem Projektverzeichnis:

```sh
python3 part1/task3/c/inspect_models.py
python3 part1/task3/c/check_outputs.py
quarto render part1/task3/task3.qmd --to html --no-execute
```

## Task 4: laufende Arbeit, nicht fertig

Aufgabe: Informationen und Netzwerkmodelle für Caco-2 zur Interpretation von SARS-CoV-2-Proteomik sammeln. Allgemeines menschliches Wissen von Caco-2-spezifischer Evidenz unterscheiden.

Nutzerauftrag: Literaturarbeit in Subagents und separater Subagent zur zuverlässigen automatischen Netzwerkerstellung. Das Zuverlässigkeitsziel wurde noch nicht erreicht.

### Gespeicherte Literatur und Daten

Unter `part1/task4/`:

- `acquire.py`, `config.json`
- `corpus/`: 29 reale Volltexte.
- `raw/`: archivierte Antworten.
- `data/mmc1.pdf`, `data/mmc2.xlsx` bis `mmc9.xlsx`
- `data/methods.txt`
- `pride_response.json`, `mendeley_response.json`

Ausgewählte Kandidatenstudie: PMID33898942, Volltext: `part1/task4/corpus/PMID_33898942.txt`

Der Literatur-Subagent meldete verarbeitete Caco-2-Daten, brach aber wiederholt mit `agent_turn_failed: ModelError` ab. Die genaue technische Ursache wurde nicht offengelegt. Dateien blieben erhalten.

Noch nicht abgeschlossen:

- Quellen- und Datensatzprüfung durch den Parent.
- Vollständige nachvollziehbare Kandidaten-/Ausschlusstabelle.
- Abschließender Literaturbericht und Task-4-QMD.
- Biologische Proteomik-/Netzwerkauswertung.

Keine weiteren identischen Subagent-Neustarts ohne Diagnose. Die Literaturarbeit kann anhand vorhandener Dateien direkt fortgesetzt werden.

## Text-Mining-Tool: aktueller Stand

Code: `text_mining/litmine/`

Zentrale Dokumentation:

- `text_mining/README.md`
- `text_mining/docs/task4.md`
- `text_mining/data/runs/task4-rules-001/handoff.json`

Letzter Tool-Subagent: `network-reliability`, Abschlussbericht liegt vor.

Änderungen:

- Dokument-Screening von erfolgreicher Relationserkennung entkoppelt.
- Profile `clock_cancer`, `task4_caco2_sarscov2`, `legacy_clock`.
- Konservative zusätzliche Assertions und Zelllinien-Abundanzaussagen.
- Graph-Sichten `attributed`, `reported_assertions`, `own_experiment`.
- Unbekannte Attribution bleibt unbekannt.
- `assertion_pass` ist keine biologische Bestätigung und kein Nachweis eines eigenen Experiments.
- Gene werden nicht stillschweigend zu Proteinen.
- Keine implizite Übernahme von Caco-2, Infektion oder Zeitpunkten aus dem Titel.

Verifizierter Run: `text_mining/data/runs/task4-rules-001/`

Ergebnis:

- 29/29 lokale Volltexte gelesen.
- Elf Dokumente zur Annotation zugelassen, 18 unklar.
- 1.946 verankerte Mentions.
- Zwei akzeptierte Aussagen, beide aus PMID33898942: IFI35 hochreguliert in Calu-3 und IFI35 hochreguliert in Caco-2.
- Abundanzaussagen, keine Proteininteraktionen.
- Attribution unbekannt; null `auto_pass`-/Own-experiment-Belege.
- Kein belastbares regulatorisches Netzwerk.

Vom Subagenten dokumentierte Prüfungen, aus `text_mining/`:

```sh
uv run python -m unittest discover -s tests -q
uv run python tests/verify_task4_run.py data/runs/task4-rules-001
```

143 Tests bestanden, Exit 0. DB/Parquet/SVG tatsächlich zurückgelesen. Offline-Replay mit blockiertem Netzwerk und blockiertem LLM stimmte überein.

Achtung: `verify_task4_run.py` schreibt einen exklusiven Receipt und verweigert dessen erneutes Überschreiben. Vor Wiederholung Skript lesen.

Neue Läufe benötigen neue Ausgabeordner:

```sh
uv run litmine run --config config.task4.json --out data/runs/<neuer-name>
```

`<neuer-name>` ist ein zu ersetzender Platzhalter, kein wörtlich auszuführender Shell-Ausdruck.

### Unabhängige begrenzte Qualitätsprüfung

Unter `part1/task4/evaluation/`:

- `REPORT.txt`
- `reference.json`, `freeze.json`
- `evaluate_bounded.py`, `results.json`
- `check_evaluation.py`, `checks.json`, `commands.txt`

Separater Subagent, ausdrücklich maschinelle Referenz, kein menschlicher Goldstandard und nicht vollständig verblindet.

Test:

- 40 echte Sätze aus fünf Papers.
- PMID33898942 als Entwicklungsquelle ausgeschlossen.
- 15 positive molekulare Beziehungen in 13 Sätzen.
- Rest Kontext, Unsicherheit, Negation oder außerhalb des Prädikatvokabulars.
- Satzgebundene Bewertung, keine vollständig annotierten Papers.

Ergebnis:

- TP 0, FP 0, FN 15.
- Recall 0 %, Präzision undefiniert.
- Elf Beziehungen ohne passende Entitätskandidaten in verarbeiteten Dokumenten.
- Vier Beziehungen scheitern vor Extraktion am Screening-/Annotations-Gate.
- Kein Referenzpaar mit passenden Kandidaten für beide Endpunkte.
- Deshalb kann dieser Test die Relationsregeln nicht isoliert bewerten.
- Null Fehlvorhersagen bei weitgehender Enthaltung beweisen keine hohe Zuverlässigkeit.

Dokumentierter Prüfaufruf, Exit 0, aus dem Projektverzeichnis:

```sh
python3 -B part1/task4/evaluation/evaluate_bounded.py --check
```

Für Entwicklung nur aggregierten `REPORT.txt` verwenden. Sobald genaue Testlabels zur Verbesserung herangezogen werden, ist dieses Set Entwicklungsdaten; neue zurückgehaltene Beispiele benötigen eine eigene Bewertung.

## Task 5, Task 6 und Part II

Task 5: menschliche Makrophagen/Monozyten/Neutrophile bei Atherosklerose/CAD, einschließlich miRNA-Kontext.

Task 6: entsprechender Mausvergleich.

Beide bisher nicht bearbeitet. Eine frühere Assistentennachricht behauptete versehentlich, dafür Subagents zu starten. Das wurde korrigiert; solche Aufträge wurden nicht gestartet.

Part II ebenfalls nicht begonnen. Lebensmittel, konkrete Ernährungsfrage und Datensatz noch nicht ausgewählt.

## Fortsetzung: begrenzter Alignment-Fix (22.09.2026)

- Dateistand geprüft; weiterhin kein Git-Repository. Bei der Prozessprüfung keine Treffer für `litmine`, `acquire.py`, `evaluate_bounded` oder `network-reliability`.
- `text_mining/litmine/sources.py`: Der satzweise BioC-Fallback berücksichtigt jetzt auch Text am Passage- oder Zeilenende ohne abschließendes Satzzeichen. Mindestlänge, eindeutige Verankerung und exakter Mention-Abgleich bleiben erhalten.
- `text_mining/tests/test_task4.py`: Regressionstest mit Varianten für Passage-/Zeilenende, Unicode-Offsets, doppelte Fundstellen und falsche Quelloffsets ergänzt. Beide positiven Varianten scheiterten vor dem Fix; anschließend bestanden alle 144 Tests (`uv run --locked python -m unittest discover -s tests -q`, aus `text_mining/`).
- Kein neuer Korpuslauf, keine Änderung archivierter Runs. Der Beitrag dieses Fehlers zu den bisherigen Erkennungsverlusten ist nicht quantifiziert; kein Nachweis verbesserten biologischen Recalls.
- Nur aggregierten Evaluationsbericht zur Diagnose verwendet, keine zurückgehaltenen Testlabels gelesen.
- Anschließend mit zwei Subagents bearbeitet: Ein Implementierungsagent ergänzte `screening_investigation` in `text_mining/litmine/rules.py`, ein unabhängiger Read-only-Agent schlug Gegenbeispiele vor. Eng gefasste vergangene Untersuchungshandlungen mit `whether`/`if`/`that` können nun I2 liefern, auch wenn das Ergebnis unsicher oder negativ ist. Zusätzliche Sperren betreffen Planung, hypothetische Formulierungen und Fragen. Relationsfilter, Assertion-Attribution und Legacy-Screening wurden nicht geändert.
- Parent-Codeprüfung und zusätzliche synthetische Tests der finalen Fulltext-Validierung in `text_mining/tests/test_screening_intent.py`: Einschluss erfordert weiterhin I1 und I2. Negierte, geplante, modale und kontrafaktische Untersuchungshandlungen bleiben in den getesteten Fällen unklar; ein eingebettetes Fremdzitat mit `whether` ebenfalls. Das ist keine allgemeine Lösung der Zitatattribution.
- Gesamttest nach Screening-Fix: 151 Tests bestanden, Exit 0 (`uv run --locked python -m unittest discover -s tests -q`, aus `text_mining/`). Die zusätzlichen Fälle sind synthetisch und LLM-unterstützt, kein menschlicher Goldstandard. Kein neuer Korpuslauf und kein gemessener Recallgewinn.
- Grenzen: Satzweite konservative Sperren bleiben teilweise erhalten. Beispielsweise werden koordinierte negative Ergebnisse (`We measured A and observed no change in B`) und `We tested the hypothesis ...` weiterhin nicht als I2 erkannt. Breite alte Auslöser wie `in this study` sind keine vollständige semantische Durchführungsprüfung.
- Quellen-/Datensatzprüfung bleibt offen. Der dafür gestartete Read-only-Subagent wurde vom Dienst mit einer Inhaltsrisiko-Meldung blockiert; kein identischer Wiederholungsauftrag gestartet.

## Offline-Vergleich nach beiden Fixes (22.09.2026)

Neuer, separat gespeicherter Run: `text_mining/data/runs/task4-rules-002-offline-fixes/`. Vergleichsprotokoll: `comparison.json`; Skript: `text_mining/tests/compare_task4_offline.py`. Ein Subagent führte aus, ein zweiter prüfte anschließend unabhängig und read-only. Parent prüfte den Ausführungscode und führte die Gesamttests erneut aus: 151 bestanden, Exit 0.

- Baseline-Konfiguration übernommen, nur `offline=True` und `replay_dir` auf den alten Run gesetzt. Aktuelle Regeln neu berechnet, keine alten Regelantworten wiederverwendet. Der Prüfagent berechnete alle 39 gespeicherten Regelrequests erneut und bestätigte identische Antworten.
- Ergebnis unverändert: 29 Papers, 58 Dokumentdatensätze, elf eingeschlossen, 18 unklar, 1.946 Mentions, 199 Entities, zwei Relationen und zwei Evidenzen mit `assertion_pass`. Keine Änderungen an Screening, Mentionbestand oder Aussagen. Die beiden Fixes bewirken auf diesem eingefrorenen Korpus keinen gemessenen Erkennungsgewinn.
- 69 Cache-Lookups, null Cachemisses. Netzwerk-/Socket-Aufrufe und LLM-Client blockiert; acht Guard-Selbsttests erfolgreich, null protokollierte Aufrufversuche im Lauf und null LLM-Calls. Kein Evaluations-/Gold-Aufruf.
- Vorher-/Nachher-Hashes: 237 Baseline-Dateien und 29 lokale Inputs unverändert. Der unabhängige Prüfer hashte aktuell 236 Baseline-Dateien nach; `evaluation.json` ließ er bewusst aus. Die vollständige historische Unverändertheit bleibt insoweit protokollgestützt.
- Parquet gegen Review zurückgelesen, Datenbankzählungen bestätigt, Exporthashes geprüft, SVG geparst. Der gefilterte Hauptgraph enthält elf Papers, elf Dokumente, drei Entities, zwei Relationen und zwei Evidenzen. Vollständige Tabellen und gefilterten Graph nicht verwechseln.
- Vergleicherskript verwendet für Mention-/Assertion-Deltas Mengen; der Prüfagent bestätigte zusätzlich per Multimengenvergleich, dass auch keine Duplikatänderungen vorliegen. Der Status `complete` des Vergleichs ist technischer Abschluss; wissenschaftlich bleiben beide Runs `incomplete=true` und ohne Qualitätsbewertung.
- Keine neuen Aussagen zur Quellenprüfung. Keine zurückgehaltenen Referenzlabels gelesen. Die unabhängige technische Prüfung ist LLM-unterstützt, kein biologischer Goldstandard.

Ausführung ab Projektverzeichnis: `text_mining/.venv/bin/python -B text_mining/tests/compare_task4_offline.py`. Das Skript verweigert eine Wiederholung bei vorhandenem Zielordner (auch mit `--inspect`). Archiv nicht löschen oder überschreiben; Reproduktion nur in separater Projektkopie ohne diesen Zielordner. Skript unverändert lassen, da sein Hash im Vergleichsprotokoll festgehalten ist.

Nächster Schwerpunkt: offene Task-4-Quellen-/Datensatzprüfung und inhaltliche Ausarbeitung. Weitere Pipelineänderungen nur nach konkreter Diagnose der weiterhin vorhandenen Verluste; diese beiden Fixes allein lösen den Engpass nicht.

## Task 4: Ausarbeitung erstellt (22.09.2026)

Neue Dateien beziehungsweise Outputs:

- `part1/task4/task4.qmd`
- `part1/task4/task4.html`

Die Datei löst Aufgabe 4 als quellenbasierte, ehrliche Teilbearbeitung: Caco-2 als humane Kolon-Adenokarzinom-Zelllinie, publizierte SARS-CoV-2-Proteomik in Saccon et al. 2021/PMID33898942, PRIDE-Zugang `PXD023760`, Supplementtabellen, Caco-2-Grenzen als Darmmodell, ein statisches qualitatives Wirtsantwortmodell und klare Grenzen der automatischen Netzwerkerstellung. Allgemeines menschliches Interferon-Pathway-Wissen, Caco-2-spezifische Proteomikbefunde, andere Zelllinien und technische Text-Mining-Ergebnisse werden getrennt.

Wichtige Aussagen in `task4.qmd`:

- Caco-2 wird als definierte Zelllinie mit RRID/Cellosaurus `CVCL_0025` und Cell Model Passport `SIDM00891` eingeordnet, nicht als gesundes Darmgewebe.
- Saccon et al. wird als Fallstudie genutzt, nicht als vollständige systematische Übersicht. Publizierte Werte werden referiert: 177 signifikant veränderte Proteine in Caco-2, 6.462 in Calu-3; 132 gemeinsam veränderte Proteine in Caco-2 und Calu-3; 88 davon gleichgerichtet; Caco-2 IFN-bezogener Teilbefund 27/131 detektierte Proteine, davon 25 erhöht und zwei erniedrigt. Diese Zahlen sind publiziert, nicht neu gerechnet.
- Das Modell ist ausdrücklich ein statisches, qualitatives Wirtsantwortmodell als begrenzte Teilantwort auf den Netzwerkanteil. Es ist kein vollständiges molekulares Interaktom, kein dynamisches Modell und keine Simulation.
- Die Text-Mining-Pipeline wird als technisches Hilfsmittel ausgewiesen: 29 Papers, 11 eingeschlossen, 18 unklar, 1.946 Mentions, 199 Entities, zwei `assertion_pass`-Evidenzen, keine neuen Aussagen im Offlinevergleich und kein validiertes regulatorisches Netzwerk.
- Die Suchprovenienz steht als PRISMA-orientierte Pilot-Recherche: 54 Treffer-Vorkommen, nach einem Datensatz ohne Kennung und zwei Dubletten 51 identifizierbare Datensätze, 29 lokale Volltexte, 22 Retrievalhindernisse. Keine abgeschlossene Review behaupten.
- Lokale XLSX-Tabellen wurden nicht numerisch geprüft. `task4.qmd` sagt ausdrücklich, dass XLSX-Zuordnung, Probenspalten, Protein-Gruppenkennungen und Kontrastdefinitionen vor einer eigenen Neuauswertung noch zu prüfen sind.

Während der Schlussprüfung meldete ein Read-only-Subagent keine kritischen Zahlenfehler, aber zwei Formulierungen waren zu stark. Diese wurden korrigiert:

- Statt "Für diese Aufgabe genügt ..." steht nun: "Diese Bearbeitung liefert ... als begrenzte Teilantwort ...".
- Statt eines Schlusses gegen Caco-2-spezifische Topologie steht nun: "Ähnliche funktionelle Befunde in Calu-3 belegen keine Caco-2-spezifische Pathway-Topologie." 

`quarto render part1/task4/task4.qmd --to html --no-execute` lief nach diesen Korrekturen erfolgreich, Exit 0. Der Render erzeugte `part1/task4/task4.html`.

Achtung für den nächsten Agenten:

- `task4.qmd` wurde neu erstellt, weil vorher keine Task-4-QMD existierte. Das ist absichtlich.
- Keine eigenen Proteomik-Fold-Changes, p-Werte oder Enrichmentanalysen ergänzen, außer die Supplementtabellen werden vorher sauber geprüft.
- Quellen [1], [2], [4] und [6] wurden per Websuche/Webabruf ergänzt; Saccon et al. basiert auch auf lokalem Text `corpus/PMID_33898942.txt`.
- Die Datei nutzt Mermaid im QMD. Wenn ein anderes Ausgabeformat Probleme macht, zuerst Render prüfen, nicht inhaltlich kürzen.
- Aufgabe 4 ist jetzt abgabefähig als begrenzte, transparente Bearbeitung. Für eine stärkere Lösung wären nächste Schritte: XLSX-Tabellen prüfen, Caco-2-Kontraste reproduzieren, identifiers bereinigen und dann einen echten statischen Netzwerkexport mit Kanten-/Evidenzschema erzeugen.

## Empfohlener nächster Arbeitsgang

1. Aktuelle Dateien und eventuelle laufende Prozesse prüfen. Keine alten Runs überschreiben.
2. Task-4-Datensatz und Literaturauswahl direkt aus den gespeicherten Quellen fertig prüfen.
3. Screening-/Annotationsverluste diagnostizieren: Textalignment, fehlende Endpunktidentitäten, ungeeignete Entitätstypen.
4. Diese Engpässe beheben, ohne Kontext zu erfinden oder Sicherheitsregeln pauschal abzuschalten.
5. Erst dann Relationsregeln erweitern und auf neuen zurückgehaltenen realen Beispielen bewerten.
6. Präzision, Recall, Enthaltung und vorgelagerte Verluste getrennt berichten.
7. Task-4-Ausarbeitung erstellen; automatisch extrahierte Aussagen, kuratierte Datenbankbeziehungen und Messdaten getrennt kennzeichnen.

Der derzeitige Blocker ist nicht fehlende Rechenzeit, sondern unzureichende End-to-End-Erkennung echter molekularer Aussagen. Ein gefüllter Graph oder bestandene Softwaretests reichen nicht als Zuverlässigkeitsnachweis.
