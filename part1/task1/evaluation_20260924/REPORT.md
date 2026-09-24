# Task 1(g): begrenzte Offline-Prüfung

Diese Prüfung verwendet echte Sätze aus Gotoh et al. (2014, 2015), Liu et al.
(2018), Zou et al. (2020) und Selfridge et al. (2016). Die Zuordnung wurde mit
LLM-Unterstützung erstellt. Sie ist kein menschlicher Goldstandard. Jeder
Ausschnitt muss genau einmal in der lokal archivierten Quelle vorkommen; Hash,
Offset und Länge stehen im Laufprotokoll.

`development.json` enthält vier Screening-Ausschnitte und sechs Sätze für
Entitäten und Relationen. Danach wurden Regeln und Entwicklungsdaten per
SHA-256 eingefroren. `test.json` wurde erst anschließend angelegt. Frühere
zurückgehaltene Evaluationslabels wurden weder gelesen noch übernommen.

Im Entwicklungssatz stimmen alle vier Screening-Entscheidungen, alle elf
erwarteten Entitäten und alle vier Relationen. Zwei Sätze ohne belegte Relation
führen zur Enthaltung. Diese Werte messen Anpassung an Entwicklungsdaten und
sind keine unabhängige Qualitätsaussage.

Der neue Testsatz enthält fünf Screening-Ausschnitte und acht Relationssätze.
Die Regeln erkennen eine von zwei einzuschließenden Untersuchungen. Ein
Literaturhinweis mit den Worten "for review" wird fälschlich ausgeschlossen,
obwohl der Ausschnitt selbst kein Review ist. Zwei unklare Ausschnitte werden
korrekt als unklar belassen.

Die Entitätsstufe findet 17 von 17 erwarteten kanonischen Entitäten ohne
zusätzliche Entität. Die Relationsstufe findet vier von fünf erwarteten
Relationen und erzeugt keine Fehlkante. Das entspricht Precision 1,00 und
Recall 0,80 in diesem kleinen Testsatz. Bei einer positiven Aussage enthält
sich die Pipeline: "Mdm2 associated with hPer2" stellt die Argumente in der
Gegenrichtung zur entwickelten Oberflächenform dar. Alle drei negativen oder
unspezifischen Testsätze führen zur Enthaltung.

Der Graph enthält deshalb vier testbelegte Kanten: PER2 bindet MDM2, MDM2
ubiquitiniert PER2, MDM2 fördert PER2-Abbau, und PER2 stabilisiert TP53. Er ist
ein Export der gefundenen Testbelege. Vollständigkeit für die Literatur oder
das biologische Netzwerk wird nicht behauptet.

Reproduktion aus dem Projektverzeichnis:

```sh
python3 -B part1/task1/evaluation_20260924/evaluate_task1.py \
  --check --out text_mining/data/runs/task1-offline-eval-20260924
```

Der Lauf nutzt nur Python-Standardbibliothek und lokale Dateien. Netzwerk und
generative Modellaufrufe sind nicht Bestandteil des Skripts.
