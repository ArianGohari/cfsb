# Aktueller Lesestand für Aufgabe 1(d)

Zuerst [html_addendum.md](html_addendum.md) lesen. Der direkt archivierte Gaddameedhi2012-Volltext korrigiert die frühere Abstract-Einordnung: Fig. 8/9 berichten eine gezielte Nichtreproduktion spezifischer PER1-/IR-Befunde in denselben benannten humanen Zelllinien, Fig. 7 dagegen reduzierte UV-Apoptose nach PER1/2-Knockdown in Mausfibroblasten. Protokollgrenzen verhindern eine totale Falsifikationsaussage.

[fulltext_review.md](fulltext_review.md) enthält den älteren API-Audittrail und die weiterhin gültige Dickmeis-Volltextprüfung. Seine Gaddameedhi-Lücke ist durch den HTML-Nachtrag geschlossen. Gauger2005, Ozturk2009 und Gery2007 bleiben ohne hier beschafften Originalhaupttext.

[report.md](report.md), extraction.json und die Aussage-/Zitatfelder in records.csv sind der historische Abstract-Pilot. Für PMID 22918252 verweisen current_review_ref und current_review_status in records.csv auf die vorrangige Neubewertung. Ein alter Status fulltext_eligibility=not_processed ist kein aktueller Beschaffungsbefund. Nicht ohne Nachtrag in QMD übernehmen.

raw/ und fulltext_raw/ wurden unverändert erhalten. Der neue Original-HTML-Abruf liegt in html_raw/ (Rohantwort, URL, UTC, HTTP, SHA256, Lesefassung). html_evidence.json enthält zehn belegte Zitate. html_addendum_plan.md dokumentiert den Plan vor der neuen Anfrage. Eine neue Anfrage, insgesamt acht in der Volltextphase; keine Vollständigkeit oder endgültige Erstpriorität beansprucht.

Offline prüfen:

```sh
python3 text_mining/pilot_task1d/followup/verify_html_addendum.py
python3 text_mining/pilot_task1d/followup/validate.py
```

Alle Änderungen liegen in followup/. QMD wurde nicht bearbeitet.
