"""Validate and export the curated five-study pilot from Obsidian.

Species comes from sample provenance, never miRNA prefixes or reference genomes.
Run using PyYAML 6.0.3. No network access or changes to frozen source files.
"""

from pathlib import Path
from collections import defaultdict
import argparse
import csv
import hashlib
import json
import math
import statistics
import yaml

ROOT = Path(__file__).resolve().parents[4]
NOTES = ROOT / "obsidian/Projekt/Literatur/04 Datenextraktion/Milchbefunde"
BASE = ROOT / "output/part2/milk_inventory/sequence_comparison"
OUT = ROOT / "output/part2/milk_inventory/processing_pilot"
MILK_PRODUCTS = {
    "Milch",
    "Kolostrum",
    "Sahne",
    "Buttermilch",
    "Milchpulver",
    "Säuglingsnahrung als Pulver",
    "Kindernahrung als Pulver",
    "Formelnahrung flüssig",
}
COUNT_TYPES = {
    "Bekannte miRNA-Namen pro Fraktion",
    "Bekannte miRNA-Namen pro Pool",
    "Autorenmittelwert pro Tier",
}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    with p.open(newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def cow_eligible(r):
    return (
        r["Tierart"] == "Bos taurus"
        and r["Tierartstatus"] == "Bestätigt"
        and r["Materialklasse"] == "Milch"
        and r["Produkt"] in MILK_PRODUCTS
        and r["Prüfstatus"] == "Am Original geprüft"
    )


def count_eligible(r):
    return (
        cow_eligible(r)
        and r["Anzahltyp"] in COUNT_TYPES
        and r.get("Anzahl berichtet") is not None
        and r.get("Panelgröße") is None
    )


def validate_record(r):
    for k in [
        "Befund-ID",
        "DOI",
        "Tierart",
        "Tierartstatus",
        "Tierartbeleg",
        "Produkt",
        "Materialklasse",
        "Anzahltyp",
        "Prüfstatus",
        "Offene Frage",
        "Belegzeilen",
    ]:
        if not r.get(k):
            raise ValueError(f"Missing field {k}")
    if r.get("Anzahl berichtet") is not None:
        v = r["Anzahl berichtet"]
        if (
            isinstance(v, bool)
            or not isinstance(v, (int, float))
            or not math.isfinite(v)
            or v < 0
        ):
            raise ValueError("Invalid count")
    if r.get("Panelgröße") is not None and r["Anzahltyp"] in COUNT_TYPES:
        raise ValueError("Panel size cannot be inventory richness")
    if (
        r["Produkt"] == "Milchpulver"
        and r["Verarbeitung"]
        == "Frisch gewonnen; keine industrielle Verarbeitung untersucht"
    ):
        raise ValueError("Laboratory preparation cannot establish milk powder")
    if r["Tierartstatus"] == "Bestätigt" and r["Tierart"] not in {
        "Bos taurus",
        "Capra hircus",
        "Homo sapiens",
    }:
        raise ValueError("Confirmed species requires explicit single taxon")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    inputs = {}
    rows = []
    seen = set()
    samples = {}
    paths = []

    def track(p):
        inputs[str(p.relative_to(ROOT))] = sha(p)

    for p in sorted(NOTES.glob("*.md")):
        text = p.read_text()
        r = yaml.safe_load(text.split("\n---\n", 1)[0][4:])
        validate_record(r)
        assert r["Befund-ID"] not in seen
        seen.add(r["Befund-ID"])
        track(p)
        for pathkey, hashkey in [("PDF", "PDF SHA256"), ("Belegdatei", "Beleg SHA256")]:
            src = ROOT / r[pathkey]
            assert sha(src) == r[hashkey], src
            track(src)
        nlines = len((ROOT / r["Belegdatei"]).read_text().splitlines())
        assert all(1 <= n <= nlines for n in r["Belegzeilen"])
        r = {
            "Notiz": str(p.relative_to(ROOT)),
            **r,
            "Kuhdaten zulässig": cow_eligible(r),
            "Inventarzahl zulässig": count_eligible(r),
        }
        for sample in r["Proben"]:
            key = (r["Studien-ID"], sample)
            assert key not in samples
            samples[key] = r
        rows.append(r)
    frozen = json.loads((BASE / "manifest.json").read_text())
    track(BASE / "manifest.json")
    for name in ["measurements.tsv", "sample_mapping.tsv", "summary.json"]:
        p = BASE / name
        assert sha(p) == frozen["outputs"][name], p
        track(p)
    # Independent species metadata from the previously checked GEO sample records.
    for m in read(BASE / "sample_mapping.tsv"):
        group = samples[("krupova_2023_cow_goat_milk_ev_mirnomes", m["sample"])]
        assert group["Tierart"] == m["species"], (m, group["Tierart"])
    measurements = []
    per_sample = defaultdict(list)
    study_names = {
        "li2016": "li_2016_mirnome_milk_fat_whey_cells",
        "krupova2023": "krupova_2023_cow_goat_milk_ev_mirnomes",
    }
    for r in read(BASE / "measurements.tsv"):
        if r["annotation"] != "reported_known":
            continue
        key = (study_names[r["study"]], r["sample"])
        group = samples[key]
        if not cow_eligible(group):
            continue
        src = ROOT / r["source_path"]
        assert sha(src) == r["source_sha256"]
        track(src)
        measurements.append(
            {
                "Befund-ID": group["Befund-ID"],
                "species": group["Tierart"],
                "DOI": group["DOI"],
                **r,
            }
        )
        per_sample[(key[0], key[1], r["unit"])].append(r)
    sample_counts = []
    for (study, sample, unit), rs in sorted(per_sample.items()):
        if study.startswith("krupova") and unit != "reported_TPM_integer":
            continue
        assert len({r["original_name"] for r in rs}) == len(rs)
        values = [float(r["value"]) for r in rs]
        assert all(math.isfinite(v) and v >= 0 for v in values)
        if study.startswith("li_"):
            denominator = sum(values)
            assert denominator > 0
            count = sum(v / denominator * 1e6 >= 10 for v in values)
            rule = ">=10 CPM; Nenner = Summe publizierter bekannter miRNA-Reads; pro Bibliothek"
        else:
            count = sum(v > 1 for v in values)
            rule = ">1 publizierte gerundete TPM; pro Tier"
        group = samples[(study, sample)]
        sample_counts.append(
            {
                "Befund-ID": group["Befund-ID"],
                "Studie": group["Studie"],
                "sample": sample,
                "species": group["Tierart"],
                "n_miRNA_names": count,
                "rule": rule,
                "DOI": group["DOI"],
            }
        )

    def write(name, data):
        assert data
        target = out / name
        fields = list(dict.fromkeys(k for r in data for k in r))
        with target.open("w", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=fields, delimiter="\t", lineterminator="\n"
            )
            writer.writeheader()
            for r in data:
                writer.writerow(
                    {
                        k: json.dumps(v, ensure_ascii=False)
                        if isinstance(v, (dict, list))
                        else v
                        for k, v in r.items()
                    }
                )
        paths.append(target)

    write("befunde.tsv", rows)
    write("kuhmilch_befunde.tsv", [r for r in rows if cow_eligible(r)])
    write("berichtete_inventarzahlen.tsv", [r for r in rows if count_eligible(r)])
    write("nicht_fuer_kuhmilch.tsv", [r for r in rows if not cow_eligible(r)])
    write("messwerte.tsv", measurements)
    write("anzahlen_pro_probe.tsv", sample_counts)
    audit = []
    for r in rows:
        counts = [
            v["n_miRNA_names"]
            for v in sample_counts
            if v["Befund-ID"] == r["Befund-ID"]
        ]
        recomputed = None
        comparison = "Keine passende Nachrechnung vorhanden"
        if r["Befund-ID"].startswith("li_"):
            by_name = defaultdict(int)
            for (study, sample, unit), rs in per_sample.items():
                if samples[(study, sample)]["Befund-ID"] != r["Befund-ID"]:
                    continue
                total = sum(float(v["value"]) for v in rs)
                for v in rs:
                    by_name[v["original_name"]] += float(v["value"]) / total * 1e6 >= 10
            recomputed = sum(n >= 2 for n in by_name.values())
            assert recomputed == r["Anzahl berichtet"]
            comparison = "Reproduziert"
        elif r["Befund-ID"] == "krupova_cow":
            recomputed = statistics.mean(counts)
            comparison = (
                "Abweichung zum Artikel; gerundete hinterlegte TPM, Ursache ungeklärt"
            )
        audit.append(
            {
                "Befund-ID": r["Befund-ID"],
                "Berichtet": r["Anzahl berichtet"],
                "Berichtstyp": r["Anzahltyp"],
                "Nachgerechnet": recomputed,
                "Vergleich": comparison,
                "n Einzelwerte": len(counts),
            }
        )
    write("zahlenabgleich.tsv", audit)
    summary = {
        "studies": len({r["DOI"] for r in rows}),
        "observation_groups": len(rows),
        "cow_groups": sum(cow_eligible(r) for r in rows),
        "withheld_groups": sum(not cow_eligible(r) for r in rows),
        "reported_inventory_counts": sum(count_eligible(r) for r in rows),
        "known_mirna_measurements": len(measurements),
        "sample_count_records": len(sample_counts),
        "species_in_measurement_export": sorted({r["species"] for r in measurements}),
        "status": "Five-study pilot; primary matrices only for Li/Krupova; no completed systematic search; no pooled cross-study mean",
    }
    target = out / "summary.json"
    target.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    paths.append(target)
    track(Path(__file__))
    manifest = {
        "inputs": inputs,
        "outputs": {p.name: sha(p) for p in paths},
        "pyyaml": yaml.__version__,
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
