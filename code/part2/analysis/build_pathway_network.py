"""Map selected miR-6517 target hypotheses to KEGG reactions and GENCODE sites."""

from pathlib import Path
import csv
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "output/part2/mir6517_pathway"
SEEDS = ROOT / "output/part2/milk_inventory/human_seed_screen"
KEGG = (
    ROOT
    / "data/datasets/milk_mirna_inventory/pfkl_omics_selection_20261010/kegg_hsa00010.txt"
)
TARGETS = ROOT / "output/part2/milk_inventory/candidate_evidence/target_evidence.tsv"
MILK = ROOT / "output/part2/milk_inventory/candidate_evidence/milk_evidence.tsv"
GENES = ["GPI", "PFKL", "PFKM", "PFKP", "ALDOA", "PGAM1", "DLAT"]


def read(path):
    return list(csv.DictReader(path.open(), delimiter="\t"))


def table(path, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    transcripts = read(SEEDS / "transcripts.tsv")
    sites = [
        r
        for r in read(SEEDS / "sites.tsv")
        if r["candidate"] == "bta-miR-6517" and r["variant"] == "inventory_reference"
    ]
    nodes = []
    for gene in GENES:
        tx = [r for r in transcripts if r["gene"] == gene]
        ids = {r["gene_id"].split(".")[0] for r in tx}
        assert len(ids) == 1, (gene, ids)
        hits = [r for r in sites if r["gene"] == gene]
        assert all(r["gene_id"].split(".")[0] in ids for r in hits)
        nodes.append(
            dict(
                gene=gene,
                ensembl=next(iter(ids)),
                mane_motif=";".join(
                    sorted({r["site_type"] for r in hits if r["mane_select"] == "True"})
                ),
                all_motifs=";".join(sorted({r["site_type"] for r in hits})),
                sites=";".join(
                    f"{r['transcript_id']}:{r['utr_start']}-{r['utr_end']}:{r['site_type']}"
                    for r in hits
                ),
                source="GENCODE 48; KEGG hsa00010",
            )
        )
    by_gene = {r["gene"]: r for r in nodes}
    assert (
        by_gene["PFKP"]["mane_motif"] == ""
        and by_gene["PFKP"]["all_motifs"] == "7mer-m8"
    )
    assert all(not by_gene[g]["all_motifs"] for g in ["GPI", "PFKM", "ALDOA"])
    table(OUT / "gene_evidence.tsv", nodes)

    target = [
        r
        for r in read(TARGETS)
        if r["candidate"] == "bta-miR-6517" and r["target"] == "PFKL"
    ]
    assert len(target) == 1 and target[0]["doi"] == "10.1111/jpn.13662"
    milk = [r for r in read(MILK) if r["original_name"] == "bta-miR-6517"]
    assert {r["study"] for r in milk} == {"li2016", "krupova2023"}
    table(OUT / "milk_provenance.tsv", milk)
    edges = []

    def edge(source, target, kind, evidence, locator, model_role):
        edges.append(
            dict(
                source=source,
                target=target,
                relation=kind,
                evidence=evidence,
                locator=locator,
                model_role=model_role,
            )
        )

    edge(
        "bta-miR-6517",
        "bovine PFKL",
        "experimental repression",
        "Yang 2022; bovine target",
        target[0]["doi"] + "; " + target[0]["locator"],
        "biological anchor; not a human edge",
    )
    for gene in ["PFKL", "PFKP", "PGAM1", "DLAT"]:
        edge(
            "bta-miR-6517",
            gene,
            "hypothesized human repression",
            "reference 3UTR motif only",
            by_gene[gene]["sites"],
            "conditional simulated edge" if gene == "PFKL" else "not simulated",
        )
    reaction_gene = {
        "GPI": "r_gpi",
        "PFKL": "r_pfk",
        "PFKM": "r_pfk",
        "PFKP": "r_pfk",
        "ALDOA": "r_aldo",
        "PGAM1": "r_pgam",
        "DLAT": "r_pdh",
    }
    kegg = KEGG.read_text()
    for gene, reaction in reaction_gene.items():
        assert f" {gene};" in kegg
        edge(
            gene,
            reaction,
            "complex component" if gene == "DLAT" else "enzyme assignment",
            "KEGG hsa00010 gene/enzyme annotation",
            str(KEGG.relative_to(ROOT)),
            "PFK reaction modeled; other reactions are context",
        )
    for source, target, relation in [
        ("r_gpi", "r_pfk", "shared F6P"),
        ("r_pfk", "r_aldo", "shared F1,6BP"),
        ("r_aldo", "r_pgam", "omitted intermediate reactions"),
        ("r_pgam", "r_pdh", "omitted intermediate reactions"),
    ]:
        edge(
            source,
            target,
            relation,
            "glycolysis pathway context",
            "KEGG hsa00010",
            "not a gene-regulatory edge",
        )
    table(OUT / "edges.tsv", edges)

    dot = [
        "digraph network {",
        'graph [rankdir=LR, bgcolor="white", pad=.15, nodesep=.23, ranksep=.7, fontname="Arial"];',
        'node [shape=box, style="rounded,filled", fillcolor="#f5f7f6", color="#b1bcb6", fontname="Arial", fontsize=12, margin=".15,.09"];',
        'edge [fontname="Arial", fontsize=10, color="#69756e", arrowsize=.65];',
        'mir [label="bta-miR-6517\\nKuhmilch / EV-Fraktion", fillcolor="#e3f0e9", color="#00883a"];',
        'bovine [label="Bovines PFKL\\nWT-/Mutantenreporter\\nYang et al. 2022", fillcolor="#e3f0e9", color="#00883a"];',
        'mir -> bovine [arrowhead=tee, color="#00883a", penwidth=1.7, label="boviner Befund"];',
    ]
    for gene in GENES:
        label = gene
        if gene == "PFKL":
            label += "\\nModellkern"
        color = "#00883a" if gene == "PFKL" else "#b1bcb6"
        dot.append(
            f'{gene} [label="{label}", color="{color}", penwidth={2 if gene == "PFKL" else 1}];'
        )
    for gene in ["PFKL", "PFKP", "PGAM1", "DLAT"]:
        motif = by_gene[gene]["mane_motif"] or by_gene[gene]["all_motifs"]
        label = motif + "\\n" + ("alternative UTR" if gene == "PFKP" else "MANE-UTR")
        dot.append(
            f'mir -> {gene} [style=dashed, color="#b17e2c", arrowhead=tee, label="{label}"];'
        )
    reactions = {
        "r_gpi": "G6P ↔ F6P",
        "r_pfk": "F6P + ATP → F1,6BP + ADP",
        "r_aldo": "F1,6BP ↔ DHAP + GAP",
        "r_pgam": "3-Phosphoglycerat ↔ 2-Phosphoglycerat",
        "r_pdh": "Pyruvat → Acetyl-CoA\\nPDH-Komplex (vereinfacht)",
    }
    for name, label in reactions.items():
        dot.append(f'{name} [label="{label}", fillcolor="#eef3f7", color="#7391a7"];')
    for gene, reaction in reaction_gene.items():
        label = "Teil des Komplexes" if gene == "DLAT" else ""
        dot.append(f'{gene} -> {reaction} [arrowhead=none, label="{label}"];')
    dot += [
        "{rank=same; bovine; GPI; PFKL; PFKM; PFKP; ALDOA; PGAM1; DLAT;}",
        "bovine -> GPI -> PFKL -> PFKM -> PFKP -> ALDOA -> PGAM1 -> DLAT [style=invis, weight=20];",
        "{rank=same; r_gpi; r_pfk; r_aldo; r_pgam; r_pdh;}",
        'r_gpi -> r_pfk -> r_aldo [color="#49748c", penwidth=1.5];',
        'r_aldo -> r_pgam -> r_pdh [style=dotted, color="#49748c", label="weitere Schritte"];',
        'label="Gestrichelte Hemmkanten: humane Hypothesen, keine gemessene miRNA-Wirkung";',
        "labelloc=b; fontsize=12;",
        "}",
    ]
    (OUT / "network.dot").write_text("\n".join(dot) + "\n")
    for ext in ["svg", "png"]:
        subprocess.run(
            [
                "dot",
                f"-T{ext}",
                str(OUT / "network.dot"),
                "-o",
                str(OUT / f"network.{ext}"),
            ],
            check=True,
        )
    hashes = lambda paths: {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in paths
    }
    inputs = [
        SEEDS / "sites.tsv",
        SEEDS / "transcripts.tsv",
        KEGG,
        TARGETS,
        MILK,
        Path(__file__).resolve(),
    ]
    files = [
        OUT / name
        for name in [
            "gene_evidence.tsv",
            "edges.tsv",
            "milk_provenance.tsv",
            "network.dot",
            "network.svg",
            "network.png",
        ]
    ]
    (OUT / "manifest.json").write_text(
        json.dumps(
            dict(
                inputs=hashes(inputs),
                outputs=hashes(files),
                graphviz=subprocess.run(
                    ["dot", "-V"], capture_output=True, text=True, check=True
                ).stderr.strip(),
                scope="Seven selected pathway genes; four unvalidated human motif edges. Bovine evidence separate. No new model edges or parameters.",
            ),
            indent=2,
        )
        + "\n"
    )
    print("PASS: KEGG assignments and GENCODE sites checked; separate bovine edge")


if __name__ == "__main__":
    main()
