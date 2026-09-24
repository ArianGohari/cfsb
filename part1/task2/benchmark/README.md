# Reproduktionsbenchmark für Aufgabe 2

Dieser Ordner enthält einen kleinen, neu ausgeführten Ausschnitt aus der
Therapieoptimierung von Schmucker et al. (2021). Der Lauf verwendet das von den
Autoren verlinkte Pan-Cancer-Modell, das K029AX-Expressionsprofil und die
veröffentlichte CMA-ES-Struktur. Drei Seeds werden für 60 Iterationen bei
$\lambda=10^{-5}$ und $L_1$-Regularisierung ausgewertet.

Die historische Python-Umgebung baut auf Apple Silicon mit Python 3.12 nicht
mehr. `build_model.py` überträgt den Modellimport deshalb auf AMICI 1.1.0. Es
ändert weder SBML-Datei noch Parameter oder Expressionswerte. Der Build erzeugt
keinen Sensitivitätscode, da die Konzentrationsoptimierung nur Vorwärtssimulationen
benötigt.

## Neu ausführen

Vorausgesetzt werden `uv`, ein C++-Compiler, CMake und eine Internetverbindung
für den ersten Download. Im Projektstamm genügt:

```sh
sh part1/task2/benchmark/run_all.sh
```

Der erste Modellbau dauert auf einem M4 Pro ungefähr 67 Sekunden. Der
Benchmark braucht weitere zwei Minuten. Spätere Läufe verwenden das kompilierte
Modell aus `.amici_model/` erneut. Quellarchive, virtuelle Umgebung und
Kompilat werden nicht versioniert; Commit-IDs, Paketlock und Prüfsummen sind
versioniert.

## Dateien

`fetch_upstream.py` lädt die beiden fixierten GitHub-Snapshots und prüft ihre
SHA-256-Summen. `build_model.py` kompiliert das SBML-Modell. Der eigentliche
Versuch steht in `run_benchmark.py`; `test_results.py` kontrolliert anschließend
Quellidentität, Dimensionen, Call-Zahl, monotone Bestwerte und die Zielfunktion.

Die Rohspur liegt in `results/convergence.csv`, die drei Endpunkte in
`results/seed_summary.csv`. `results/benchmark.json` enthält Laufzeit,
Nullkontrolle und Gewinner. `results/build_metadata.json` protokolliert Modell
und Umgebung. Die Abbildung wird als SVG und PNG erzeugt.

Das Audit in [`audit/README.md`](audit/README.md) grenzt diesen Lauf von den
publizierten Benchmarks ab.

