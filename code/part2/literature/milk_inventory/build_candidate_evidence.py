"""Join existing milk, annotation and target evidence without promoting hypotheses.

Source notes own target curation. Historical tables and the 270-sequence
inventory remain unchanged. Ali is a separate provisional reference layer.
"""

from pathlib import Path
from collections import defaultdict, Counter
import csv, hashlib, json, os
from urllib.parse import quote
import yaml

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / "output/part2/milk_inventory"
OUT = BASE / "candidate_evidence"
NOTES = ROOT / "obsidian/Projekt/Literatur/04 Datenextraktion/Quellen"
CURATION = (
    ROOT
    / "obsidian/Projekt/Literatur/05 Evidenzbewertung und Synthese/Targetvergleich aller 16 Kandidaten.md"
)
LABELS = {
    "exact_human_sequence": "Identisch human",
    "human_seed_only": "Nur gleicher Seed",
    "no_human_seed_match": "Kein humaner Seedtreffer",
    "unresolved": "Sequenz offen",
}
ANNOTATIONS = {
    "exact_sequence": "MirGeneDB: exakte Sequenz",
    "accession_with_sequence_difference": "MirGeneDB: abweichende Endvariante",
    "no_accession_or_exact_sequence_match": "Kein passender MirGeneDB-Eintrag",
}


def read(p):
    with p.open() as f:
        return list(csv.DictReader(f, delimiter="\t"))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(name, rows):
    with (OUT / name).open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        w.writeheader()
        w.writerows(rows)


def link(p, label):
    return "[" + label + "](" + quote(os.path.relpath(p, OUT), safe="/") + ")"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = [
        BASE / "human_comparison/all_sequences.tsv",
        BASE / "paper_support/source_evidence.tsv",
        BASE / "annotation_audit/candidates.tsv",
        BASE / "human_seed_screen/literature_pairs.tsv",
        BASE / "human_seed_screen/candidate_summary.tsv",
        BASE / "published_lists/ali_reference_comparison.tsv",
        CURATION,
    ]
    baseline = read(inputs[0])
    milk = read(inputs[1])
    annotation = read(inputs[2])
    pairs = {(r["candidate"], r["gene"]): r for r in read(inputs[3])}
    seed_by_seq = {
        r["sequence_RNA"]: r
        for r in read(inputs[4])
        if r["variant"] == "inventory_reference"
    }
    ali = read(inputs[5])
    byseq = {}
    milk_rows = []
    target_rows = []
    annotation_by_seq = {r["sequence_RNA"]: r for r in annotation}
    curation_rows = [
        [s.strip() for s in l.strip("|").split("|")]
        for l in CURATION.read_text().splitlines()
        if l.startswith("|")
    ][2:]
    literature = {
        r[0]: dict(zip(["approach", "level", "limits"], r[1:])) for r in curation_rows
    }
    assert len(literature) == 16
    for r in baseline:
        seq = r["sequence_RNA"]
        byseq[seq] = {
            "names": set(r["miRNA_names"].split(";")),
            "baseline": r,
            "ali": [],
        }
    for r in ali:
        seq = r["reference_sequence"]
        key = seq or "unresolved:" + r["accession"]
        byseq.setdefault(key, {"names": set(), "baseline": None, "ali": []})
        byseq[key]["names"].add(r["original_name"])
        byseq[key]["ali"].append(r)
    for r in milk:
        milk_rows.append(
            dict(
                candidate_id="seq:"
                + hashlib.sha256(r["sequence_RNA"].encode()).hexdigest()[:16],
                study=r["study"],
                doi=r["doi"],
                original_name=r["original_name"],
                evidence_status="Qualifizierender Beleg im Basisbestand",
                source_path=r["source_path"],
                locator=r["source_sheet"] + ": Zeile " + r["source_row"],
                material=r["qualified_materials"],
                support=r["replicate_support"],
                reference_origin=r["sequence_origin"],
            )
        )
    for r in ali:
        key = r["reference_sequence"] or "unresolved:" + r["accession"]
        milk_rows.append(
            dict(
                candidate_id="seq:" + hashlib.sha256(key.encode()).hexdigest()[:16],
                study="ali2026",
                doi="10.1016/j.idairyj.2025.106422",
                original_name=r["original_name"],
                evidence_status="Sequenz offen"
                if not r["reference_sequence"]
                else "Vorläufig >1 Read"
                if r["strict_gt1"] == "True"
                else "Nur 1 Read",
                source_path="data/sources/ali_2026_infant_formula_mirnas/ali_2026_infant_formula_mirnas.pdf",
                locator="Tabelle 3; PDF S. " + r["pdf_page"],
                material="Kuhbasierte Formelnahrung; gemeinsame Ergebnistabelle",
                support=r["reads"] + " Reads",
                reference_origin="23.1-Accessionzuordnung; Studie verwendete 22.1",
            )
        )
    for p in sorted(NOTES.glob("*.md")):
        props = yaml.safe_load(p.read_text().split("\n---\n", 1)[0][4:])
        for e in props.get("Targetbefunde", []):
            inputs.append(p)
            pair = pairs.get((e["Kandidat"], e["Target"]))
            if pair:
                human_site = (
                    pair["site_types"]
                    + "; "
                    + pair["transcripts_with_sites"]
                    + "/"
                    + pair["eligible_transcripts"]
                    + " untersuchte Transkripte"
                    if pair["status"] == "canonical_site_found"
                    else "Keine definierte Stelle in "
                    + pair["eligible_transcripts"]
                    + " untersuchten 3′UTRs"
                )
            else:
                human_site = "Nicht geprüft; außerhalb bisheriger 3′UTR-Suche"
            target_rows.append(
                dict(
                    candidate=e["Kandidat"],
                    sequence_RNA=e["Inventarsequenz"],
                    target=e["Target"],
                    doi=props["DOI"],
                    evidence=e["Evidenz"],
                    experimental_context=e["Versuchskontext"],
                    pathway_or_context=e["Pathway oder Kontext"],
                    locator=e["Fundstelle"],
                    human_site=human_site,
                    human_transfer=e["Humane Übertragung"],
                    open_question=e["Offene Prüfung"],
                    source_note=str(p.relative_to(ROOT)),
                    pair_scope="Gültig nur für getestete GENCODE-48-basic-CHR-3′UTRs; Treffer belegt keine Repression",
                )
            )
    targets_by_seq = defaultdict(list)
    for e in target_rows:
        targets_by_seq[e["sequence_RNA"]].append(e)
    rows = []
    for seq, d in sorted(
        byseq.items(), key=lambda kv: (";".join(sorted(kv[1]["names"])), kv[0])
    ):
        b = d["baseline"]
        a = d["ali"]
        ann = annotation_by_seq.get(seq)
        edges = targets_by_seq[seq]
        names = sorted(d["names"])
        seed = seed_by_seq.get(seq)
        cls = b["human_class"] if b else a[0]["human_class"]
        if b and a:
            assert all(x["human_class"] == cls for x in a)
        cur = literature.get(ann["candidate"].removeprefix("bta-")) if ann else None
        cohort = (
            "Basisbestand"
            if b
            else "Ali: Sequenz offen"
            if seq.startswith("unresolved:")
            else "Ali: vorläufig >1 Read"
            if any(x["strict_gt1"] == "True" for x in a)
            else "Ali: nur ein Read"
        )
        flags = [b["review_flags"]] if b and b["review_flags"] else []
        if a:
            flags.append(
                "Ali: Referenz 23.1 statt 22.1; Aggregation und Zählwidersprüche offen"
            )
        if any(x["different_sequence_under_same_name"] == "True" for x in a):
            flags.append(
                "Gleicher Name im Basisbestand, aber andere Sequenz; Targetbefunde nicht per Name übertragen"
            )
        rows.append(
            dict(
                candidate_id="seq:" + hashlib.sha256(seq.encode()).hexdigest()[:16],
                names=";".join(names),
                sequence_RNA="" if seq.startswith("unresolved:") else seq,
                cohort=cohort,
                human_class=cls,
                human_class_label=LABELS[cls],
                baseline_papers=b["n_papers"] if b else "0",
                baseline_dois=b["doi"] if b else "",
                ali_names_and_reads="; ".join(
                    x["original_name"] + ": " + x["reads"] for x in a
                ),
                ali_strict_gt1=any(x["strict_gt1"] == "True" for x in a),
                annotation=ANNOTATIONS[ann["status"]]
                if ann
                else "Außerhalb der bisherigen 16er-Annotationsprüfung",
                target_review=cur["level"]
                if cur
                else "Außerhalb der bisherigen 16er-Targetprüfung",
                literature_context=cur["approach"] if cur else "",
                target_genes=";".join(sorted({e["target"] for e in edges})),
                target_evidence="; ".join(
                    e["target"] + ": " + e["evidence"] for e in edges
                ),
                human_site_evidence="; ".join(
                    e["target"] + ": " + e["human_site"] for e in edges
                ),
                pathway_or_context="; ".join(e["pathway_or_context"] for e in edges),
                target_dois=";".join(sorted({e["doi"] for e in edges})),
                seed_screen_status="Durchgeführt; keine funktionelle Validierung"
                if seed
                else "Für diese Sequenz nicht durchgeführt",
                open_questions="; ".join(
                    filter(None, flags + [e["open_question"] for e in edges])
                ),
                old_model_context="Ältere miR-146a/miR-223/miR-155-Bewertung separat; hier keine neue kantenweise Prüfung"
                if any(
                    any(
                        n.startswith("bta-miR-" + mir) for mir in ["146a", "223", "155"]
                    )
                    for n in names
                )
                else "",
            )
        )
    assert len([r for r in rows if r["cohort"] == "Basisbestand"]) == 270
    assert len({r["candidate_id"] for r in rows}) == len(rows)
    assert {e["sequence_RNA"] for e in target_rows} <= {
        r["sequence_RNA"] for r in baseline
    }
    focus = [r for r in rows if r["sequence_RNA"] in annotation_by_seq]
    assert len(focus) == 16 and len(target_rows) == 8
    write("candidates.tsv", rows)
    write("milk_evidence.tsv", milk_rows)
    write("target_evidence.tsv", target_rows)
    write("focused_candidates.tsv", focus)
    lines = [
        "# Gemeinsamer Kandidatenvergleich",
        "",
        "Vertiefte Sichtung der bisherigen 16 Kandidaten. Alle übrigen bleiben in der vollständigen Tabelle. Keine Rangliste oder Modellentscheidung. „Kein humaner Seedtreffer“ beschreibt die miRNA-Referenz, nicht das Fehlen möglicher menschlicher Targets.",
        "",
        "| Kandidat | Milchbelege | Annotation | Targetansatz / Kontext | Eigene humane Stellenprüfung | Grenze der Übertragung | Quellen |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in focus:
        ann = annotation_by_seq[r["sequence_RNA"]]
        edges = targets_by_seq[r["sequence_RNA"]]
        cites = ", ".join(
            link(ROOT / e["source_note"], e["target"]) for e in edges
        ) or link(CURATION, "Literatursichtung")
        lines.append(
            "| "
            + " | ".join(
                [
                    ann["candidate"],
                    r["baseline_papers"]
                    + " Basis-Papers"
                    + (
                        "; Ali " + r["ali_names_and_reads"] + " Reads (vorläufig)"
                        if r["ali_names_and_reads"]
                        else ""
                    ),
                    r["annotation"],
                    r["target_evidence"] or r["literature_context"],
                    r["human_site_evidence"]
                    or "Keine literaturbezogene Einzelkante geprüft",
                    "; ".join(e["human_transfer"] for e in edges)
                    or "Kein humaner Targetbeleg zugeordnet",
                    cites,
                ]
            )
            + " |"
        )
    lines += [
        "",
        "Milch-Papers: Li 2016 (10.1371/journal.pone.0154129), Krupova 2023 (10.1038/s41597-023-02347-0); Ali 2026 (10.1016/j.idairyj.2025.106422) separat. Einzelne Fundstellen in `milk_evidence.tsv`.",
        "",
        link(OUT / "Alle Kandidaten.md", "Vollständige Kandidatenliste"),
    ]
    (OUT / "Kandidatenvergleich.md").write_text("\n".join(lines) + "\n")
    lines = [
        "# Alle Kandidaten mit Herkunft und Prüfstatus",
        "",
        "270 Basissequenzen plus getrennte vorläufige Ali-Einträge. Gleiche Sequenzen gemeinsam dargestellt; Referenzversionen und Nachweisstatus bleiben getrennt. Die Zeilenzahl ist keine neue bestätigte Inventargröße.",
        "",
        "| Namen | Bestand | Humane Referenzklasse | Basis-Papers | Ali Reads je Name | Targetprüfung |",
        "|---|---|---|---:|---|---|",
    ]
    for r in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    r["names"],
                    r["cohort"],
                    r["human_class_label"],
                    str(r["baseline_papers"]),
                    r["ali_names_and_reads"] or "Kein zugeordneter Tabellenbeleg",
                    r["target_evidence"] or r["target_review"],
                ]
            )
            + " |"
        )
    (OUT / "Alle Kandidaten.md").write_text("\n".join(lines) + "\n")
    summary = {
        "display_rows": len(rows),
        "cohorts": dict(Counter(r["cohort"] for r in rows)),
        "focused_candidates": len(focus),
        "source_specific_target_records": len(target_rows),
        "candidate_target_pairs": len(
            {(e["candidate"], e["target"]) for e in target_rows}
        ),
        "milk_evidence_rows": len(milk_rows),
        "baseline_unique_sequence_paper_pairs": len(
            {
                (r["candidate_id"], r["study"])
                for r in milk_rows
                if r["study"] != "ali2026"
            }
        ),
        "baseline_without_16_candidate_review": 270 - len(focus),
        "scope": "Current evidence synthesis; no additional target predictions, independent validation, or final candidate selection.",
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    )
    inputs.append(Path(__file__))
    (OUT / "manifest.json").write_text(
        json.dumps(
            {
                "inputs": {
                    str(p.relative_to(ROOT)): sha(p) for p in sorted(set(inputs))
                },
                "outputs": {
                    p.name: sha(p)
                    for p in sorted(OUT.iterdir())
                    if p.name != "manifest.json"
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
