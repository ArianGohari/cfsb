# Begrenzter Volltext- und Prioritätscheck

Vor dem ersten neuen Netzabruf festgelegt. Ziel: historische Beiträge der vier Kandidaten und ältere Bezugspunkte unterscheiden, keine globale Erstentdeckung behaupten. Nur history/ beschreiben; alle 21 vorhandenen history-Dateien bleiben unverändert (before.json). Bereits vorhandene OpenAlex-Antworten aus followup/raw wurden lesend übernommen und unter input/ kopiert. Es werden keine Schlüssel gesucht und keine Authentifizierung oder Sperrumgehung verwendet.

## Budget und Ablauf

Höchstens 12 neue HTTP-Abfragen insgesamt, einschließlich etwaiger Weiterleitungen. Keine automatischen Weiterleitungen, keine Retries, 25 Sekunden Socket-Timeout. Jeder Request wird vor Abruf mit URL, UTC und Zweck ins append-only requests.jsonl geschrieben; Antwortbytes und Abschlussstatus werden je Request separat gespeichert. HTTP-Fehler und Nicht-PDF-Antworten gelten nicht als gelesene Artikel.

1. Drei aus lokalen OA-Metadaten bekannte PDF-Adressen (Fu, Gery, Gréchez-Cassiau); HTTP-Links nur auf HTTPS umgestellt. Für Matsuo ein öffentlicher Verlags-Volltextlink aus DOI und Verlagsmuster. Höchstens vier Abfragen. Bei 401/403/Challenge keine weiteren Versuche an dieser Artikeladresse, kein Browser-/Cookie-Wechsel.
2. Bis zu vier DOI-Lookups bei der öffentlichen Crossref-API, um die Referenzlisten der Kandidaten zu prüfen. Crossref-Referenzen sind bibliografische Metadaten, keine gelesenen Originaltexte.
3. Restbudget (mindestens vier, wenn 1 und 2 ausgeschöpft): höchstens zwei gezielte Europe-PMC-Suchabfragen aus den so gefundenen älteren Referenzen, jeweils resultType=core, format=json, pageSize=10, cursorMark=*, eine Seite, Standardsortierung. Keine Sprach-/Species-/OA-Beschränkung. Query und Identifier werden vor dem Request protokolliert, Trefferzahl und gespeicherte Anzahl danach. Die letzten maximal zwei Abfragen dürfen zugängliche Originalvolltexte identifizierter Referenzen über deren PMCID abrufen. Wenn keine geeigneten PMCID vorliegen, endet der Lauf früher; keine breite Ersatzsuche.

Keine PubMed-/OpenAlex-Abfrage zur Wiederholung bereits vorhandener Kandidatenmetadaten. Kein automatisches Citation-Crawling. Bei erfolgreichen Kandidatenvolltexten werden Einleitung, relevante Resultate, Diskussion und zugehörige Referenzen gezielt gelesen; gelesene Abschnitte ausdrücklich dokumentieren. Bei Blockade bleibt der bisherige Abstractstatus bestehen. Ältere Referenzen werden anhand konkreter Abstracts/Volltexte bewertet, nicht aufgrund ihres Zitiertwerdens als Replikation oder als Erstentdeckung bezeichnet.

## Vorab bekannte Abrufziele

- Fu 2002: https://www.cell.com/article/S0092867402009613/pdf (lokale Europe-PMC- und OpenAlex-OA-Location).
- Gery 2006: https://www.cell.com/article/S1097276506002565/pdf (lokale OpenAlex-OA-Location).
- Gréchez-Cassiau 2008: https://www.jbc.org/article/S002192582068214X/pdf (lokale Europe-PMC-OA-Location).
- Matsuo 2003: https://www.science.org/doi/10.1126/science.1086271 (öffentliche Verlagsseite; keine OA-Location in vorhandenen Metadaten).
- Crossref: https://api.crossref.org/works/{URL-kodierte DOI}; die vier DOI stehen in ../records.csv.
- Europe PMC: https://www.ebi.ac.uk/europepmc/webservices/rest/search und gegebenenfalls /{PMCID}/fullTextXML.

## Auswertung und Tests

Neue Befunde in ../fulltext_review.md, Belegstellen in evidence.json. Rohdaten, ursprüngliche CSV und Reports werden nicht überschrieben. Offline-Tests prüfen nur diesen neuen Bereich plus Erhalt der 21 vorhandenen history-Artefakte, Requestbudget und Rohdatenhashes, Textbelege und lokale Links. Parallele Änderungen außerhalb history/ sind kein Testfehler. Keine globalen PRISMA-Zahlen.
