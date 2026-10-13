"""Independent score checks and synthetic parameter recovery for the PFKL fit."""

import csv
import hashlib
import json
import math
import numpy as np
from fit_enzyme import fit, predict, rate, ROOT, OUT


def main():
    manifest = json.loads((OUT / "manifest.json").read_text())
    for group in ["inputs", "outputs"]:
        for name, digest in manifest[group].items():
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, (
                name
            )
    read = lambda name: list(csv.DictReader((OUT / name).open(), delimiter="\t"))
    held = read("held_out_predictions.tsv")
    for m in read("prediction_metrics.tsv"):
        rows = [
            r
            for r in held
            if r["model"] == m["model"]
            and (m["region"] == "all" or r["region"] == m["region"])
        ]
        err = [float(r["predicted"]) - float(r["observed"]) for r in rows]
        concentrations = sorted(set(r["held_out_mM"] for r in rows))
        errors = [
            sum(
                float(r["predicted"]) - float(r["observed"])
                for r in rows
                if r["held_out_mM"] == s
            )
            / sum(r["held_out_mM"] == s for r in rows)
            for s in concentrations
        ]
        for key, value in [
            ("rmse_individual", math.sqrt(sum(e * e for e in err) / len(err))),
            ("mae_individual", sum(abs(e) for e in err) / len(err)),
            ("rmse_means", math.sqrt(sum(e * e for e in errors) / len(errors))),
        ]:
            assert math.isclose(value, float(m[key]), rel_tol=1e-12)
    # Known synthetic parameters check the optimizer, not the biology.
    x = np.array([0, 0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4, 6.0])
    truth = np.array([0.3, 8.0, 1.7, 2.4])
    estimated, diag = fit(x, predict(x, truth))
    assert np.allclose(estimated, truth, rtol=1e-5, atol=1e-6)
    assert rate(0, 8, 1.7, 2.4) == 0 and np.isclose(rate(1.7, 8, 1.7, 2.4), 4)
    print(
        "PASS: source/output hashes, 27 independent score checks, synthetic parameter recovery and physical zero/half-maximum."
    )


if __name__ == "__main__":
    main()
