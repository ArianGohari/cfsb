# Früherer LLM-Entwurf

Historischer Entwurf für Aufgabe 1(g). Der aktuelle Standard arbeitet regelbasiert; [Befehle und Grenzen](../README.md).

![Geplanter Ablauf](diagrams/v1.svg)

Der Entwurf trennt Suche, Abstract-Screening, Volltextprüfung, Entity-Normalisierung, Relationsextraktion und Export. LLM-Schritte liefern strukturierte Antworten; Python prüft Identifier, Typen und wörtliche Belege. Unklare Fälle bleiben offen. Ko-Erwähnung allein ergibt keine Relation.

## Datenmodell

![Graphschema](diagrams/graph_schema.svg)

Fünf Tabellen: `papers`, `documents`, `entities`, `relations`, `evidence`. Evidence verknüpft eine Relation mit ihrer Textstelle. Dokumentoffsets zählen Unicode-Zeichen als halboffenes Intervall; `text[start:end]` muss dem Zitat entsprechen.

Kontext, Attribution und Prüfstatus werden getrennt gespeichert. `auto_pass` bedeutet bestandene technische Prüfung, keine fachliche Bestätigung. Reviews und mehrfach extrahierte Stellen zählen nicht als unabhängige Experimente.

## Nachvollziehbarkeit

Suchantworten, Entscheidungen, Originaltexte, Modellantworten, Konfiguration und Prüfsummen sollten ein Offline-Replay ermöglichen. Neue LLM-Aufrufe können andere Ergebnisse liefern. Zugriffslücken, begrenzte Suchbudgets und Enthaltungen müssen sichtbar bleiben.

[PRISMA-Unterlagen](prisma/README.md), [Protokoll](prisma/protocol.md) und [Zählregeln](prisma/tracking.md) dokumentieren die damalige Planung. Sie belegen keine abgeschlossene systematische Review. Fachliche Extraktionsqualität benötigt einen unabhängigen Goldstandard.

Diagramme ab Projektwurzel rendern:

```sh
dot -Tsvg code/text_mining/docs/diagrams/v1.dot -o code/text_mining/docs/diagrams/v1.svg
dot -Tsvg code/text_mining/docs/diagrams/graph_schema.dot -o code/text_mining/docs/diagrams/graph_schema.svg
```
