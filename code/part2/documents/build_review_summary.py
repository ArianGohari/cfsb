"""Build a scoped search flow and sequence-count figure from saved review tables."""

from pathlib import Path
from collections import Counter
import csv, json, hashlib, subprocess
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "output/part2/milk_inventory"
OUT = ROOT / "output/part2/review_summary"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = [
        BASE / "extension_search/search_hits.tsv",
        BASE / "extension_search/screening.tsv",
        BASE / "sequence_comparison/summary.json",
        BASE / "human_comparison/summary.json",
        BASE / "paper_support/summary.json",
    ]
    hits = list(csv.DictReader(inputs[0].open(), delimiter="\t"))
    records = list(csv.DictReader(inputs[1].open(), delimiter="\t"))
    c = Counter(r["status"] for r in records)
    q = Counter(r["search"] for r in hits)
    assert len(records) == len({r["record"] for r in records}) == 93
    assert len(hits) == 106 and len(hits) - len(records) == 13
    assert set(r["record"] for r in hits) == set(r["record"] for r in records)
    screened = [r for r in records if r.get("screened_on")]
    decisions = Counter(r["status"] for r in screened)
    fulltexts = Counter(
        r.get("fulltext_status", "") for r in screened if r.get("fulltext_status")
    )
    followup_done = fulltexts["Gezielt geprüft"]
    followup_pending = sum(
        r["status"] != "Für Milch-Inventar ausgeschlossen"
        and r.get("fulltext_status") != "Gezielt geprüft"
        for r in screened
    )
    assert len(screened) == 82 and all(
        r["reason"] and r["basis"] and r["note"] for r in screened
    )
    assert set(decisions) <= set(
        ["Für Milch-Inventar ausgeschlossen", "Volltext prüfen", "Zuordnung klären"]
    )
    assert (
        c["Noch nicht einzeln bewertet"] == 0
        and c["Bereits im fünfteiligen Pilotbestand"] == 4
    )
    assert q == {"pubmed": 66, "elicit_powder": 20, "elicit_processing": 20}
    assert len(records) == 82 + 4 + 5 + 1 + 1
    scope_path = ROOT / "output/part2/review_scope/summary.json"
    scope = json.loads(scope_path.read_text())
    inputs.append(scope_path)
    assert scope["roles"]["Zurückgestellt"] == followup_pending
    assert (
        scope["roles"]["Inventarvergleich"] == 10
        and scope["roles"]["Transferdiskussion"] == followup_done
    )
    comparison = json.loads(inputs[2].read_text())["comparison"]
    classes = json.loads(inputs[3].read_text())
    support = json.loads(inputs[4].read_text())
    assert comparison["classes_all_qualifying"] == classes["classes"]
    assert sum(classes["classes"].values()) == support["n_sequences"] == 270
    assert support["histogram"] == {"1": 96, "2": 174}
    evidence = {
        "search_scope": "Supplementary milk/processing search, 2026-10-09; remaining title/abstract screening completed 2026-10-11; focused synthesis bounded retrospectively 2026-10-11; 32 follow-up records deferred, not excluded",
        "hits": len(hits),
        "unique_records": len(records),
        "duplicates": 13,
        "not_screened": c["Noch nicht einzeln bewertet"],
        "title_abstract_assessments": len(screened),
        "screening_decisions": dict(decisions),
        "pilot_overlap": 4,
        "prioritized_fulltexts": 5,
        "preprint_same_study": 1,
        "goat_only": 1,
        "curated_milk_comparison_studies": 10,
        "followup_fulltexts": dict(fulltexts),
        "followup_pending": followup_pending,
        "report_scope": scope,
        "harmonized_sequence_studies": 2,
        "classes": classes["classes"],
        "paper_support": support["histogram"],
        "limitations": "Not a global PRISMA flow; source catalog, publication records, studies and sequences have different denominators.",
    }
    (OUT / "evidence.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False) + "\n"
    )
    dot = """digraph flow {
    graph [rankdir=TB,bgcolor="white",nodesep=.28,ranksep=.32];
    node [shape=box,style="rounded,filled",fillcolor="#f0f6f2",color="#63836d",fontname="Arial",fontsize=12,margin=".15,.10"];
    edge [color="#63836d",arrowsize=.65];
    a [label="PubMed: 66 Treffer\\nElicit: 20 + 20 Treffer"];
    b [label="106 Trefferzuordnungen"];
    dup [label="13 wiederholte Zuordnungen\\nüber DOI/PMID zusammengeführt",fillcolor="#f5f5f5"];
    c [label="93 Publikationsdatensätze"];
    screen [label="82 Titel/Abstracts gesichtet\\nKI-unterstützte Bewertung, 11.10.2026"];
    exclude [label="EXCLUDED ausgeschlossen\\nfür das Milch-Inventar",fillcolor="#f5f5f5"];
    next [label="Erstsichtung: RELEVANT vorgemerkt + UNCLEAR unklar\\nDavon FULLTEXT Volltexte gezielt geprüft\\nPENDING für diese Synthese zurückgestellt\\n(darunter PARTIAL Teilzugang); kein Ausschluss",fillcolor="#fff1d6",color="#b8954e"];
    done [label="11 bereits zugeordnet"];
    focus [label="5 priorisierte Arbeiten\\ngezielt im Volltext geprüft"];
    other [label="4 bereits im Pilotbestand\\n1 Preprint derselben Turner-Studie\\n1 ausschließlich Ziegenmilch",fillcolor="#f5f5f5"];
    a->b;b->dup;b->c;c->screen;c->done;done->focus;done->other;screen->exclude;screen->next;
    {rank=same;c;dup} {rank=same;done;screen} {rank=same;focus;other;exclude;next}
    }"""
    dot = (
        dot.replace("EXCLUDED", str(decisions["Für Milch-Inventar ausgeschlossen"]))
        .replace("RELEVANT", str(decisions["Volltext prüfen"]))
        .replace("UNCLEAR", str(decisions["Zuordnung klären"]))
        .replace("FULLTEXT", str(followup_done))
        .replace("PENDING", str(followup_pending))
        .replace("PARTIAL", str(fulltexts["Teilzugang; Volltext offen"]))
    )
    (OUT / "search_flow.dot").write_text(dot + "\n")
    subprocess.run(
        [
            "dot",
            "-Tsvg",
            str(OUT / "search_flow.dot"),
            "-o",
            str(OUT / "search_flow.svg"),
        ],
        check=True,
    )
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "svg.hashsalt": "cfsb_review_summary",
        }
    )
    fig, ax = plt.subplots(figsize=(8.5, 2.6))
    colors = ["#007a53", "#679fa3", "#b8bdc4"]
    keys = ["exact_human_sequence", "human_seed_only", "no_human_seed_match"]
    labels = [
        "Identische humane Sequenz",
        "Nur gleicher humaner Seed",
        "Kein humaner Seedtreffer",
    ]
    for y, d in [(1, classes["classes"]), (0, comparison["classes_supported_in_both"])]:
        left = 0
        for key, color in zip(keys, colors):
            v = d[key]
            ax.barh(y, v, left=left, color=color, height=0.55)
            ax.text(
                left + v / 2,
                y,
                str(v),
                va="center",
                ha="center",
                color="white" if key == keys[0] else "#17251f",
                weight="bold",
            )
            left += v
        ax.text(left + 3, y, str(left) + " gesamt", va="center", fontsize=10)
    ax.set(
        yticks=[1, 0],
        yticklabels=["Gesamter Basisbestand", "In beiden Studien gestützt"],
        xlabel="Reife Referenzsequenzen",
        xlim=(0, 330),
        ylim=(-0.5, 1.5),
    )
    for side in ["top", "right", "left"]:
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="y", length=0)
    from matplotlib.patches import Patch

    fig.legend(
        handles=[Patch(color=c, label=l) for c, l in zip(colors, labels)],
        loc="upper center",
        ncol=3,
        frameon=False,
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.83))
    fig.savefig(OUT / "sequence_classes.svg", metadata={"Date": None})
    plt.close(fig)
    files = [
        OUT / f
        for f in [
            "evidence.json",
            "search_flow.dot",
            "search_flow.svg",
            "sequence_classes.svg",
        ]
    ]
    (OUT / "manifest.json").write_text(
        json.dumps(
            {
                "inputs": {
                    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in inputs + [Path(__file__).resolve()]
                },
                "outputs": {
                    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in files
                },
                "matplotlib": matplotlib.__version__,
            },
            indent=2,
        )
        + "\n"
    )
    print(
        f"PASS: 106→93; 82 assessed: {dict(decisions)}; 11 prior assignments; sequence classes 270/174"
    )


if __name__ == "__main__":
    main()
