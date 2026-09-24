"""Run the published demo and replay with actual Parquet, LadybugDB and Graphviz."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from litmine.__main__ import main


class CLITests(unittest.TestCase):
    def test_demo_replay_and_no_overwrite(self):
        self.check_demo('demo')

    def test_rules_replay_without_llm(self):
        with patch('litmine.llm.Client', side_effect=AssertionError('LLM forbidden')):
            self.check_demo('rules')

    def check_demo(self, example):
        config = Path(__file__).resolve().parents[1] / f'examples/{example}/config.json'
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / 'first', Path(directory) / 'second'
            with patch('litmine.sources.urlopen', side_effect=AssertionError('network forbidden')), patch(
                'urllib.request.OpenerDirector.open', side_effect=AssertionError('network forbidden')):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(main(['run', '--config', str(config), '--out', str(first)]), 0)
                    self.assertEqual(main(['replay', '--from-run', str(first), '--out', str(second)]), 0)
            a, b = (json.loads((folder / 'review.json').read_text()) for folder in (first, second))
            for name in ('papers', 'documents', 'entities', 'relations', 'evidence'):
                left = json.dumps(a[name], sort_keys=True).replace(str(first), '<run>')
                right = json.dumps(b[name], sort_keys=True).replace(str(second), '<run>')
                self.assertEqual(left, right, name)
            self.assertEqual(len(a['relations']), 1)
            self.assertEqual(b['qc']['llm_calls'], 0)
            self.assertTrue(b['qc']['synthetic_demo'])
            for folder in (first, second):
                svg = ET.parse(folder / 'graph.svg')
                self.assertIn('SYNTHETIC DEMO', ''.join(svg.getroot().itertext()))
                self.assertTrue((folder / 'graph.lbug').is_file())
                self.assertEqual(len(list(folder.glob('*.parquet'))), 5)
                if example == 'rules':
                    self.assertFalse((folder / 'llm').exists())
                    self.assertIn('BINDS', ''.join(svg.getroot().itertext()))
                    self.assertEqual(json.loads((folder / 'qc.json').read_text())['processing_mode'], 'rules')
            original = (first / 'review.json').read_bytes()
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(['review', '--config', str(config), '--out', str(first)]), 1)
            self.assertEqual((first / 'review.json').read_bytes(), original)

    def test_invalid_config_reports_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / 'invalid.json'
            config.write_text('[]')
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(['review', '--config', str(config), '--out', str(Path(directory) / 'out')]), 1)


if __name__ == '__main__':
    unittest.main()
