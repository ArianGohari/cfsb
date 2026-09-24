# Abschlussbericht: numerische Reproduktion in Aufgabe 3

Stand 24.09.2026. Geändert und neu angelegt wurden ausschließlich Dateien unter `part1/task3/`. Bestehende Modellrohdaten wurden nicht verändert. Es gab keinen Commit oder Push.

## Ergebnisse

BIOMD0000000170, Revision 3, wurde unverändert von 0 bis 720 h simuliert. Aus 20 Per2/Cry-mRNA-Maxima ab 240 h folgen 19 Periodenabstände: Mittel 23,842681 h, Streuung 0,000301 h. Das passt zum auf eine Nachkommastelle berichteten Literaturwert 23,8 h. Es ist keine Reproduktion experimenteller Einzelmessungen. Das Fenster 100 bis 150 h stimmt qualitativ mit der archivierten BioModels-Kurationsabbildung zu Fig. 3A überein.

BIOMD0000001006, Revision 3, wurde von 0 bis 1.200 SBML-Zeiteinheiten simuliert. Formal deklariert SBML Sekunden; die Achse wird nicht als physiologische Minuten- oder Stundenachse umgedeutet. Zwei p53-Gesamtmaxima liegen bei t = 200,364 und 681,287; gespeicherte Peakwerte 1,46563 und 1,43410. Das Kurationsbild zeigt qualitativ entsprechende Pulse und Größenordnungen. Keine Bilddigitalisierung und kein statistischer Bildvergleich wurden ausgeführt.

Die Peakdetektion verwendet `find_peaks(prominence=0.05)` und parabolische Interpolation über drei Ausgabezeitpunkte. Die Uhr-Ausgabe ist 0,05 h, die p53-Ausgabe 0,1 SBML-Zeiteinheiten. Die Auswerteparameter sind von biologischen Modellparametern getrennt.

## SBML-Semantik

Anfangswerte, Parameter, Kompartimente, Funktionendefinitionen, Assignment Rules und Events sind vollständig als JSON archiviert. LibSBML: keine Error-/Fatal-Meldung; Uhrmodell eine Warnung 99505, p53-Modell 30 Warnungen 99505 und 27 Warnungen 80701. Fehlende Parametereinheiten wurden nicht geraten.

`ModelValue_6 = vratio` ergibt bei Initialisierung den Wert 15. p53 wird aus der Assignment Rule `p53_total - p53_ub - p53_ub_ub` berechnet; die Relation gilt über die Zeitreihe numerisch exakt. Der maximale Residualbetrag der MDM2-Gesamtzuweisung beträgt 5,55 × 10^-17.

Das p53-Einschalt-Ereignis besitzt Trigger `time > 10` und delay 2. Die Wirkung setzt bei etwa t = 12 ein. Das Ausschalt-Ereignis besitzt Trigger `time > 20` ohne Verzögerung. Bei 10,1 und 11,9 sind `step` und `IR` null; bei 12,1 und 19,9 eins; bei 20,1 wieder null. Ein zunächst fehlerhaft auf t = 10,1 formulierter Test wurde anhand des tatsächlich vorhandenen Delay-Feldes korrigiert. Das war ein Testannahmefehler, kein Fehler der unveränderten Simulation. Das ursprüngliche Protokoll ist `initial-event-check.log`.

Die separat heruntergeladene Autoren-XPP-Datei definiert einen Puls von 10 bis 20 ohne diese Ereignisverzögerung. Die Reproduktion bezieht sich auf die kuratierte SBML-Fassung. Sie behauptet keine vollständige Gleichheit des SBML mit allen Autorendateien.

## Numerische Kontrollen

CVODE/BDF: rtol 1e-9, atol 1e-12; Kontrolllauf rtol 1e-11, atol 1e-14. Maximaler skalierter Unterschied 3,279 × 10^-6 für die Uhr und 3,745 × 10^-6 für p53. Skaliert wird spaltenweise durch den größten absoluten Kontrollwert, mindestens 1e-12. Beide liegen unter der vorgegebenen Grenze 1e-5.

Ein zusätzlicher Uhrlauf mit DOP853 (rtol 1e-10, atol 1e-12) unterscheidet sich maximal skaliert um 2,162 × 10^-6. Der Integrator ist unabhängig von CVODE, die SBML-kompilierte rechte Seite stammt in beiden Fällen aus RoadRunner. Das prüft nicht unabhängig den SBML-Parser. Für p53 wurde kein zweiter Integrator ergänzt.

Alle Zeitreihen enthalten endliche Werte; Spezies sind bis Toleranz 1e-10 nicht negativ. Frisch initialisierte Wiederholungen sind bitgleich. Eine vollständige Wiedererzeugung in einem isolierten temporären Ordner ergab bytegleiche CSV-, SVG- und PNG-Dateien sowie einen bytegleichen Validierungsbericht. Die Figuren wurden betrachtet; Beschriftungen und Legenden sind lesbar.

## Snapshot

Der Census bleibt der Erhebungsstand 21.09.2026: 1.096 Modelle, 346 eindeutige Modell-Pathway-Paare. Vier CSV-Dateien, acht SVG-Dateien und das Snapshot-Protokoll wurden bytegleich neu erzeugt. Das zusätzliche Manifest fixiert 2.316 Dateien aus dem Archiv. Eine Hashfixierung ersetzt keine atomare Erhebung und keine gemeinsame Pathway-Datenbankversion. Neue Live-Daten wurden nicht in den alten Census eingemischt.

## Abschließende Kommandos und Exitcodes

Alle folgenden Kommandos endeten mit Exit 0. Die ersten drei werden aus `part1/task3/`, der vierte aus `part1/task3/a/`, die übrigen aus der Projektwurzel ausgeführt.

```text
python3 b/census.py --offline
python3 b/verify_api.py --offline
python3 -m unittest discover -s b -p test_*.py -v
uv run --locked python -m unittest -v
python3 part1/task3/c/check_outputs.py
uv sync --project part1/task3/simulation --locked --python 3.12 --no-build
uv run --project part1/task3/simulation --locked python part1/task3/simulation/simulate.py
uv run --project part1/task3/simulation --locked python -m unittest discover -s part1/task3/simulation -p test_*.py -v
uv run --project part1/task3/simulation --locked python part1/task3/simulation/verify_reproduction.py
python3 part1/task3/simulation/render_standalone.py
```

Testzahlen: vier bestehende Census-Tests, fünf bestehende SBML-Tests und vier neue Simulationstests, insgesamt 13 Unit-Tests. Hinzu kommen die vollständigen Offline-Regenerationen, der API/SBML-Abgleich und die Assertions im Simulationslauf. Die exakten Argumentlisten und Exitcodes stehen in `results-20260924/snapshot-validation.json` sowie `final-checks.json`. `render_standalone.py` führt `quarto render task3.qmd --no-execute` in einem isolierten temporären Projekt unter task3 aus und übernimmt das selbstständige HTML. Das übergeordnete Buchprojekt wurde nicht verändert.

## Grenzen

Kein gekoppeltes PER2-p53-MDM2-Modell, keine neuen biologischen Parameter, keine Kalibrierung und keine klinische Schlussfolgerung. Der Kurationsbildvergleich ist qualitativ. Die Einheitenwarnungen bleiben bestehen. Numerische Reproduzierbarkeit gilt für die fixierte Umgebung; bitgleiche Ergebnisse auf anderen CPU-/Bibliothekskombinationen sind nicht zugesichert. Eine PNFL-Abbildung wurde nicht ergänzt, da sie für die Original-SBML-Simulation nicht erforderlich ist.
