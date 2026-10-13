# PFKL-Enzymmodul: vorab festgelegter Prüfplan

10.10.2026, vor der ersten Modellanpassung. Daten: Lynch 2024, DOI 10.1038/s41467-024-51808-6, Wildtyp-F6P-Reihe. 56 vorhandene Werte an neun Konzentrationen (0–4 mM), bei ATP 0,125 mM, pH 7,5, 25 °C. Wiederholungsspalten sind nicht sicher unabhängigen Proteinpräparationen zugeordnet.

## Modell und Anpassung

Physikalischer Enzymanteil: `v(S) = V * S^h / (K^h + S^h)`. Gemessenes Signal: `y(S) = b + v(S)`. Der konstante Hintergrund b gehört nur zur Beobachtung und darf keine Reaktion bei Nullsubstrat erzeugen. K ist die Konzentration halber maximaler Modellaktivität, kein elementarer Bindungsparameter.

Ungewichtete kleinste Quadrate auf allen vorhandenen Einzelwerten; fehlende Werte bleiben fehlend. Kein SEM-Gewicht, da 0,25 mM nur eine Messung besitzt. Gleiche Varianz der Residuen ist eine Arbeitsannahme, keine gesicherte Eigenschaft. Keine inferentiellen Parameter-Konfidenzintervalle aus 56 vermeintlich unabhängigen Experimenten.

Positive Parameter über begrenzte Optimierung: b 0–20 U/mg, V 0,001–1000 U/mg, K 0,001–100 mM, h 0,1–10. Grenzen sind numerische Suchgrenzen, keine biologischen Priorintervalle. Deterministische Starts: V 10, b 0,2, K aus 1/2/4 und h aus 1/3. Gültige Konvergenz, Zielwertstreuung und Grenztreffer protokollieren.

Vergleich: Michaelis-Menten als einfacheres Modell mit h=1 und gleichem Hintergrund. Konstante Trainingsmittelwerte als triviale Vorhersagereferenz. Keine nachträgliche Modellauswahl anhand einzelner günstiger Konzentrationen.

## Interne Prüfung

Jede der neun Konzentrationen einmal vollständig zurückhalten, auf den übrigen Konzentrationen anpassen. Zurückgehaltene Werte dürfen weder zur Hintergrundbestimmung noch zur Startwertwahl dienen. Alle Folds berichten; 0 und 4 mM getrennt als Randvorhersagen, sieben innere Stufen als Interpolation. RMSE auf Einzelwerten und gleichgewichteten Konzentrationsmitteln sowie MAE berichten. Keine externe Validierung, da dieselbe Studie und teils dieselben Messreihen.

Sensitivität: sieben Anpassungen mit jeweils einer ausgelassenen Originalspalte (B:H), ohne diese als sieben unabhängige Proteinpräparationen zu deklarieren. Parameter-Min/Max sind Empfindlichkeitsbereiche, keine Konfidenzintervalle. Zusätzlich Hintergrund auf null fixieren, um dessen Einfluss zu zeigen. Die Hauptanalyse behält alle Nullsubstratwerte, einschließlich des auffälligen Werts C10; kein unbegründeter Ausschluss.

Die ATP-Reihe bleibt außerhalb der Anpassung: Ihr Hemmungsverlauf liegt außerhalb des Modells mit festem ATP. Literaturparameter dienen erst nach der eigenen Anpassung dem Vergleich, nicht als Zielwerte oder zusätzliche Trainingsdaten. Modell kann keine humane miRNA-Hemmstärke, Enzymkonzentration in Fettzellen oder Zellzeitkonstanten bestimmen.

## Ergänzende numerische Prüfung nach der ersten Anpassung

Michaelis-Menten erreicht die obere K-Grenze und approximiert damit eine nahezu lineare Antwort. Deshalb zusätzlich zehnfach höhere Obergrenzen für K (1000 mM) und V (10000 U/mg) prüfen, einschließlich aller ausgelassenen Konzentrationen. Diese nachträgliche Sensitivitätsprüfung ersetzt die vorab festgelegten Ergebnisse nicht; die großen Werte werden nicht als Enzymparameter interpretiert.
