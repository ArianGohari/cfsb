"""Import complete published matrices and compare their reference sequences offline.

uv run --offline --project code/part2/reproduction --locked python \
    code/part2/literature/milk_inventory/compare_sequences.py
"""

from pathlib import Path
from collections import defaultdict, Counter
import argparse, csv, hashlib, json, math, re
import openpyxl

ROOT = Path(__file__).resolve().parents[4]
DATA = ROOT / "data/datasets/milk_mirna_inventory"
LI = ROOT / "data/sources/li_2016_mirnome_milk_fat_whey_cells/supplements"
KR = ROOT / "data/sources/krupova_2023_cow_goat_milk_ev_mirnomes/supplements"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_tsv(p, rows):
    assert rows, p
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, list(rows[0]), delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def seq(s):
    s = s.upper().replace("T", "U")
    assert len(s) >= 8 and set(s) <= set("ACGU"), s
    return s


def fasta(p):
    result = {}
    name = None
    for line in p.read_text().splitlines():
        if line.startswith(">"):
            parts = line[1:].split()
            name = parts[0]
            if name in result:
                # Current FASTA contains duplicate names in unrelated species.
                # Retain both accessions; require unambiguous human/bovine labels.
                assert not name.startswith(("hsa-", "bta-")), name
                name += "|" + parts[1]
                assert name not in result
            result[name] = {"accession": parts[1], "sequence": ""}
        elif name:
            result[name]["sequence"] += line.strip()
    for record in result.values():
        record["sequence"] = seq(record["sequence"])
    return result


def sheet(p, name):
    w = openpyxl.load_workbook(p, read_only=True, data_only=True)
    rows = list(w[name].values)
    w.close()
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--output",
        type=Path,
        default=ROOT / "output/part2/milk_inventory/sequence_comparison",
    )
    out = ap.parse_args().output
    out.mkdir(parents=True, exist_ok=True)
    protocol = json.loads((DATA / "sequence_comparison_protocol.json").read_text())
    inputs = {}
    for manifest in ["retrieval_20261009.json", "reference_retrieval_20261009.json"]:
        p = DATA / manifest
        inputs[str(p.relative_to(ROOT))] = sha(p)
        for r in json.loads(p.read_text()):
            source = ROOT / r["path"]
            assert sha(source) == r["sha256"], source
            inputs[r["path"]] = r["sha256"]
    inputs[str((DATA / "sequence_comparison_protocol.json").relative_to(ROOT))] = sha(
        DATA / "sequence_comparison_protocol.json"
    )
    refs = {
        v: fasta(DATA / f"references/mirbase{v}_mature.fa")
        for v in ["20", "21", "23_1"]
    }
    human = {n: r for n, r in refs["23_1"].items() if n.startswith("hsa-")}
    bovine = {n: r for n, r in refs["23_1"].items() if n.startswith("bta-")}
    human_seq = defaultdict(list)
    human_seed = defaultdict(list)
    bovine_seq = defaultdict(list)
    for n, r in human.items():
        human_seq[r["sequence"]].append(n)
        human_seed[r["sequence"][1:8]].append(n)
    for n, r in bovine.items():
        bovine_seq[r["sequence"]].append(n)

    def compare(s):
        seed = s[1:8]
        exact = sorted(human_seq.get(s, []))
        same = sorted(human_seed.get(seed, []))
        prefix = [
            n
            for n in same
            if human[n]["sequence"] != s
            and (
                human[n]["sequence"].startswith(s) or s.startswith(human[n]["sequence"])
            )
        ]
        five_prime = [
            n
            for n, r in human.items()
            if 0 < abs(len(r["sequence"]) - len(s)) <= 3
            and (r["sequence"].endswith(s) or s.endswith(r["sequence"]))
        ]
        return {
            "sequence_RNA": s,
            "seed_2_8": seed,
            "human_class": "exact_human_sequence"
            if exact
            else "human_seed_only"
            if same
            else "no_human_seed_match",
            "human_exact_names": ";".join(exact),
            "human_seed_names": ";".join(same),
            "three_prime_length_variant_names": ";".join(prefix),
            "five_prime_length_variant_names": ";".join(sorted(five_prime)),
            "current_bovine_exact_names": ";".join(sorted(bovine_seq.get(s, []))),
        }

    numeric = []
    inventory = []
    novels = []
    qc = {}

    def measurement(
        study,
        path,
        sheet_name,
        row,
        col,
        name,
        sample,
        material,
        value,
        unit,
        annotation,
    ):
        assert (
            isinstance(value, (int, float)) and math.isfinite(value) and value >= 0
        ), (path, row, col, value)
        numeric.append(
            {
                "study": study,
                "original_name": name,
                "sample": sample,
                "material": material,
                "value": value,
                "unit": unit,
                "annotation": annotation,
                "source_path": str(path.relative_to(ROOT)),
                "source_sha256": sha_cache[path],
                "sheet": sheet_name,
                "cell": f"{openpyxl.utils.get_column_letter(col)}{row}",
            }
        )

    paths = [
        LI / "pone.0154129.s006.xlsx",
        LI / "pone.0154129.s008.xlsx",
        LI / "pone.0154129.s009.xlsx",
        KR / "data_ref_4590_cow.xlsx",
        KR / "GSE227559_Processed_data.xlsx",
    ]
    sha_cache = {p: sha(p) for p in paths}
    # Li: all known counts; reproduce the author's explicit within-fraction rule.
    p = paths[0]
    rows = sheet(p, "S2 Table")
    headers = list(rows[1][1:])
    records = rows[2:]
    assert len(records) == 255 and len(headers) == 12
    assert len(set(r[0] for r in records)) == len(records)
    sums = [sum(r[i + 1] for r in records) for i in range(12)]
    fraction_counts = Counter()
    fraction_names = {k: set() for k in ["Cell", "Fat", "Whey"]}
    li_counts = {}
    for rownum, r in enumerate(records, 3):
        name = r[0]
        values = list(r[1:])
        li_counts[name] = values
        assert name in refs["21"], name
        sequence = refs["21"][name]["sequence"]
        cpm = [v * 1e6 / d for v, d in zip(values, sums)]
        fractions = []
        n_by_fraction = []
        for fraction in ["Cell", "Fat", "Whey"]:
            ids = [i for i, h in enumerate(headers) if h.startswith(fraction + "_")]
            n = sum(cpm[i] >= protocol["li_known"]["threshold_cpm"] for i in ids)
            n_by_fraction.append(f"{fraction}:{n}/4")
            if n >= protocol["li_known"]["minimum_replicates_per_fraction"]:
                fractions.append(fraction)
                fraction_names[fraction].add(name)
                fraction_counts[fraction] += 1
        for i, (h, v) in enumerate(zip(headers, values), 2):
            measurement(
                "li2016",
                p,
                "S2 Table",
                rownum,
                i,
                name,
                h,
                h.split("_")[0],
                v,
                "raw_reads",
                "reported_known",
            )
        inventory.append(
            {
                "study": "li2016",
                "original_name": name,
                "sequence_origin": "miRBase21_name_mapping",
                "source_reference_accession": refs["21"][name]["accession"],
                "qualifies": bool(fractions),
                "qualified_materials": ";".join(fractions),
                "replicate_support": ";".join(n_by_fraction),
                "sequence_matches_study_reference": True,
                "source_path": str(p.relative_to(ROOT)),
                "source_sheet": "S2 Table",
                "source_row": rownum,
                **compare(sequence),
            }
        )
    shared = len(set.intersection(*fraction_names.values()))
    assert dict(fraction_counts) == {"Cell": 249, "Fat": 210, "Whey": 200}, (
        fraction_counts
    )
    assert shared == 188
    qc["li"] = {
        "known_rows": len(records),
        "sample_columns": headers,
        "cpm_denominators": dict(zip(headers, sums)),
        "fraction_counts": dict(fraction_counts),
        "shared_all_fractions": shared,
        "any_fraction": len(set.union(*fraction_names.values())),
        "reported_counts_reproduced": True,
        "denominator_note": "Sum of published known-miRNA counts; matches reported calls, not a FASTQ reanalysis",
    }
    # Krupova: verify species from both deposit metadata and original workbook sample sheet.
    p = paths[3]
    sample_rows = sheet(p, "samples")
    sample_species = {r[1]: r[2] for r in sample_rows[2:] if r[1]}
    cows = [n for n, s in sample_species.items() if s == "Cow"]
    assert set(cows) == {"B1", "B2", "B3", "B20", "B62"}
    soft = (DATA / "GSE227559_family_20261009.soft").read_text()
    geo_samples = []
    for block in soft.split("^SAMPLE = ")[1:]:
        gsm = block.splitlines()[0].strip()
        title = re.search(r"!Sample_title = (.+)", block).group(1).strip()
        organism = re.search(r"!Sample_organism_ch1 = (.+)", block).group(1).strip()
        sample = re.search(r"\[(.+)\]", title).group(1)
        assert organism == (
            "Bos taurus" if sample_species[sample] == "Cow" else "Capra hircus"
        )
        geo_samples.append(
            {"sample": sample, "GSM": gsm, "species": organism, "source": "GSE227559"}
        )
    assert len(geo_samples) == 9
    write_tsv(out / "sample_mapping.tsv", geo_samples)
    sheets = {name: sheet(p, name) for name in ["mirna_rawcounts", "mirna_tpm"]}
    tables = {
        name: {
            r[0]: (i, r)
            for i, r in enumerate(rows[3:], 4)
            if isinstance(r[0], str) and r[0].startswith("bta-")
        }
        for name, rows in sheets.items()
    }
    assert len(tables["mirna_tpm"]) == 793 and set(tables["mirna_rawcounts"]) == set(
        tables["mirna_tpm"]
    )
    header = list(sheets["mirna_tpm"][2])
    assert header == list(sheets["mirna_rawcounts"][2])
    cow_indices = [i for i, h in enumerate(header) if h in cows]
    all_indices = list(range(4, 13))
    assert len(cow_indices) == 5
    kr_tpm = {}
    sequence_mismatches = []
    for name, (rownum, r) in tables["mirna_tpm"].items():
        sequence = seq(r[1])
        rawrow, raw = tables["mirna_rawcounts"][name]
        assert seq(raw[1]) == sequence
        tpm = [r[i] for i in cow_indices]
        kr_tpm[name] = tpm
        threshold = protocol["krupova_known"]["threshold_tpm_strictly_greater_than"]
        n = sum(v > threshold for v in tpm)
        refmatch = name in refs["20"] and refs["20"][name]["sequence"] == sequence
        if not refmatch:
            sequence_mismatches.append(name)
        inventory.append(
            {
                "study": "krupova2023",
                "original_name": name,
                "sequence_origin": "deposited_reference_sequence",
                "source_reference_accession": refs["20"]
                .get(name, {})
                .get("accession", ""),
                "qualifies": n >= protocol["krupova_known"]["minimum_replicates"],
                "qualified_materials": "milk_EV"
                if n >= protocol["krupova_known"]["minimum_replicates"]
                else "",
                "replicate_support": f"cow_TPM>{threshold}:{n}/5",
                "sequence_matches_study_reference": refmatch,
                "source_path": str(p.relative_to(ROOT)),
                "source_sheet": "mirna_tpm",
                "source_row": rownum,
                **compare(sequence),
            }
        )
        for i in cow_indices:
            measurement(
                "krupova2023",
                p,
                "mirna_tpm",
                rownum,
                i + 1,
                name,
                header[i],
                "milk_EV",
                r[i],
                "reported_TPM_integer",
                "reported_known",
            )
            measurement(
                "krupova2023",
                p,
                "mirna_rawcounts",
                rawrow,
                i + 1,
                name,
                header[i],
                "milk_EV",
                raw[i],
                "raw_reads",
                "reported_known",
            )
    # GEO contains a filtered copy, not an independent study. Check every sequence/value.
    gp = paths[4]
    geo = sheet(gp, "Feuil1")
    gh = list(geo[2])
    gr = [(i, r) for i, r in enumerate(geo[3:], 4) if r[0]]
    geo_names = set()
    comparisons = 0
    for _, r in gr:
        name = r[0]
        geo_names.add(name)
        source = tables["mirna_tpm"][name][1]
        assert seq(r[1]) == seq(source[1])
        for i, h in enumerate(gh[2:], 2):
            assert r[i] == source[header.index(h)]
            comparisons += 1
    positive_all = {
        n
        for n, (_, r) in tables["mirna_tpm"].items()
        if any(r[i] > 0 for i in all_indices)
    }
    assert geo_names == positive_all
    sensitivity = []
    for threshold in protocol["krupova_known"][
        "sensitivity_thresholds_strictly_greater_than"
    ]:
        for min_n in protocol["krupova_known"]["sensitivity_minimum_replicates"]:
            eligible = [
                r
                for r in inventory
                if r["study"] == "krupova2023"
                and sum(v > threshold for v in kr_tpm[r["original_name"]]) >= min_n
            ]
            sensitivity.append(
                {
                    "strict_TPM_threshold": threshold,
                    "minimum_cows": min_n,
                    "names": len(eligible),
                    "unique_sequences": len({r["sequence_RNA"] for r in eligible}),
                }
            )
    write_tsv(out / "threshold_sensitivity.tsv", sensitivity)
    qc["krupova"] = {
        "all_annotated_rows": 793,
        "unique_reference_sequences": len(
            {seq(r[1]) for _, r in tables["mirna_tpm"].values()}
        ),
        "cow_samples": [header[i] for i in cow_indices],
        "positive_raw_read_names_any_cow": sum(
            any(tables["mirna_rawcounts"][n][1][i] > 0 for i in cow_indices)
            for n in tables["mirna_rawcounts"]
        ),
        "positive_TPM_names_any_cow": sum(
            any(v > 0 for v in values) for values in kr_tpm.values()
        ),
        "positive_TPM_per_cow": {
            header[i]: sum(r[i] > 0 for _, r in tables["mirna_tpm"].values())
            for i in cow_indices
        },
        "TPM_above1_per_cow": {
            header[i]: sum(r[i] > 1 for _, r in tables["mirna_tpm"].values())
            for i in cow_indices
        },
        "positive_TPM_any_species": len(positive_all),
        "GEO_rows": len(gr),
        "GEO_value_comparisons": comparisons,
        "GEO_matches_figshare": True,
        "sequence_mismatches_to_miRBase20": sequence_mismatches,
        "reported_discrepancies": [
            "Article: 295 across species; deposited positive-TPM/GEO rows: 296.",
            "Article: average 239 cow miRNAs >1 TPM; deposited integer TPM gives different values. No adjustment to force agreement.",
        ],
        "unit_note": "Rounded integer TPM as deposited. A zero TPM can coexist with positive raw reads; not an absence claim.",
    }
    # Novel predictions kept separate with cell provenance and all conflicting sequences retained.
    s4 = sheet(paths[1], "S4 Table")
    novseq = defaultdict(set)
    sequence_rows = []
    for i, r in enumerate(s4[2:], 3):
        if not r[0]:
            continue
        sequence = seq(r[1])
        novseq[r[0]].add(sequence)
        sequence_rows.append(
            {
                "study": "li2016",
                "id": r[0],
                "sequence_RNA": sequence,
                "location": r[4],
                "source_path": str(paths[1].relative_to(ROOT)),
                "sheet": "S4 Table",
                "row": i,
                "cell": f"B{i}",
            }
        )
    write_tsv(out / "li_novel_sequence_records.tsv", sequence_rows)
    s5 = sheet(paths[2], "S5 Table")
    novnames = []
    for i, r in enumerate(s5[2:], 3):
        if not isinstance(r[0], str) or not r[0].startswith("bta-"):
            continue
        name = r[0]
        novnames.append(name)
        for j, h in enumerate(s5[1][1:], 2):
            measurement(
                "li2016",
                paths[2],
                "S5 Table",
                i,
                j,
                name,
                h,
                h.split("_")[0],
                r[j - 1],
                "raw_counts_as_labeled_unit_under_review",
                "predicted_novel",
            )
        for sequence in sorted(novseq.get(name, set())):
            novels.append(
                {
                    "study": "li2016",
                    "original_name": name,
                    "sequence_conflict": len(novseq[name]) != 1,
                    "included_in_known_comparison": False,
                    "source_path": str(paths[1].relative_to(ROOT)),
                    "note": "S5 label says raw counts, but overlaps Table 5 CPM values; unit/sample mapping unresolved",
                    **compare(sequence),
                }
            )
    put = sheet(paths[3], "putative_mirna")
    ph = list(put[2])
    putrows = []
    for i, r in enumerate(put[3:], 4):
        if not isinstance(r[0], str) or not r[0].startswith("put-miR-"):
            continue
        putrows.append(r)
        sequence = seq(r[5])
        for j, h in enumerate(ph):
            if h in cows:
                measurement(
                    "krupova2023",
                    paths[3],
                    "putative_mirna",
                    i,
                    j + 1,
                    r[0],
                    h,
                    "milk_EV",
                    r[j],
                    "counts_unit_not_explicit_in_sheet",
                    "predicted_novel",
                )
        novels.append(
            {
                "study": "krupova2023",
                "original_name": r[0],
                "sequence_conflict": False,
                "included_in_known_comparison": False,
                "source_path": str(paths[3].relative_to(ROOT)),
                "note": "Putative miRNA; no validated annotation or mature read-processing audit",
                **compare(sequence),
            }
        )
    qc["novel"] = {
        "li_S4_records": len(sequence_rows),
        "li_S4_ids": len(novseq),
        "li_S5_ids": len(novnames),
        "li_conflicting_ids": [n for n, s in novseq.items() if len(s) > 1],
        "li_S4_without_S5": sorted(set(novseq) - set(novnames)),
        "krupova_putative_rows": len(putrows),
        "kept_separate": True,
    }
    write_tsv(out / "measurements.tsv", numeric)
    write_tsv(out / "known_annotation_comparison.tsv", inventory)
    write_tsv(out / "novel_predictions.tsv", novels)
    # Sequence-level aggregation never sums assay values or evidence from duplicate names.
    grouped = defaultdict(list)
    for r in inventory:
        if r["qualifies"]:
            grouped[r["sequence_RNA"]].append(r)
    support = []
    for sequence, rs in sorted(grouped.items()):
        ids = sorted({r["study"] for r in rs})
        lirows = [r for r in rs if r["study"] == "li2016"]
        krrows = [r for r in rs if r["study"] == "krupova2023"]
        support.append(
            {
                "supporting_studies": ";".join(ids),
                "n_studies": len(ids),
                "names": ";".join(sorted({r["original_name"] for r in rs})),
                "li_materials": ";".join(
                    sorted(
                        {f for r in lirows for f in r["qualified_materials"].split(";")}
                    )
                ),
                "krupova_cow_replicates_above1_TPM": max(
                    (sum(v > 1 for v in kr_tpm[r["original_name"]]) for r in krrows),
                    default=0,
                ),
                "krupova_mean_TPM": max(
                    (sum(kr_tpm[r["original_name"]]) / 5 for r in krrows), default=""
                ),
                "interpretation": "Reference-sequence support; no demonstrated bovine RNA transfer or function in humans",
                **compare(sequence),
            }
        )
    sensitivity_ref = []
    for version in ["20", "21", "23_1"]:
        hr = [r["sequence"] for n, r in refs[version].items() if n.startswith("hsa-")]
        sequences = set(hr)
        seeds = {s[1:8] for s in hr}
        for r in support:
            sequence = r["sequence_RNA"]
            cl = (
                "exact_human_sequence"
                if sequence in sequences
                else "human_seed_only"
                if sequence[1:8] in seeds
                else "no_human_seed_match"
            )
            sensitivity_ref.append(
                {
                    "sequence_RNA": sequence,
                    "reference_version": version.replace("_", "."),
                    "human_class": cl,
                    "n_supporting_studies": r["n_studies"],
                }
            )
    write_tsv(out / "reference_sensitivity.tsv", sensitivity_ref)
    support.sort(key=lambda r: (-r["n_studies"], r["human_class"], r["sequence_RNA"]))
    write_tsv(out / "sequence_support.tsv", support)
    review = [
        r
        for r in support
        if r["n_studies"] == 2 and r["human_class"] != "exact_human_sequence"
    ]
    if review:
        write_tsv(out / "cross_study_review_pool.tsv", review)
    priority = [
        r
        for r in review
        if r["human_class"] == "no_human_seed_match"
        and r["current_bovine_exact_names"]
        and not r["five_prime_length_variant_names"]
    ]
    priority.sort(key=lambda r: -float(r["krupova_mean_TPM"]))
    if priority:
        write_tsv(out / "annotation_review_priority.tsv", priority)

    def classes(rs):
        return dict(Counter(r["human_class"] for r in rs))

    qc["comparison"] = {
        "human_reference": "miRBase 23.1",
        "human_annotation_records": len(human),
        "human_unique_sequences": len(human_seq),
        "reference_mature_records_parsed": len(refs["23_1"]),
        "known_study_annotation_rows": len(inventory),
        "qualifying_unique_sequences": len(support),
        "classes_all_qualifying": classes(support),
        "sequences_supported_in_both_studies": sum(
            r["n_studies"] == 2 for r in support
        ),
        "classes_supported_in_both": classes(
            [r for r in support if r["n_studies"] == 2]
        ),
        "cross_study_review_pool": len(review),
        "review_pool_simple_3prime_variants": sum(
            bool(r["three_prime_length_variant_names"]) for r in review
        ),
        "review_pool_simple_5prime_variants": sum(
            bool(r["five_prime_length_variant_names"]) for r in review
        ),
        "priority_for_annotation_review": len(priority),
        "classes_supported_in_both_by_reference": {
            v: dict(
                Counter(
                    r["human_class"]
                    for r in sensitivity_ref
                    if r["n_supporting_studies"] == 2 and r["reference_version"] == v
                )
            )
            for v in ["20", "21", "23.1"]
        },
        "numeric_measurements_exported": len(numeric),
        "qualifying_by_study": dict(
            Counter(r["study"] for r in inventory if r["qualifies"])
        ),
    }
    (out / "summary.json").write_text(
        json.dumps(qc, ensure_ascii=False, indent=2) + "\n"
    )
    inputs[str(Path(__file__).resolve().relative_to(ROOT))] = sha(Path(__file__))
    (out / "manifest.json").write_text(
        json.dumps(
            {
                "inputs": inputs,
                "outputs": {
                    p.name: sha(p)
                    for p in sorted(out.iterdir())
                    if p.is_file() and p.name != "manifest.json"
                },
                "software": {"openpyxl": openpyxl.__version__},
                "protocol": str(
                    (DATA / "sequence_comparison_protocol.json").relative_to(ROOT)
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(qc, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
