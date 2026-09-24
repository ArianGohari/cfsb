# Gezielter Volltext-Nachtrag: Plan vor Abruf

2026-09-20. Nur followup/ schreiben; bestehende Rohdaten und Abstract-Auswertung unverändert erhalten. Maximal zwölf neue HTTP-Anfragen einschließlich etwaiger Weiterleitungen, keine Retries. Keine Zugangsdaten, Paywall- oder Sperrumgehung. Öffentliche Europe-PMC-/PMC-APIs.

Priorität: Gaddameedhi2012 (PMID 22918252, PMC3466558), Gauger2005 (16061665, bisher keine PMCID), Ozturk2009 (19188586, PMC2634797), danach Gery2007 (17332281, bisher keine PMCID) und Dickmeis2007 (17373855, PMC1828142). Identitäten stammen aus vorhandenen Europe-PMC-Rohantworten.

Geplanter Abruf: drei Europe-PMC fullTextXML-Abfragen für bekannte PMCIDs; eine gebündelte öffentliche PMC-ID-Converter-Abfrage für Gauger/Gery. Bei neu ermittelter PMCID je ein fullTextXML-Abruf. Falls Europe PMC nur fehlende XML-Verfügbarkeit meldet, darf pro zugänglichem PMC-Artikel der öffentliche PMC-BioC-API-Endpunkt einmal geprüft werden (separater regulärer Bereitstellungsweg, keine Umgehung einer Zugriffssperre). Bei 401/403/429 oder anderer expliziter Zugriffssperre keine alternative Beschaffung desselben Texts. Maximal zwölf Anfragen, ungenutztes Budget verfällt. Kein Verlagsabruf. Fehlende PMCID ist eine Beschaffungslücke, kein fachlicher Ausschluss.

Pro Anfrage: URL, UTC-Anfang/-Ende, HTTP-Status, Fehlertext, unveränderte Antwortbytes, SHA256 und Byteumfang in fulltext_raw/. Weiterleitungen werden nicht automatisch verfolgt. Alte raw/-Dateien vorab hashen und offline auf Unverändertheit prüfen. HTML/Fehlerseiten nie als Volltext ausgeben.

Auswertung: Artikelidentität prüfen, Haupttext mit Methoden, Resultaten, Abbildungslegenden und Diskussion lesen; heruntergeladene Textversion und nicht abgerufene Supplemente benennen. Kurze Zitate mit Abschnitt/Absatz und Quelle. Spezifische Behauptung, Organismus/Zelllinie, Allel, Hintergrund, Stress/Dosis, Endpunkte und Grenzen getrennt dokumentieren. Unabhängigkeit anhand Autorengruppen vorsichtig bewerten; Zitation allein reicht nicht. Die chronologisch widersprüchliche OpenAlex-Kante wird nicht verwendet.

Planergänzung nach sechs Anfragen, vor weiterem Abruf: Europe PMC meldete für Gaddameedhi/Ozturk HTTP 500, BioC HTTP 200 mit "No result can be found" (OA-Subset). Keine Zugriffssperre. Eine siebte, gebündelte öffentliche EFetch-Abfrage (db=pmc, beide IDs) prüft die reguläre PMC-XML-Bereitstellung außerhalb des BioC-OA-Subsets. Keine weiteren Endpunktversuche danach. Gauger/Gery: ID-Converter meldet "Identifier not found in PMC"; kein Verlagszugriff.

Ergebnis fulltext_review.md: gezielte Aussageprüfung für Aufgabe 1(d), keine Vollständigkeit oder abschließende historische Priorität behaupten. Exakte Replikation nur bei passendem Design; anderer Kontext nicht als Widerlegung des ursprünglichen Experiments darstellen. Offline-Verifikation von Hashes, Identitäten und Zitaten mit Python-Standardbibliothek, Befehle und Exitcodes dokumentieren.
