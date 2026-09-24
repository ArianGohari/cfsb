import io
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import sbml_demo as demo


class DemoTests(unittest.TestCase):
    def test_originals_inventory_warnings_and_unchanged_bytes(self):
        expected = [
            ("f6f1bd3faf8223d8a32314e7422263568e88b1f662b9d2ee9f7e0300960d6328", 7, 17, 3, 0, 1),
            ("c412f691fb6dad00ebb96148ebdc52148b1f47949ad1dd139a0ea99c6ec6b389", 10, 21, 4, 2, 57),
        ]
        for path, (digest, species, reactions, rules, events, warnings) in zip(demo.MODELS.values(), expected):
            with self.subTest(path=path.name):
                result = demo.validate(path)
                self.assertTrue(result["ok"])
                self.assertEqual(result["read_diagnostics"], 0)
                self.assertEqual(result["severity_counts"], {"Warning": warnings})
                self.assertEqual(result["checkConsistency_return"], warnings)
                for key, count in [("species", species), ("reactions", reactions), ("rules", rules), ("events", events)]:
                    self.assertEqual(result["inventory"][key], count)
                self.assertEqual(result["sha256"], digest)
                self.assertEqual(demo.sha256(path.read_bytes()), digest)

    def test_cached_public_responses_and_comparison(self):
        directory = demo.HERE / "data" / "20260921T153214070366Z"
        summary = json.loads((directory / "summary.json").read_text())
        self.assertTrue(summary["ok"])
        self.assertEqual(len(summary["records"]), 2)
        for record in summary["records"]:
            self.assertEqual(len(record["requests"]), 3)
            for response in record["requests"]:
                self.assertEqual(response["status"], 200)
                self.assertEqual(demo.sha256((directory / response["body"]).read_bytes()), response["sha256"])
            original = demo.MODELS[record["record"]].read_bytes()
            current = (directory / record["downloads"][0]["file"]).read_bytes()
            self.assertEqual(original, current + b"\n" if record["record"] == "BIOMD0000000170" else current)
            self.assertTrue(demo.validate(directory / record["downloads"][0]["file"])["ok"])

    def test_invalid_xml_is_failure(self):
        with tempfile.TemporaryDirectory(dir=demo.HERE) as tmp:
            path = Path(tmp) / "invalid.xml"
            path.write_text("<sbml>")
            result = demo.validate(path)
            self.assertFalse(result["ok"])
            self.assertGreater(result["read_diagnostics"], 0)
            cli = subprocess.run([sys.executable, str(demo.HERE / "sbml_demo.py"), "validate", str(path),
                                  "--output", str(Path(tmp) / "report.json")], capture_output=True, text=True)
            self.assertEqual(cli.returncode, 1, cli.stderr)
            self.assertIn("FAIL", cli.stdout)

    def test_http_error_body_is_cached(self):
        url = "https://example.org/public"
        error = HTTPError(url, 403, "Forbidden", {"Date": "Mon, 21 Sep 2026 00:00:00 GMT"}, io.BytesIO(b"forbidden"))
        with tempfile.TemporaryDirectory(dir=demo.HERE) as tmp, patch.object(demo, "urlopen", side_effect=error):
            path = Path(tmp) / "response.raw"
            meta, raw = demo.request(url, path)
            self.assertEqual(meta["status"], 403)
            self.assertEqual(path.read_bytes(), b"forbidden")
            self.assertEqual(meta["sha256"], demo.sha256(raw))
            self.assertEqual(json.loads(path.with_suffix(".raw.json").read_text()), meta)
            self.assertIn("requested_at_utc", meta)

    def test_network_failure_is_recorded(self):
        with tempfile.TemporaryDirectory(dir=demo.HERE) as tmp, patch.object(demo, "urlopen", side_effect=URLError("offline")):
            meta, raw = demo.request("https://example.org/public", Path(tmp) / "response.raw")
            self.assertIsNone(meta["status"])
            self.assertIn("offline", meta["error"])
            self.assertEqual(raw, b"")


if __name__ == "__main__":
    unittest.main()
