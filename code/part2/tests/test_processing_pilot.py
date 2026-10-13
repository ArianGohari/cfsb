"""Regression checks for species leakage and invalid inventory counts."""

import copy
import importlib.util
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    "pilot", ROOT / "code/part2/literature/milk_inventory/export_processing_pilot.py"
)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


class ProvenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {}
        for path in pilot.NOTES.glob("*.md"):
            row = yaml.safe_load(path.read_text().split("\n---\n", 1)[0][4:])
            cls.rows[row["Befund-ID"]] = row

    def test_goat_on_bovine_reference_is_not_cow(self):
        self.assertFalse(pilot.cow_eligible(self.rows["krupova_goat"]))
        self.assertFalse(pilot.count_eligible(self.rows["krupova_both"]))

    def test_human_sample_stays_excluded_even_with_bovine_label(self):
        row = copy.deepcopy(self.rows["krupova_cow"])
        row.update(
            {
                "Tierart": "Homo sapiens",
                "Referenzgenom": "Bos taurus",
                "miRNA": "bta-miR-148a",
            }
        )
        self.assertFalse(pilot.cow_eligible(row))

    def test_unknown_formula_cannot_be_promoted_by_mirna_name(self):
        row = copy.deepcopy(self.rows["chen_formula_infant"])
        row["miRNA"] = "bta-miR-148a"
        self.assertFalse(pilot.cow_eligible(row))

    def test_lab_freeze_drying_is_not_milk_powder(self):
        row = copy.deepcopy(self.rows["li_whey"])
        self.assertEqual(row["Produkt"], "Milch")
        row["Produkt"] = "Milchpulver"
        with self.assertRaises(ValueError):
            pilot.validate_record(row)

    def test_qpcr_panel_cannot_be_total_inventory(self):
        row = copy.deepcopy(self.rows["chen_formula_infant"])
        row.update({"Tierart": "Bos taurus", "Tierartstatus": "Bestätigt"})
        self.assertFalse(pilot.count_eligible(row))
        row["Anzahltyp"] = "Bekannte miRNA-Namen pro Pool"
        row["Anzahl berichtet"] = 7
        with self.assertRaises(ValueError):
            pilot.validate_record(row)

    def test_unknown_is_not_zero(self):
        self.assertIsNone(self.rows["shome_raw"]["Anzahl berichtet"])
        self.assertIsNone(self.rows["chen_formula_infant"]["Anzahl berichtet"])

    def test_joint_analysis_is_not_per_stage_count(self):
        self.assertFalse(pilot.count_eligible(self.rows["zhang_all"]))
        for key in ["zhang_raw", "zhang_pasteurized", "zhang_uht"]:
            self.assertIsNone(self.rows[key]["Anzahl berichtet"])

    def test_real_cow_positive_controls_and_pool_unit(self):
        for key in ["li_fat", "li_whey", "li_cell", "chen_mature", "chen_colostrum"]:
            self.assertTrue(pilot.count_eligible(self.rows[key]))
        self.assertEqual(self.rows["chen_mature"]["n unabhängig"], 1)
        self.assertEqual(self.rows["zhang_uht"]["n unabhängig"], 3)

    def test_heat_treatments_are_separate_branches(self):
        self.assertEqual(self.rows["zhang_pasteurized"]["Temperatur C"], 85)
        self.assertEqual(self.rows["zhang_uht"]["Temperatur C"], 135)
        for key in ["zhang_pasteurized", "zhang_uht"]:
            self.assertIn("Alternative", self.rows[key]["Verfahrenszweig"])


if __name__ == "__main__":
    unittest.main()
