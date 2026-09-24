# Aufgabe 1(b): Netzwerkmodelle, dynamische Modelle und widersprüchliche Hypothesen

Grundlage: Zou et al. (2020), *A Systems Biology Approach Identifies Hidden Regulatory Connections Between the Circadian and Cell-Cycle Checkpoints*. DOI: [10.3389/fphys.2020.00327](https://doi.org/10.3389/fphys.2020.00327). [Lokaler Volltext](sources/markdown/zou_2020_circadian_cell_cycle_checkpoints/zou_2020_circadian_cell_cycle_checkpoints.md).

Die folgende Diskussion beschränkt sich auf den Review. Experimentelle Ergebnisse und Modellrechnungen werden nach dessen Darstellung wiedergegeben; eigene Simulationen oder eine unabhängige Prüfung sämtlicher Originalarbeiten wurden nicht durchgeführt. Der Vergleich der vorgegebenen Quelle ist keine abgeschlossene systematische Literaturrecherche.

## Vergleich der Modelle

Zou et al. behandeln die Kopplung der circadianen Uhr mit Zellzyklus-Checkpoints auf unterschiedlichen Beschreibungsebenen. Ein Netzwerkdiagramm zeigt biologische Beziehungen; dynamische Modelle prüfen, ob bestimmte Annahmen auch die beobachteten zeitlichen Verläufe erklären können.

| Modell / Darstellung | Aufbau und Annahmen | Aussagekraft | Grenzen |
|---|---|---|---|
| Qualitatives PER2–p53–MDM2-Netzwerk, Abb. 2 | Verknüpft PER2-vermittelten p53-Schutz und Kerntransport mit der Freisetzung transkriptionsfähigen p53 sowie MDM2-vermitteltem PER2-Abbau. | Zeigt die bidirektionale Verbindung zwischen Uhr und Checkpoint: Uhrkomponenten beeinflussen p53, und MDM2 wirkt auf PER2 und damit auf die Uhr zurück. | Die Abbildung allein enthält keine vollständige Parametrisierung. Aus den Pfeilen lassen sich keine eindeutigen Konzentrationskurven, Phasenverschiebungen oder Periodenlängen berechnen. |
| Kim–Forger-Uhrmodell als Eingang des vereinfachten p53-Modells | Liefert simulierte circadiane PER-Verläufe im Cytoplasma und Kern. | Stellt die zeitabhängige Eingangsgröße bereit, mit der unterschiedliche PER2-Einflüsse auf p53 untersucht werden. | Diese Verwendung prüft die p53-Antwort auf vorgegebene Uhrverläufe; sie stellt für sich genommen keine vollständige bidirektionale Kopplung des Netzwerks aus Abb. 2 dar. |
| Vereinfachtes p53-Modell, Gl. 1–2 und Abb. 1C–F | Zwei Differentialgleichungen beschreiben p53 in Cytoplasma und Kern. Fünf Funktionen stehen für Synthese, Kernimport, Kernexport und Abbau in beiden Kompartimenten. Für jeden Prozess werden positive, negative oder fehlende PER2-Regulation sowie passende Parameter untersucht. | Prüft konkurrierende Regulationsszenarien. Unter den erfolgreichen Varianten ist PER2-geförderter Kernimport stark bevorzugt; außerdem wird eine höhere p53-Stabilität im Kern vorhergesagt. | Fasst viele molekulare Vorgänge zu effektiven Raten zusammen. Es beschreibt, welche Prozesse erforderlich erscheinen, ohne deren molekularen Ablauf eindeutig festzulegen. |
| Verfeinertes mechanistisches Modell, Abb. 1G und Modellierungsabschnitt | Laut Review 13 Differentialgleichungen und 18 Parameter. Enthält PER-Rückkopplung, PER2–p53-Bindung und verschiedene Ubiquitinierungszustände. Angenommen wird, dass PER2 den Kernimport durch Schutz vor Ubiquitinierung im Importmotiv fördert und cytoplasmatisches monoubiquitiniertes p53 durch Polyubiquitinierung instabil wird. | Verknüpft die Phasenbeziehungen mit konkreten molekularen Mechanismen. Liefert die zusätzliche Vorhersage, dass PER2 auch an ubiquitiniertes p53 bindet. | Zusätzliche Details benötigen zusätzliche Annahmen und Parameter. Die vollständigen Gleichungen werden in der zitierten Originalarbeit beschrieben; eine passende Simulation beweist keine einzigartige Modellstruktur. |

Das vereinfachte und das verfeinerte Modell bauen aufeinander auf. Ihre unterschiedliche Detailtiefe ist kein Widerspruch. Auch das Netzwerk in Abb. 2 darf nicht ohne Weiteres mit dem vollständig implementierten Reaktionsumfang des verfeinerten ODE-Modells gleichgesetzt werden.

## Conflicting hypotheses

### Stabilisierung und gegenphasige Oszillation

Der zentrale scheinbare Widerspruch entsteht aus dem Befund, dass PER2 p53 vor MDM2-vermittelter Ubiquitinierung und Abbau schützt. Daraus leiten die Autoren zunächst die Erwartung ab, dass PER2 und p53 gleichphasig oszillieren. Die berichteten Messungen zeigen jedoch weitgehend gegenphasige Verläufe im Cytoplasma und Gesamtlysat, während beide Proteine im Kern gleichphasig verlaufen (Abb. 1A–C).

Damit ist die einfache Phasenvorhersage unzureichend. Der Stabilisierungseffekt selbst wird nicht widerlegt. Ein Modell mit getrennten Kompartimenten berücksichtigt, dass p53-Mengen sowohl vom Transport als auch vom lokalen Abbau abhängen. PER2-geförderter Kernimport und höhere nukleäre Stabilität können deshalb die unterschiedlichen Phasenbeziehungen erklären.

### Konkurrierende Regulationsvarianten

Im vereinfachten Modell konkurrieren positive, negative und fehlende PER2-Einflüsse auf die fünf betrachteten Prozesse. Von ungefähr einer Million simulierten Szenarien reproduzieren laut Review 1.000 die gesuchten Phasenbeziehungen. Erfolgreiche Modelle bevorzugen positiven Kernimport und eine höhere p53-Stabilität im Kern (Abb. 1D–F). Daraus folgt eine Auswahl plausibler Mechanismen, aber keine eindeutige Festlegung aller Regulationsfunktionen.

Die berichteten Experimente stützen diese Vorhersagen: PER2-Manipulation verändert die nukleäre p53-Anreicherung, und die nukleäre p53-Halbwertszeit ist ungefähr siebenmal länger als die cytoplasmatische. Nach PER2-Absenkung bleibt allerdings p53 im Kern nachweisbar. PER2 trägt daher zum Transport bei; weitere Wege bleiben möglich (Abschnitt "From in silico Prediction to in vitro Validation").

### Weitere scheinbare Gegensätze

| Gegenüberstellung | Einordnung anhand des Reviews |
|---|---|
| PER2 verhindert p53-Ubiquitinierung, bindet aber auch ubiquitiniertes p53. | Schutz vor weiterer Modifikation und Bindung an bereits modifiziertes Protein schließen sich nicht aus. Das verfeinerte Modell sagt Bindung unabhängig vom Ubiquitinierungsstatus voraus; Proteinassays zeigen Bindung an mono- und polyubiquitiniertes p53 (Abb. 1G, Prediction 3). Eine Beschränkung auf unmodifiziertes p53 wäre eine zusätzliche, nicht aus dem Schutzbefund ableitbare Annahme. |
| PER2 stabilisiert p53, hemmt aber dessen Transkriptionsaktivität im gebundenen Zustand. | Stabilität und Aktivität sind unterschiedliche Eigenschaften. Ein stabiler gebundener Vorrat kann zunächst inaktiv sein. Der Review beschreibt die Freisetzung von PER2 als Voraussetzung für p53-Aktivierung; dauerhaft gekoppelte Chimären unterstützen diese Unterscheidung ("Coupling Between..."; Abb. 2, Knoten 1 und 3). |
| PER2-Abbau über CK1/β-TrCP gegenüber PER2-Abbau über MDM2. | Der klassische β-TrCP-Weg setzt PER2-Phosphorylierung voraus, der beschriebene MDM2-Weg nicht. Dies widerspricht einer ausschließlich phosphorylierungsabhängigen Beschreibung des gesamten PER2-Abbaus. Die beiden Wege selbst sind jedoch miteinander vereinbar und können nebeneinander wirken ("A Bidirectional Relationship Between Clock and Checkpoint Components"). |

Diese Gegenüberstellungen sind nicht durchweg konkurrierende, von verschiedenen Autoren vertretene Theorien. Teilweise handelt es sich um zu einfache Schlussfolgerungen, die durch zusätzliche Zustände oder Prozesse präzisiert werden müssen.

## Bewertung

Die Modelle zeigen, wie räumliche Verteilung, Bindungszustand und Ubiquitinierung scheinbar widersprüchliche Beobachtungen miteinander vereinbar machen. Entscheidend sind die zusätzlichen experimentellen Prüfungen der Modellvorhersagen. Die Übereinstimmung simulierter und gemessener Phasen allein genügt nicht als Mechanismusbeweis: Mehrere Modellvarianten können dieselben Beobachtungen erklären, und der Review bezeichnet die verfügbaren Zeitreihen ausdrücklich als unzureichend für eine eindeutige Bestimmung des Systems.

Auch "unbiased" bedeutet hier nur, dass die vorgegebenen positiven, negativen und fehlenden Regulationstypen zunächst gleichberechtigt ausgewählt werden. Die Wahl der Prozesse, Kompartimente und Funktionsformen bleibt eine Modellannahme. Die Befunde stützen somit bestimmte Mechanismen unter den untersuchten Bedingungen, ohne alle Alternativen auszuschließen oder eine Gültigkeit für sämtliche Zelltypen zu belegen.
