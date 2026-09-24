# Suchprotokolle, Entscheidungen und PRISMA-Zahlen

Dies sind Datenverträge für die spätere Implementierung. Noch keine echten Trefferzahlen oder Review-Ergebnisse. Die Protokolle liegen pro Run außerhalb des biologischen Graphen; es entstehen keine weiteren biologischen Parquet-Tabellen.

## Identitäten und Zähleinheiten

- Record: ein bibliografischer Treffer aus einer bestimmten Suche oder einem anderen dokumentierten Fundweg. Derselbe Bericht kann mehrere Records haben.
- Report: eine Veröffentlichung, im Projekt durch `paper_id` repräsentiert. Abstract und Volltext desselben Papers sind Document-Versionen desselben Reports, keine zwei Reports.
- Study: die zugrunde liegende Untersuchung. Mehrere Reports können dieselbe Study beschreiben; ein Report kann mehrere Untersuchungen enthalten.

Study ist weder mit Paper noch mit Evidence gleichzusetzen. Ohne belastbare Studienzuordnung keine Studienzahl aus der Zahl der Papers ableiten.

## Suchmanifest

Das bestehende Raw-/Run-Manifest erhält je `search_id`:

```text
source, platform, source_kind, full_query, filters, coverage_period,
searched_at, sort_order, pagination, reported_hits, retrieved_records,
completion_status, raw_response_refs, deduplication_version
```

`source_kind` unterscheidet Datenbank/Register und andere Fundwege, etwa vorgegebene Referenzen. PubTator ist im aktuellen Entwurf eine Annotationsquelle, keine zusätzliche Literaturdatenbank mit eigenen Treffern. Vom Dienst gemeldete Trefferzahlen und tatsächlich gespeicherte Treffer werden separat berichtet. Fehlende Seiten oder API-Limits dürfen nicht als vollständige Suche erscheinen.

## records.csv: Treffer vor Deduplikation

```text
record_id,search_id,source_identifier,paper_id,duplicate_of,raw_ref
```

Ein Record ist innerhalb einer Suche stabil identifiziert. Wiederholter Download derselben Seite erzeugt keine weiteren Records. Derselbe Bericht in zwei Suchstrategien kann zwei Records erzeugen; die Zusammenführung wird ausdrücklich protokolliert. `duplicate_of` verweist auf den behaltenen Record, nicht auf sich selbst und nicht zyklisch. Identifierkonflikte bleiben im QC-Protokoll offen; dafür wird kein erfundener fachlicher Ausschluss erzeugt.

Bei mehreren Fundwegen wird die Zählzuordnung des behaltenen Records deterministisch festgelegt und im Manifest beschrieben. Alle anderen Fundwege bleiben erhalten. So wird derselbe Report am Ende nicht mehrfach eingeschlossen.

## screening.csv: phasenbezogene Ereignisse

Die bisherige einfache Screeningdatei wird erweitert, nicht um eine weitere Auswahl-Datenbank ergänzt:

```text
event_id,paper_id,record_id,stage,decision,primary_reason_code,criterion_id,
reason,evidence_quote,document_id,input_hash,screening_run_id,decided_at,supersedes_event_id
```

| Stage | Zulässige Entscheidungen | Bedeutung |
|---|---|---|
| `title_abstract` | `include`, `exclude`, `unclear`, `not_processed` | `include` ist nur Weiterleitung; `unclear` wird ebenfalls zur Beschaffung weitergeleitet |
| `retrieval` | `retrieved`, `not_retrieved`, `pending`, `not_processed` | Bezieht sich auf den gesuchten Bericht/Volltext, nicht auf einen bereits verfügbaren Abstract |
| `fulltext_eligibility` | `include`, `exclude`, `unclear`, `not_processed` | Endgültiger Einschluss erst nach abgeschlossener Eignungsprüfung |

Ein Ausschluss benötigt einen anwendbaren Kriteriumsbezug und einen primären fachlichen Grund. Weitere Details stehen in `reason`; pro Report wird für die Ausschlusszählung nur ein primärer Grund verwendet. Fehlende Texte, offene Entscheidungen oder Modellfehler sind keine solchen Gründe.

Bei technischen Ereignissen dürfen Zitat und Kriterien-ID fehlen. Input-Hash und Quellreferenz bleiben erhalten. Fehlende Modellantwort bedeutet `unclear` beziehungsweise `not_processed`, nie einen fachlichen Ausschluss. Ein LLM-Ausfall blockiert den Batch nicht unbegrenzt; der Lauf kann als unvollständig enden.

Wiederholungen erzeugen keine zusätzlichen Auswahlobjekte. Eine neue Entscheidung kann eine alte über `supersedes_event_id` ablösen; das Run-Manifest fixiert die aktive Ereignismenge. Mehrere aktive Entscheidungen derselben Phase für denselben Report sind ein Integritätsfehler. Für nachträglich ergänzte Reports bleibt der ursprüngliche Fundweg erhalten.

## study_reports.csv: nur bei belegter Studienzuordnung

Wenn Studienzahlen berichtet werden sollen, wird eine kleine Zuordnung geführt:

```text
study_id,paper_id,link_basis,source_ref,assessment_status
```

Nur begründete, geprüfte Zuordnungen fließen in die Studienzahl ein. Automatische Kandidaten bleiben von akzeptierten Zuordnungen unterscheidbar. Unterschiedliche Papers sind ohne Nachweis keine unabhängigen Replikationen. Solange die Zuordnung unvollständig ist, wird die Studienzahl als noch nicht bestimmt berichtet, nicht als null und nicht als Paperzahl. Das ist eine offene methodische Aufgabe; die Pipeline darf fehlende Zuordnungen nicht erfinden.

## Zahlen aus Ereignissen statt aus dem Graphen

Ein Export berechnet `prisma_counts.json` und das offizielle Flussdiagramm später aus einem eingefrorenen Review-Stand. Das ist ein Ergebnisartefakt pro Lauf. Python berechnet die Zahlen; das LLM formuliert sie nicht frei. Die passende offizielle Vorlage wird verwendet und zitiert.

Die folgenden Größen sind interne Kontrollsummen, keine Ersatzvorlage. Sie gelten nach Deduplikation und Zusammenführung der Quellenzweige auf eindeutig gezählten Objekten. Datenbanktreffer und weitere Quellen werden im offiziellen Diagramm entsprechend dessen Struktur getrennt ausgewiesen.

```text
identifizierte Records
  = behaltene Records + Duplikate + andere dokumentierte Vorab-Entfernungen

behaltene Records
  = abgeschlossene Abstract-Screenings + noch nicht verarbeitete Records

abgeschlossene Abstract-Screenings
  = Abstract-Ausschlüsse + zur Beschaffung weitergeleitete Reports

zur Beschaffung weitergeleitete Reports
  = beschaffte Reports + nicht beschaffte Reports + noch offene Beschaffungen

beschaffte Reports
  = abschließend geprüfte Reports + unklare oder noch nicht geprüfte Reports

abschließend geprüfte Reports
  = eingeschlossene Reports + Volltext-Ausschlüsse
```

Vorab-Entfernungen durch Automatisierung werden nur ausgewiesen, wenn sie tatsächlich vor dem Screening stattfinden. Ein LLM-Ausschluss nach Lektüre von Titel/Abstract ist in unserem Ablauf ein Screening-Ausschluss, keine vorab entfernte Dublette. Ergänzende Methodenangaben benennen, welche Entscheidungen automatisiert waren.

Offene Restmengen werden in Bericht und Zählmanifest separat gezeigt. Ein unvollständiger Lauf darf nicht in ein vollständig abgeschlossenes Diagramm gezwungen werden. Ein endgültiges Flussdiagramm mit Studienzahlen setzt eine belastbare Studienzuordnung voraus. Explorative Abstract-Extraktion bei fehlendem Volltext bleibt vom primären Einschlussbestand getrennt.

## Integritätsregeln und Abgabe

- Keine Doppelzählung durch API-Retries, mehrere Textversionen oder mehrere Modellantworten.
- Record-Deduplikation vor Auswahlzählung; Auswahl und Dokumentbeschaffung getrennt auswerten.
- Jeder Volltext-Ausschluss referenziert einen Report und einen primären fachlichen Grund; ausgeschlossene scheinbar passende Arbeiten im Bericht mit Begründung nennen.
- Ein eingeschlossener Report ohne extrahierte Relation bleibt eingeschlossen. Graph-Node- oder Edge-Zahlen ersetzen keine Review-Zahlen.
- Prüfen, dass die Belege der Eignungsentscheidung zum verwendeten Dokumentstand passen und nicht aus einer späteren Textversion stammen.
- Für den primären Graphen sowohl endgültigen Report-Einschluss als auch `validation_status=auto_pass` verlangen.
- In den Abschlussbericht gehören Quellen-/Suchprotokoll, Protokolländerungen, Ausschlussliste, Flussdiagramm, eingeschlossene Reports/Studien, Datenverfügbarkeit und methodische Grenzen.

Grundlage: [PRISMA-2020-Checkliste](https://www.prisma-statement.org/prisma-2020-checklist), [Flow-Diagramme](https://www.prisma-statement.org/prisma-2020-flow-diagram) und [PRISMA-S](https://www.prisma-statement.org/prisma-search).
