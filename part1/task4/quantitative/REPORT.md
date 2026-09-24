# Table S11: nachvollziehbare Sekundäranalyse

## Eingabe und Prüfung

Analysiert wurde `data/mmc9.xlsx`, Blatt `Caco2_norm_file`. Die Tabelle enthält 8.768 eindeutige UniProt-Zugänge und sechs numerische, vollständig belegte Probenspalten. Ihre Bezeichnungen sind `R2_Caco2_Mock_U1`, `R2_Caco2_SARS-CoV-2_T1` bis `U3` und `T3`. Nach Sortierung sind die Werte jeder Spalte identisch. Das ist mit Quantilnormalisierung vereinbar.

Die Zugänge wurden mit der Proteintabelle `data/mmc5.xlsx`, Blatt `Proteins`, verbunden. 8.759 Zugänge stimmen exakt überein; neun bleiben ohne Symbol oder Beschreibung und werden nicht verworfen.

## Modell und Ergebnis

Das Primärmodell ist ein robustes unpaariges `limma`-Modell für T minus U auf der gelieferten normalisierten Skala. Es findet 175 Proteine bei BH-FDR < 0,05 und 425 bei BH-FDR < 0,10. Davon sind 77 Differenzen positiv und 98 negativ.

Ein Modell mit dem wiederkehrenden U/T-Label als Block ist nur eine Sensitivitätsrechnung, weil das Workbook keine Zuordnung zu gepaarten biologischen Proben dokumentiert. Dieses Modell ergibt 45 beziehungsweise 98 Proteine bei den beiden FDR-Schwellen. Die Abhängigkeit von der Annahme ist daher sichtbar und wird nicht verborgen.

Die publizierten 177 signifikanten Caco-2-Proteine werden ungefähr erreicht, aber nicht exakt reproduziert. Diese Analyse rekonstruiert nicht die vollständige Filterung und Vorverarbeitung der Publikation. Die gemeldeten Differenzen sind keine Fold Changes.

## Ausführen und Prüfen

```bash
Rscript quantitative/analyse_table_s11.R data/mmc9.xlsx data/mmc5.xlsx quantitative
Rscript quantitative/validate_table_s11.R quantitative
python3 quantitative/run_quantitative_qc.py data/mmc9.xlsx quantitative
python3 quantitative/validate_outputs.py data/mmc9.xlsx quantitative
```

`table_s11_differential.tsv` enthält das vollständige Ergebnis. `table_s11_summary.json` und `sensitivity_summary.tsv` fassen die Modelle zusammen. `validation_report.json` bestätigt die Ausgaben des R-Skripts; die weiteren JSON- und CSV-Dateien dokumentieren die Struktur- und Qualitätskontrollen der Eingabetabelle.
