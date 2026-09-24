# Audit des Aufgabe-2-Benchmarks

Stand: 24. September 2026

## Was tatsächlich ausgeführt wurde

Der Lauf kompiliert die SBML-Datei aus `FFroehlich/reference_simulator` und
setzt die feste Bedingungszeile `TUMOR-K029AX-cellline-01-01`. AMICI integriert
1.228 Zustände bis zum stationären Zustand. Drei CMA-ES-Läufe mit je 60
Iterationen und neun Kandidaten erzeugen 1.620 Optimierungsauswertungen. Dazu
kommen die unbehandelte Kontrolle und der gleich verteilte Startpunkt.

Die beste Zielfunktion beträgt 0,1358591818 bei 4.522,15 nM Gesamtdosis und
relativer Proliferation 0,0906377027. Sie stammt von Seed 89. Der Lauf misst
eine gesamte Modellzeit von 114,81 s und eine Wandzeit von 116,36 s auf einem
Apple M4 Pro. Diese Messwerte gehören nur zu diesem Rechner und AMICI 1.1.0.

## Abgrenzung von den Veröffentlichungen

Fröhlich et al. messen Gradienten für eine Parameterschätzung mit mehr als
4.100 Parametern. Der hier ausgeführte Lauf schätzt diese Parameter nicht neu.
Er übernimmt den veröffentlichten Parametersatz und optimiert sieben
Wirkstoffkonzentrationen. Der Faktor größer als 37.000 bleibt deshalb eine
Literaturangabe aus dem Sparse-Adjoint-Vergleich der Autoren.

Schmucker et al. rechnen 400 Iterationen, drei Seeds, ein Raster von
$\lambda=10^{-7}$ bis $10^{-1}$, mehrere Zelllinien und drei Strafen. Sie
vergleichen außerdem gegen Einzelwirkstoffe und eine RAF/MEK-Kombination. Der
vorliegende Lauf beschränkt sich auf K029AX, $\lambda=10^{-5}$,
$L_1$-Regularisierung und 60 Iterationen. Er reproduziert den Rechenweg, nicht
die vollständige Abbildungsserie.

## Konkreter Blocker der historischen Umgebung

Das offizielle Repository fixiert `amici==0.10.13`, `petab==0.0.0a16`,
`numpy==1.22.0` und `pandas==0.25.3`. Der isolierte Installationsversuch mit
Python 3.12.8 endet bereits beim Bau von AMICI 0.10.13 mit:

```text
Failed to build `amici==0.10.13`
Failed trying to install numpy. Please install manually.
```

Der Port nutzt AMICI 1.1.0 mit Python 3.12.8. Die neue API verwendet
`assignment_rules_to_observables`, `fixed_parameters`, `observation_model` und
`model.simulate()`. Der Modellinhalt stammt unverändert aus dem fixierten
Referenz-Commit.

## Offene Reproduzierbarkeitsgrenzen

Die SBML-Datei im verlinkten Referenz-Commit enthält 2.686 Reaktionen. Schmucker
et al. schreiben 2.704. Im Repository fehlt eine versionierte Datei, die diese
Differenz erklärt. Der eigene Benchmark berichtet daher die gezählte Zahl.

Eine Vorhersagegüte gegen Messwerte wurde nicht berechnet. Der verwendete
Optimierungsdatensatz enthält Zelllinienbedingungen und Modellparameter, aber
keine unabhängigen beobachteten K029AX-Kombinationswerte für die gefundenen
Cocktails. Relative Proliferation ist hier Modelloutput.

