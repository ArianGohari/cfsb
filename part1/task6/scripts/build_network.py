#!/usr/bin/env python3
"""Export the curated mouse network and check its coverage in public matrices."""
from pathlib import Path
import csv
import hashlib
import io
import json
import subprocess
import tarfile
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "network"
OUT.mkdir(exist_ok=True)

def tsv(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

genes = {"Abca1": 11303, "Abcg1": 11307, "Ccr2": 12772,
         "Ccr5": 12774, "Cx3cr1": 13051, "Il1b": 16176}
nodes = [dict(id=f"NCBIGene:{gid}", label=symbol, type="gene_product",
              taxon=10090, id_source=f"https://www.ncbi.nlm.nih.gov/gene/{gid}")
         for symbol, gid in genes.items()]
nodes += [dict(id="miRBase:MIMAT0000667", label="mmu-miR-33-5p", type="mature_miRNA",
               taxon=10090, id_source="https://mirbase.org/mature/MIMAT0000667")]
processes = {
    "efflux_apoa1": "Cholesterinefflux zu ApoA-I",
    "efflux_hdl": "Cholesterinefflux zu HDL",
    "recruitment_hi": "Plaque-Akkumulation Ly6C-hi",
    "recruitment_lo": "Plaque-Akkumulation Ly6C-lo",
    "nets": "NETs im Apoe-KO-Plaquekontext",
    "lesion": "Atherosklerotische Lesionslast",
}
nodes += [dict(id=f"TASK6:{key}", label=label, type="process_or_phenotype",
               taxon=10090, id_source="local definition; task6.qmd")
          for key, label in processes.items()]

edges = []
def edge(source, target, relation, sign, module, context, pmid, evidence, locator, limitation):
    edges.append(dict(id=f"T6E{len(edges)+1:02d}", source=source, target=target,
                      relation=relation, sign=sign, taxon=10090, module=module,
                      cell_context=context, source_pmid=str(pmid),
                      source_url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                      evidence=evidence, locator=locator, limitation=limitation))

for symbol in ["Abca1", "Abcg1"]:
    edge("miRBase:MIMAT0000667", f"NCBIGene:{genes[symbol]}", "represses_expression", -1,
         "lipid_miRNA", "mouse macrophages; supporting heterologous 3UTR reporter assays",
         20466885, "mouse expression perturbation; " + ("human ABCA1 3UTR reporter support" if symbol == "Abca1" else "mouse Abcg1 3UTR reporter support"), "Results; Figs 2-3",
         "Legacy miR-33 mapped to mature 5p; no 3p inference; reporter context differs from plaque" +
         ("; Abcg1 targeting is species-specific" if symbol == "Abcg1" else ""))
for symbol, acceptor in [("Abca1", "apoa1"), ("Abcg1", "hdl")]:
    edge(f"NCBIGene:{genes[symbol]}", f"TASK6:efflux_{acceptor}", "supports_efflux", 1,
         "lipid_miRNA", "mouse macrophages; acceptor-specific cholesterol efflux",
         20466885, "functional efflux evidence; pathway abstraction", "Results; Fig 4",
         "Not a stoichiometric transport reaction; flux cannot be inferred from mRNA alone")
for symbol in ["Ccr2", "Ccr5", "Cx3cr1"]:
    edge(f"NCBIGene:{genes[symbol]}", "TASK6:recruitment_hi", "supports_accumulation", 1,
         "monocytes", "Ly6C-hi monocytes; Apoe-deficient mouse atherosclerosis",
         17200718, "receptor perturbation and monocyte tracking", "Results: receptor use by subsets",
         "Accumulation includes recruitment and survival; not a direct transcriptional interaction")
edge("NCBIGene:12774", "TASK6:recruitment_lo", "supports_accumulation", 1,
     "monocytes", "Ly6C-lo monocytes; Apoe-deficient mouse atherosclerosis", 17200718,
     "receptor perturbation and monocyte tracking", "Results: CCR5 dependence",
     "Partial dependence; cannot substitute Ly6C-hi context")
edge("TASK6:nets", "NCBIGene:16176", "supports_expression_indirectly", 1,
     "neutrophil_macrophage", "Apoe-deficient mouse aorta; macrophage-associated IL1b",
     26185250, "indirect in vivo perturbation evidence", "Fig 3A-D",
     "NE/PR3 deficiency and DNase are not perfectly NET-specific; detailed priming assay used HUMAN monocytes; mRNA and protein not equivalent to mature cytokine")
edge("TASK6:nets", "TASK6:lesion", "supports_lesion_burden_indirectly", 1,
     "neutrophil_macrophage", "Apoe-deficient mouse atherosclerosis", 26185250,
     "indirect in vivo perturbation evidence", "Fig 2",
     "Model- and stage-specific phenotype; no quantitative human CAD risk prediction")

metadata = dict(schema_version="1.0", curated_on="2026-09-23", taxon=10090,
                model_type="static typed evidence graph", llm_assisted=True,
                experimental_validation_performed=False,
                semantics="Gene product nodes aggregate gene/protein identity. Signs refer only to the named endpoint and context. No rates or reaction stoichiometry.")
network = dict(metadata=metadata, nodes=nodes, edges=edges)
(OUT / "network.json").write_text(json.dumps(network, indent=2, ensure_ascii=False) + "\n")
tsv(OUT / "nodes.tsv", nodes)
tsv(OUT / "edges.tsv", edges)

ids = {n["id"] for n in nodes}
assert len(ids) == len(nodes)
assert len({e["id"] for e in edges}) == len(edges)
assert all(e["source"] in ids and e["target"] in ids for e in edges)
assert all(e["sign"] in [-1, 1] and e["source_pmid"] and e["limitation"] for e in edges)
assert all(n["taxon"] == 10090 for n in nodes)

dot = ['digraph Mouse {', 'graph [rankdir=LR, bgcolor="white", pad="0.25", nodesep="0.4", ranksep="0.7"];',
       'node [shape=box, style="rounded,filled", fillcolor="#eef4f8", fontname="Helvetica", fontsize=12];',
       'edge [fontname="Helvetica", fontsize=10];']
for n in nodes:
    color = "#e7dcf5" if n["type"] == "mature_miRNA" else ("#fff0d5" if n["type"] == "process_or_phenotype" else "#eef4f8")
    dot.append(f'{json.dumps(n["id"])} [label={json.dumps(n["label"])}, fillcolor="{color}"];')
for e in edges:
    indirect = "indirect" in e["relation"]
    color = "#ad2932" if e["sign"] == -1 else "#235e5b"
    arrow = "tee" if e["sign"] == -1 else "normal"
    label = e["id"] + (" -" if e["sign"] == -1 else " +")
    dot.append(f'{json.dumps(e["source"])} -> {json.dumps(e["target"])} [label="{label}", color="{color}", arrowhead="{arrow}", style="{"dashed" if indirect else "solid"}"];')
dot.append('}')
(OUT / "network.dot").write_text("\n".join(dot) + "\n")
subprocess.run(["dot", "-Tsvg", str(OUT / "network.dot"), "-o", str(OUT / "network.svg")], check=True)

archive = ROOT / "sources/GSE97310_10X_Matrices_CircRes2018.tar.gz"
coverage = []
matrices = []
with tarfile.open(archive) as tf:
    for member in tf.getmembers():
        if not member.name.endswith("/genes.tsv"):
            continue
        prefix = member.name.rsplit("/", 1)[0]
        sample = prefix.rsplit("/", 1)[-1]
        features = [line.decode().strip().split("\t") for line in tf.extractfile(member)]
        indices = {i + 1: (row[0], row[1]) for i, row in enumerate(features) if row[1] in genes}
        assert len(indices) == len(genes), (sample, indices)
        assert len({row[1] for row in indices.values()}) == len(genes)
        barcode_count = sum(1 for _ in tf.extractfile(prefix + "/barcodes.tsv"))
        handle = io.TextIOWrapper(tf.extractfile(prefix + "/matrix.mtx"))
        line = next(handle)
        while line.startswith("%"):
            line = next(handle)
        nr, nc, nnz = map(int, line.split())
        assert nr == len(features) and nc == barcode_count
        counts, cells = Counter(), {idx: set() for idx in indices}
        observed = 0
        for line in handle:
            row, col, value = map(int, line.split())
            observed += 1
            assert 1 <= row <= nr and 1 <= col <= nc and value > 0
            if row in indices:
                counts[row] += value
                cells[row].add(col)
        assert observed == nnz
        matrices.append(dict(matrix=sample, features=nr, barcodes=nc, nonzero_entries=nnz))
        for idx, (ensembl, symbol) in indices.items():
            coverage.append(dict(matrix=sample, gene_id=f"NCBIGene:{genes[symbol]}", symbol=symbol,
                                 ensembl_in_file=ensembl, positive_barcodes=len(cells[idx]),
                                 total_barcodes=nc, total_counts=counts[idx],
                                 positive_fraction=round(len(cells[idx]) / nc, 6)))
tsv(OUT / "matrix_inventory.tsv", matrices)
tsv(OUT / "data_coverage.tsv", coverage)
neighbors = {key: set() for key in ids}
for e in edges:
    neighbors[e["source"]].add(e["target"])
    neighbors[e["target"]].add(e["source"])
unseen, components = set(ids), 0
while unseen:
    stack = [unseen.pop()]
    components += 1
    while stack:
        newly_seen = neighbors[stack.pop()] & unseen
        unseen -= newly_seen
        stack.extend(newly_seen)
checks = dict(nodes=len(nodes), edges=len(edges), connected_modules=components,
              protein_coding_genes=len(genes), matrix_count=len(matrices),
              gene_matrix_pairs=len(coverage), detected_pairs=sum(r["positive_barcodes"] > 0 for r in coverage),
              signs=dict(Counter(str(e["sign"]) for e in edges)),
              validation="Unique IDs; endpoints; sources; taxon; exact unique symbol mapping; matrix dimensions; sparse entry count; positive integer counts; Graphviz SVG generation.")
(OUT / "validation.json").write_text(json.dumps(checks, indent=2) + "\n")
files = sorted((ROOT / "sources").glob("*")) + sorted(OUT.glob("*"))
(ROOT / "SHA256SUMS").write_text("".join(hashlib.sha256(p.read_bytes()).hexdigest() + "  " + str(p.relative_to(ROOT)) + "\n" for p in files if p.is_file()))
print(json.dumps(checks, indent=2))
