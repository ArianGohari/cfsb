# Quellen- und Dateiaudit zu Aufgabe 4

Offline-Prüfung der gespeicherten Recherche und Dateiprovenienz. Die fachliche Eignung der Kandidaten und numerische Messergebnisse wurden nicht bewertet.

## Recherchebestand

54 Treffer-Vorkommen, 2 ID-Dubletten und 1 Datensatz ohne interne `paper_id` ergeben 51 intern identifizierte Datensätze. 29 lokale Volltexte stimmen mit den archivierten Retrievaltexten und deren Hashes überein.

Der nicht übernommene Datensatz besitzt bereits die Quellkennung `PMC:PMC8108313`. Die historische Bezeichnung "ohne verwendbare Kennung" war daher zu weitgehend. Festgestellt ist eine fehlende interne Kennung. Eine Nachakquisition oder Zusammenführung mit anderen Publikationsversionen ist nicht erfolgt.

Zugriffshindernisse sind keine fachlichen Ausschlüsse. Alle Einträge des Registers tragen deshalb `eligibility=not_assessed`.

| Retrievalstatus | Eindeutige interne IDs |
|---|---:|
| missing_pmcid | 17 |
| oa_not_confirmed | 3 |
| retrieved | 29 |
| http_500 | 2 |

## Datensatz und Supplemente

Die Artikelkennung und DOI stimmen mit der ausgewählten Fallstudie überein. `PXD023760` steht in deren Datenverfügbarkeitsabschnitt und im archivierten PRIDE-Datensatz. PRIDE verwendet einen anderen Projekttitel; DOI und Referenzliste sind dort leer. Die Zuordnung stützt sich daher auf den expliziten Zugang im Artikel.

Der archivierte PRIDE-Abruf und der Supplementabruf haben HTTP 200. Der archivierte Mendeley-API-Abruf hat HTTP 404. Dieser Fehlschlag sagt nichts über die heutige Verfügbarkeit einer Mendeley-Webseite aus.

Alle neun lokalen Supplementdateien sind bytegleich mit den Mitgliedern des archivierten Europe-PMC-ZIPs. Die acht XLSX-Container bestehen die CRC-Prüfung. Tabellenlabels stammen aus den XML-Medienverweisen des Artikels; Blattnamen wurden ausschließlich aus `xl/workbook.xml` gelesen.

| Lokale Datei | Label im Artikel | Blattname |
|---|---|---|
| mmc1.pdf | Document S1 | PDF |
| mmc2.xlsx | Table S4 | PeptideGroups |
| mmc3.xlsx | Table S5 | Proteins |
| mmc4.xlsx | Table S6 | PeptideGroups |
| mmc5.xlsx | Table S7 | Proteins |
| mmc6.xlsx | Table S8 | 293FT_norm_file |
| mmc7.xlsx | Table S9 | Huh7_norm_file |
| mmc8.xlsx | Table S10 | Calu3_norm_file |
| mmc9.xlsx | Table S11 | Caco2_norm_file |

Numerische Zellwerte, Probenspalten, Formeln und biologische Kennungen wurden nicht geprüft. Bytegleichheit und lesbare Container belegen keine statistische Reproduzierbarkeit. Die Beschreibungsfehler "Calu2"/"Caco3" im Artikel bleiben bestehen; die Blattnamen lauten `Calu3_norm_file` und `Caco2_norm_file`.

## Kandidaten- und Zugriffsregister

Die maschinenlesbare Fassung in `audit.json` enthält Titel, DOI, Quellverweise und sämtliche 54 Suchvorkommen. Die folgende Tabelle fasst nach interner ID zusammen.

| Interne ID | PMC-ID | Suchvorkommen | Retrievalstatus | Fachliche Eignung |
|---|---|---:|---|---|
| DOI:10.1101/2020.07.20.213280 |  | 1 | missing_pmcid | ungeprüft |
| DOI:10.1101/2020.08.28.271684 |  | 2 | missing_pmcid | ungeprüft |
| DOI:10.1101/2020.09.09.289488 |  | 1 | missing_pmcid | ungeprüft |
| DOI:10.1101/2021.01.17.427024 |  | 1 | missing_pmcid | ungeprüft |
| DOI:10.1101/2021.02.16.431318 |  | 1 | missing_pmcid | ungeprüft |
| DOI:10.1101/2021.06.03.21258241 |  | 1 | missing_pmcid | ungeprüft |
| DOI:10.1101/2022.04.17.488607 |  | 1 | missing_pmcid | ungeprüft |
| DOI:10.1101/2023.04.13.536832 |  | 1 | missing_pmcid | ungeprüft |
| DOI:10.1101/2023.09.19.558444 |  | 1 | missing_pmcid | ungeprüft |
| DOI:10.1101/2025.05.01.651662 |  | 1 | missing_pmcid | ungeprüft |
| DOI:10.20944/preprints202006.0206.v1 |  | 2 | missing_pmcid | ungeprüft |
| DOI:10.21203/rs.3.rs-100849/v1 |  | 1 | missing_pmcid | ungeprüft |
| DOI:10.21203/rs.3.rs-117172/v1 |  | 1 | missing_pmcid | ungeprüft |
| DOI:10.21203/rs.3.rs-831421/v1 |  | 1 | missing_pmcid | ungeprüft |
| PMID:32336042 | PMC7267628 | 1 | oa_not_confirmed | ungeprüft |
| PMID:32402155 | PMC7240771 | 1 | retrieved | ungeprüft |
| PMID:32408336 | PMC7616921 | 1 | oa_not_confirmed | ungeprüft |
| PMID:32591346 | PMC7780043 | 1 | retrieved | ungeprüft |
| PMID:33143316 | PMC7692688 | 1 | retrieved | ungeprüft |
| PMID:33155280 | PMC9619483 | 1 | http_500 | ungeprüft |
| PMID:33282147 | PMC7700767 | 1 | retrieved | ungeprüft |
| PMID:33300150 | PMC9619457 | 1 | http_500 | ungeprüft |
| PMID:33395484 | PMC7799041 | 1 | retrieved | ungeprüft |
| PMID:33685917 | PMC8139715 | 1 | retrieved | ungeprüft |
| PMID:33898942 | PMC8056843 | 1 | retrieved | ungeprüft |
| PMID:34094637 | PMC8139212 | 1 | retrieved | ungeprüft |
| PMID:34228902 | PMC8420455 | 1 | oa_not_confirmed | ungeprüft |
| PMID:34440669 | PMC8394956 | 1 | retrieved | ungeprüft |
| PMID:34467820 | PMC8721337 | 1 | retrieved | ungeprüft |
| PMID:34486072 | PMC8418960 | 1 | retrieved | ungeprüft |
| PMID:34935057 | PMC8722767 | 1 | retrieved | ungeprüft |
| PMID:35182354 | PMC8857399 | 1 | retrieved | ungeprüft |
| PMID:35313658 | PMC8925281 | 1 | retrieved | ungeprüft |
| PMID:35332140 | PMC8948269 | 1 | retrieved | ungeprüft |
| PMID:35336922 | PMC8955556 | 1 | retrieved | ungeprüft |
| PMID:35672403 | PMC9172986 | 1 | retrieved | ungeprüft |
| PMID:35858406 | PMC9335272 | 1 | retrieved | ungeprüft |
| PMID:36152751 | PMC9492400 | 1 | retrieved | ungeprüft |
| PMID:36225252 | PMC9550266 | 1 | retrieved | ungeprüft |
| PMID:36509737 | PMC9743116 | 1 | retrieved | ungeprüft |
| PMID:36815509 |  | 1 | missing_pmcid | ungeprüft |
| PMID:36830577 | PMC9953368 | 1 | retrieved | ungeprüft |
| PMID:36928633 | PMC10018580 | 1 | retrieved | ungeprüft |
| PMID:37724881 | PMC10779674 | 1 | retrieved | ungeprüft |
| PMID:37733584 |  | 1 | missing_pmcid | ungeprüft |
| PMID:37939376 |  | 1 | missing_pmcid | ungeprüft |
| PMID:38686388 | PMC11056506 | 1 | retrieved | ungeprüft |
| PMID:40303168 | PMC12017221 | 1 | retrieved | ungeprüft |
| PMID:41562775 | PMC12821584 | 1 | retrieved | ungeprüft |
| PMID:42090268 | PMC13167771 | 1 | retrieved | ungeprüft |
| PMID:42578668 | PMC13532326 | 1 | retrieved | ungeprüft |

## Reproduktion

Ab Projektverzeichnis:

```sh
python3 -B part1/task4/audit_sources.py --check part1/task4/audits/source-audit-20260923
```

Ein neuer Lauf benötigt mit `--out` ein noch nicht vorhandenes Verzeichnis. Das Skript nutzt nur die Python-Standardbibliothek, öffnet keine Netzwerkverbindung und liest keine Evaluationslabels. Hashes aller Quelldateien stehen in `audit.json`. Die Berichtserstellung ist LLM-unterstützt; sie ist kein menschlicher Goldstandard.
