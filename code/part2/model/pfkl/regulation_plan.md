# Bedingte miR-6517/PFKL-Regulation

10.10.2026, vor Simulation. Frage: Können zwei angenommene Wirkwege denselben langfristigen Proteinwert, aber unterschiedliche Antworten auf einen begrenzten Eingriff erzeugen?

## Modell und Voraussetzungen

M = PFKL-mRNA relativ zum ungestörten Gleichgewicht, E = PFKL-Protein relativ dazu. Start M=E=1. Zeit τ=δP·t; δP unbekannt. Kein Bezug zu Stunden, Milchmengen oder gemessenen intrazellulären miRNA-Mengen. Der externe rechteckige Eingriff stellt eine angenommene, sofort ein-/ausschaltbare wirksame Hemmung dar. Aufnahme, RISC-Beladung und miRNA-Abbau sind nicht modelliert.

Kontinuierliches Petrinetz: ∅→M, M→∅, M→M+E, E→∅. Raten γ, γ·d·M, k·M, E. γ=δM/δP ist das unbekannte Verhältnis ungestörter Abbauraten. Daraus dM/dτ=γ(1−dM), dE/dτ=kM−E. Transkription, lineare Abbauraten, fehlende Rückkopplung und konstante Zellbedingungen sind Annahmen.

Während des Eingriffs zwei Grenzfälle:

- mRNA-Abbau: d=1/q, k=1.
- Translation: d=1, k=q.

Außerhalb: d=k=1. q ist der angenommene stationäre Proteinrestwert bei dauerhafter Hemmung. Kein Dosisparameter: q∈{0,25; 0,5; 0,75; 1}. q=1 schaltet die humane Hemmkante aus. Beide Varianten haben E∞=q; mRNA unterscheidet sich (q bzw. 1). Reine Translation ist ein Mechanismusvergleich, nicht die beste Erklärung von Yangs bovinem qPCR-Befund. Guo 2010 begründet die Mechanismusklassen allgemein, nicht deren Gültigkeit für humane miR-6517/PFKL. Gemischte Mechanismen bleiben möglich.

γ∈{0,25;1;4}; Eingriffsdauer L∈{0,25;1;4} in τ-Einheiten. Diese Rasterwerte sind Annahmen ohne Wahrscheinlichkeiten oder Konfidenzniveau. Kein Parameterschätzer wird eingesetzt.

## Kopplung an das Enzymmodul

Bei festem F6P, ATP und unverändertem Aktivierungszustand skaliert der PFKL-Zweig mit E. Mit unbeeinflusstem anderem Beitrag f ergibt sich relative Aktivität f+(1−f)E. f=0/0,5/0,9 sind bestehende Szenarien; keine Kompensation. Die Lynch-Kurve liefert den gemeinsamen Substrateingang und kürzt sich im Verhältnis heraus. Es werden daher keine neuen absoluten Zellflusswerte berechnet. Kein dynamischer geschlossener Substratpool wird mit diesen Kurven gekoppelt.

## Prüfungen vor Interpretation

Catalyst-Lösung gegen geschlossene Lösung der linearen Gleichungen für jede Phase prüfen, einschließlich γd=1. Phasen getrennt integrieren, Zustände beim Umschalten kontinuierlich übergeben. Nullhypothese q=1 bleibt bei M=E=1; Positivität/obere Schranke 1; Erholung zur Baseline. Stationäre Zustände unabhängig in die erzeugte RHS einsetzen. An ausgewählten Fällen engere Solvertoleranzen prüfen. Finale Ausgaben mit gleichem Code erneut erzeugen und Hashes vergleichen. Technische Prüfungen sind keine biologische Validierung.

Berichten: Proteinrestwert am Ende des Eingriffs und gegebenenfalls späteres Minimum. Keine Rangfolge der biologischen Mechanismen aus einer konstruierten Simulation ableiten. Den gemeinsamen stationären Wert ausdrücklich als konstruierten Vergleich benennen. Zeitreihen von mRNA und Protein wären nötig, um die Mechanismen im passenden humanen Zellkontext zu unterscheiden.
