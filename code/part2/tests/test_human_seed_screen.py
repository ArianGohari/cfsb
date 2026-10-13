"""Canonical-site fixtures, independent pairing oracle, and offline replay."""

import csv
import hashlib
import importlib.util
import json
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "code/part2/literature/milk_inventory/scan_human_seeds.py"
spec = importlib.util.spec_from_file_location("scan_human_seeds", SCRIPT)
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)


def pairing_oracle(transcript, mirna):
    """Enumerate miRNA-position-1 anchors, checking antiparallel base pairs."""
    complement = {"A": "T", "U": "A", "G": "C", "C": "G"}
    result = []
    # Anchor may lie just beyond the transcript for a terminal 7mer-m8.
    for anchor in range(6, len(transcript) + 1):
        core = all(transcript[anchor - i] == complement[mirna[i]] for i in range(1, 7))
        if not core:
            continue
        m8 = anchor >= 7 and transcript[anchor - 7] == complement[mirna[7]]
        a1 = anchor < len(transcript) and transcript[anchor] == "A"
        if m8 and a1:
            result.append((anchor - 7, anchor + 1, "8mer"))
        elif m8:
            result.append((anchor - 7, anchor, "7mer-m8"))
        elif a1:
            result.append((anchor - 6, anchor + 1, "7mer-A1"))
    return sorted(result)


class SeedScreenTests(unittest.TestCase):
    def test_site_classes_boundaries_and_overlaps(self):
        cases = {
            "CGTACGTA": [(0, 8, "8mer")],
            "CGTACGTC": [(0, 7, "7mer-m8")],
            "AGTACGTA": [(1, 8, "7mer-A1")],
            "GTACGTA": [(0, 7, "7mer-A1")],
            "CGTACGT": [(0, 7, "7mer-m8")],
            "CGTNCGTA": [],
            "TACGTACG": [],
            "CGTACGTACGTACGTA": [(0, 8, "8mer"), (4, 12, "8mer"), (8, 16, "8mer")],
        }
        for sequence, expected in cases.items():
            with self.subTest(sequence=sequence):
                self.assertEqual(scan.sites(sequence, "UACGUACGA"), expected)

    def test_independent_pairing(self):
        rng = random.Random(20261009)
        for _ in range(250):
            mirna = "".join(rng.choices("ACGU", k=22))
            random_bases = "".join(rng.choices("ACGTN", k=70))
            # Include a guaranteed complementary region amid background bases.
            paired = "".join(
                {"A": "T", "U": "A", "G": "C", "C": "G"}[x] for x in mirna[1:8][::-1]
            )
            sequence = random_bases[:35] + paired + random_bases[35:]
            self.assertEqual(
                scan.sites(sequence, mirna), pairing_oracle(sequence, mirna)
            )

    def test_replay_and_site_coordinates(self):
        output = scan.DEFAULT_OUT
        manifest = json.loads((output / "manifest.json").read_text())
        with tempfile.TemporaryDirectory(prefix="cfsb-seeds-") as temporary:
            subprocess.run(
                [sys.executable, str(SCRIPT), "--output", temporary],
                check=True,
                stdout=subprocess.DEVNULL,
            )
            for name in manifest["outputs"]:
                self.assertEqual(
                    (output / name).read_bytes(),
                    (Path(temporary) / name).read_bytes(),
                    name,
                )
            # Results and data hashes must agree; the reformatted source has its own hash.
            expected_manifest = dict(
                manifest, code_sha256=hashlib.sha256(SCRIPT.read_bytes()).hexdigest()
            )
            self.assertEqual(
                json.loads((Path(temporary) / "manifest.json").read_text()),
                expected_manifest,
            )
        sequences = {
            header.split("|")[0]: sequence for header, sequence in scan.fasta()
        }
        checked = 0
        with (output / "sites.tsv").open() as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                fragment = sequences[row["transcript_id"]][
                    int(row["transcript_start"]) - 1 : int(row["transcript_end"])
                ]
                self.assertEqual(fragment, row["site_DNA"])
                self.assertEqual(len(fragment), 8 if row["site_type"] == "8mer" else 7)
                checked += 1
        self.assertGreater(checked, 0)


if __name__ == "__main__":
    unittest.main()
