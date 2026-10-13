# Milch-miRNA-Inventar

Offline-Auswertung gespeicherter Papers, Tabellen, Referenzsequenzen und kuratierter Quellennotizen. Keine neue Suche oder automatische Volltextlektüre.

Eingaben: `data/sources/`, `data/datasets/milk_mirna_inventory/` und `obsidian/Projekt/Literatur/`. Diese Dateien liegen nur lokal. Ergebnisse: `output/part2/milk_inventory/`.

| Skripte | Aufgabe |
|---|---|
| `build.py`, `verify_pdf.py` | Studienangaben und Tabellenwerte mit Fundstellen prüfen |
| `compare_sequences.py`, `audit_annotations.py` | Referenzsequenzen und Annotationen vergleichen |
| `scan_human_seeds.py` | Kanonische Seedstellen in humanen GENCODE-48-3′UTRs suchen |
| `search_targets.py`, `export_target_screen.py` | Gespeicherte Treffer und aktuelle Kandidatenbewertungen exportieren |
| `export_processing_pilot.py`, `review_processing_supplements.py` | Tierart, Material und Verarbeitung zuordnen |
| `extract_ali_tables.py`, `extend_published_lists.py` | Zusätzliche publizierte Namenslisten auswerten |
| `build_candidate_evidence.py`, `review_additional_candidates.py` | Milch-, Sequenz- und Targetbelege zusammenführen |
| `audit_reported_targets.py`, `review_bae_reporter.py`, `review_pfkl.py` | Publizierte Sequenzen und Targetangaben prüfen |
| `review_pfkp_isoform.py`, `review_pgam1_dlat.py` | Weitere humane Bindestellen prüfen |
| `extract_pfkl_kinetics.py`, `review_pfkl_turnover.py` | Enzymmesswerte und mögliche Abbauraten entnehmen |
| `export_report_scope.py`, `plot_study_counts.py` | Berichtsauswahl und Studiengrafiken erzeugen |

Reihenfolge und Umgebung stehen im [Gesamtlauf](../../reproduction/README.md). Einzelne Skripte erst starten, wenn ihre Eingaben vorliegen:

```sh
uv run --offline --locked --project code/part2/reproduction python code/part2/literature/milk_inventory/compare_sequences.py
```

Tierarten, Milchfraktionen und Nachweisschwellen bleiben getrennt. Fehlende Werte sind keine Nullen; CPM, Reads und TPM werden nicht zusammengezählt. Der 270-Sequenzen-Vergleich verwendet Li und Krupova; zusätzliche Namenslisten erweitern ihn nicht automatisch.

Seedtreffer sind Bindestellenhypothesen. Geprüft werden 8mer, 7mer-m8 und 7mer-A1 in protein-codierenden GENCODE-48-Transkripten; Koordinaten sind 1-basiert und inklusiv. Die Suche belegt weder Isoformexpression noch Regulation. Manifeste halten Eingaben, Fundstellen und Prüfsummen fest.
