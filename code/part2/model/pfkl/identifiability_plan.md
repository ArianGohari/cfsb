# Synthetische Parameterwiedergewinnung

11.10.2026, vor Ausführung. Methodenprüfung am bestehenden Zweizustandsmodell;
keine Anpassung an Aldehoff, Yang oder andere biologische Messungen.

## Frage und Voraussetzungen

Welche Parameter lassen sich bei bekanntem rechteckigem Eingriff getrennt
bestimmen? Unbekannt sind q, γ und ein Zeitfaktor β. Für eine beliebige,
bekannte Versuchsuhr s gilt τ = β s. Somit M' = β γ (1 − d M),
E' = β (k M − E). β ist eine Umparametrisierung der bisherigen relativen
Zeit, kein neuer biologischer Prozess. Ohne kalibrierte Versuchsuhr liefert
die Prüfung keine Rate pro Stunde.

Start M=E=1, Eingriff von s=0 bis 1, danach d=k=1. Währenddessen entweder
d=1/q, k=1 (Abbau) oder d=1, k=q (Translation). Der Mechanismus wird beim
Fit als bekannt vorausgesetzt. Keine Prüfung gemischter Mechanismen,
unbekannter Dosis, Eingriffsverzögerung oder Messskalierung.

Künstliche Wahrheit: q=0,5, γ=1, β=1. Optimierung positiver Parameter in
Log-Koordinaten, Grenzen q=0,05–1 und γ,β=0,05–20. Acht Startpunkte aus
q={0,2;0,8}, γ={0,25;4}, β={0,4;2,5}; keine empirischen Parameterbereiche.

## Vorab gewählte Beobachtungen

1. Abbau, nur Protein: s=0,1,4. Zwei informative Werte für drei Parameter.
2. Abbau, nur Protein: s=0;0,25;0,5;1;1,25;2;4;8.
3. Abbau, RNA und Protein zu denselben acht Zeitpunkten.
4. Translation, RNA und Protein zu denselben acht Zeitpunkten.

Diese Messpläne sind synthetisch. Die Dreipunktmessung ist keine Nachbildung
der SGBS-Differenzierung. Zusätzlich analytisch: Ein Gleichgewichtswert
enthält keine Rateninformation; bei reiner Translationshemmung bleibt M=1,
sodass γ in keiner beobachteten Kurve vorkommt.

## Auswertung und Grenzen

- Rauschfreie Wiedergewinnung mit allen acht Starts; Fehler zur bekannten
  Wahrheit und Residuen berichten. Mehrere Starts beweisen keine globale Eindeutigkeit.
- Ein fest gespeichertes, synthetisches Gaußrauschen mit σ=0,02 in normierten
  Einheiten (Seed 6517), ohne Abschneiden. Ein Beispiel, keine Erfolgsquote.
- Lokale Sensitivitätsmatrix nach Log-Parametern an der Wahrheit; SVD-Rang
  mit relativer Schwelle 10⁻⁷. Lokaler Rang ist kein globaler Beweis.
- Für jeden Messplan das rauschfreie γ-Profil: 31 logarithmische Werte von
  0,1 bis 10; q und β pro Punkt neu schätzen, vier Starts. Gewichtete
  Residuenquadratsumme mit σ=0,02 dient der Vergleichbarkeit, ohne CI-Schwelle.
- Analytische Phasenlösung unabhängig gegen direkte ODE-Integration und
  gespeicherte Catalyst-Kurven prüfen; Sonderfall γd=1 berücksichtigen.
- Deterministische Ausgaben, Originalwerte der synthetischen Beobachtungen,
  Startpunkte, Grenzen, Versionen, Herkunft und Fitstatus speichern.

Ergebnis bleibt auf diesen Eingriff, diese Wahrheit und bekannte Beobachtungsskalen
begrenzt. Ein guter synthetischer Fit bestätigt keine humane miRNA-Wirkung.
