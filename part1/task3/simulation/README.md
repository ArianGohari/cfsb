# Numerische Ergänzung zu Aufgabe 3

Die [Ausarbeitung](../task3.html) enthält Simulationen der unveränderten archivierten SBML-Modelle BIOMD0000000170 und BIOMD0000001006. Ergebnisse und Semantikexporte stehen unter `results-20260924/`. Die Eingaben einschließlich SHA-256 stehen unter `inputs/`.

Ab Projektwurzel:

```sh
uv sync --project part1/task3/simulation --locked --python 3.12 --no-build
uv run --project part1/task3/simulation --locked python part1/task3/simulation/simulate.py
uv run --project part1/task3/simulation --locked python -m unittest discover -s part1/task3/simulation -p 'test_*.py' -v
uv run --project part1/task3/simulation --locked python part1/task3/simulation/verify_reproduction.py
python3 part1/task3/simulation/render_standalone.py
```

`simulate.py --output NEUER_ORDNER` schreibt eine weitere Ergebnisfassung. Die Standardbefehle verwenden ausschließlich lokale Eingaben; nur die erste Paketinstallation benötigt Internet. Die Ausgabeintervalle und Solvertoleranzen sind numerische Auswerteentscheidungen. Biologische Parameter werden nicht verändert.

Das p53-Modell enthält einen verzögerten Einschaltvorgang: Trigger `time > 10`, Verzögerung 2, anschließend `step = 1`; Ausschalten nach `time > 20`. Die Achse bleibt die SBML-Zeitachse. Die dokumentierten Warnungen über unvollständige Einheiten bleiben bestehen.
