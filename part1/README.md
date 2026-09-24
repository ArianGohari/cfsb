# Teil I: Abgabestand 24.09.2026

Für alle sechs Aufgaben liegen Quarto-Quellen vor. `quarto render` erzeugt das vollständige Buch lokal unter `_book/index.html`. Die Antworten behandeln den geforderten Stoff mit den jeweils verfügbaren Quellen und Daten. Die erstellten Netzwerke für Aufgaben 4 bis 6 sind begrenzte, statische Evidenzmodelle; sie sind keine vollständigen zellulären oder dynamischen Modelle.

| Aufgabe | Ausarbeitung | Ergebnis und Grenze |
|---|---|---|
| 1 | [QMD](task1/task1.qmd) | Teilaufgaben a–g; kleine getrennte Text-Mining-Prüfstichprobe und numerische Wang-DDE-Reproduktion. Der Vollkorpus wurde nicht erneut extrahiert. |
| 2 | [QMD](task2/task2.qmd) | Parameterschätzung und Therapieoptimierung quellenbezogen erläutert; begrenzter CMA-ES-Benchmark auf dem publizierten Pan-Cancer-Modell, keine erneute Parameterschätzung. |
| 3 | [QMD](task3/task3.qmd) | SBML-Demo, Pathway-Zählung, Modellvergleich und Simulation zweier unveränderter BioModels-SBMLs. Keine Kopplung der Modelle. |
| 4 | [QMD](task4/task4.qmd) | Caco-2-Fallstudie mit Supplementaudit, [Evidenznetz](task4/model/network.json) und robuster `limma`-Sekundäranalyse von Table S11: 175 Proteine bei BH-FDR < 0,05 im dokumentierten Primärmodell. |
| 5 | [QMD](task5/task5.qmd) | Humanes myeloides [Evidenznetz](task5/data/network.json) und Reanalyse von GSE41571: 5 rupturierte gegen 6 stabile Karotisplaques, 852 Gene bei BH-FDR < 0,05. Keine SFB1123-Patientendaten. |
| 6 | [QMD](task6/task6.qmd) | Murines [Evidenznetz](task6/network/network.json), gepaarte Subset-Analysen von GSE17256 und GSE18565 sowie beschreibende Prüfung von GSE97310. Der Mensch-Maus-Vergleich umfasst 17 messbare Orthologpaare. |

Die Quellenbewertung und Netzwerkkuration für Aufgaben 4 bis 6 sind LLM-unterstützt. Technische Prüfungen belegen Dateikonsistenz und reproduzierbare Exporte. Sie ersetzen keine unabhängige biologische Validierung oder eine vollständige systematische Literaturübersicht. Details stehen in den jeweiligen Ausarbeitungen und Auditdateien.
