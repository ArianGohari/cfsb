"""Assess endpoint-dependent claims in the existing, assumed regulation grid.

No new simulations, biological parameter estimates, or probability statements.
"""

from pathlib import Path
import csv
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "output/part2/pfkl_regulation"
OUT = ROOT / "output/part2/pfkl_regulation_claims"


def main():
    manifest = json.loads((SOURCE / "manifest.json").read_text())
    for name in ["minima.tsv", "endpoints.tsv", "trajectories.tsv"]:
        path = SOURCE / name
        assert (
            hashlib.sha256(path.read_bytes()).hexdigest()
            == manifest["outputs"][str(path.relative_to(ROOT))]
        )
    rows = list(csv.DictReader((SOURCE / "minima.tsv").open(), delimiter="\t"))
    groups = {}
    for r in rows:
        key = tuple(float(r[k]) for k in ["q", "gamma", "duration"])
        groups.setdefault(key, {})[r["mechanism"]] = r
    comparisons = []
    for (q, gamma, duration), pair in sorted(groups.items()):
        d, t = pair["decay"], pair["translation"]
        ed, et = float(d["protein_end"]), float(t["protein_end"])
        md, mt = float(d["protein_minimum"]), float(t["protein_minimum"])
        lag = float(d["post_pulse_lag_tau"])
        # Independent closed form for the translation-only endpoint.
        assert abs(et - (q + (1 - q) * math.exp(-duration))) < 2e-9
        # Verify that the stored post-pulse extremum is actually a minimum:
        # E'=M-E=0 and E''=gamma*(1-M)>0 after the input is removed.
        if q < 1:
            m_at_min = 1 + (float(d["mRNA_end"]) - 1) * math.exp(-gamma * lag)
            assert abs(m_at_min - md) < 2e-9 and gamma * (1 - m_at_min) > 0
            assert ed > et and lag > 0 and md < ed
        else:
            assert max(abs(v - 1) for v in [ed, et, md, mt]) < 2e-9
        comparisons.append(
            dict(
                q=q,
                gamma=gamma,
                duration=duration,
                decay_end=ed,
                translation_end=et,
                decay_minimum=md,
                translation_minimum=mt,
                decay_minimum_lag=lag,
                endpoint_difference_pp=100 * (ed - et),
                minimum_difference_pp=100 * (md - mt),
                minimum_reverses_endpoint_ranking=md < mt - 2e-9,
            )
        )
    active = [r for r in comparisons if r["q"] < 1]
    reversals = [r for r in active if r["minimum_reverses_endpoint_ranking"]]
    example = next(
        r for r in active if (r["q"], r["gamma"], r["duration"]) == (0.25, 4.0, 0.25)
    )
    summary = dict(
        paired_grid_points=len(comparisons),
        active_pairs=len(active),
        delayed_decay_minimum_pairs=sum(r["decay_minimum_lag"] > 0 for r in active),
        minimum_ranking_reversals=reversals,
        counterexample=example,
        scope="Existing assumed grid only; frequencies are not probabilities or independent experiments.",
        structural_claims=[
            "For positive rates and finite nonzero pulse with q<1, decay has M<E at switch-off and hence continued protein decline.",
            "Translation-only has M=1 and immediate protein recovery after switch-off.",
            "At switch-off decay protein is higher than translation protein for matched q, gamma and duration.",
            "This endpoint ordering need not hold for the minimum over the full response.",
            "For an unchanged other-enzyme contribution f, relative activity reduction is (1-f)*(1-E).",
            "Changing absolute protein half-life rescales time only when dimensionless duration and gamma are held fixed.",
        ],
        not_established=[
            "human miR-6517 target function",
            "milk dose-response",
            "time in hours",
            "cellular glycolysis effect",
        ],
    )
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "comparisons.tsv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(comparisons[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(comparisons)
    (OUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    )
    inputs = [
        SOURCE / "minima.tsv",
        SOURCE / "endpoints.tsv",
        SOURCE / "trajectories.tsv",
        SOURCE / "manifest.json",
        Path(__file__).resolve(),
    ]
    outputs = [OUT / "comparisons.tsv", OUT / "summary.json"]
    (OUT / "manifest.json").write_text(
        json.dumps(
            {
                "inputs": {
                    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in inputs
                },
                "outputs": {
                    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in outputs
                },
            },
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(
            {
                "active_pairs": len(active),
                "ranking_reversals": len(reversals),
                "example": example,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
