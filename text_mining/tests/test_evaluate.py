"""Synthetic engineering checks, not biological validation; no network access."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from litmine.evaluate import evaluate

RELATION = dict(subject_id='A', predicate='UPREGULATES', object_id='B',
                species_id=None, cell_line_id=None, condition=None, compartment=None)


class EvaluateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.review_path = self.root / 'review.json'
        self.gold_path = self.root / 'gold.json'
        self.output = self.root / 'evaluation.json'
        self.gold = dict(version=1, reports=[dict(paper_id='p1', split='test', screening='include',
            fulltext_eligibility='include', extraction_complete=True,
            relations=[dict(RELATION, attribution='own_experiment')]),
            dict(paper_id='p2', split='test', screening='exclude', extraction_complete=True, relations=[])])
        self.review = dict(manifest={'mode': 'synthetic_demo'},
            papers=[{'paper_id': 'p1'}, {'paper_id': 'p2'}],
            documents=[dict(document_id='abstract', paper_id='p1'),
                       dict(document_id='fulltext', paper_id='p1'), dict(document_id='negative', paper_id='p2')],
            screening=[dict(paper_id='p1', stage='title_abstract', decision='include'),
                       dict(paper_id='p2', stage='title_abstract', decision='exclude'),
                       dict(paper_id='p1', stage='fulltext_eligibility', decision='include')],
            relations=[dict(RELATION, relation_id='r1')],
            evidence=[dict(document_id='fulltext', relation_id='r1', validation_status='auto_pass',
                           stance='supports', attribution='own_experiment')],
            baseline=dict(screening=[dict(paper_id='p1', decision='include'), dict(paper_id='p2', decision='exclude')],
                          candidates=[dict(RELATION, paper_id='p1')]))
        mock = patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('network forbidden'))
        mock.start()
        self.addCleanup(mock.stop)

    def run_evaluation(self, gold=True, output=None):
        self.review_path.write_text(json.dumps(self.review))
        self.gold_path.write_text(json.dumps(self.gold))
        return evaluate(self.review_path, self.gold_path if gold else None, output or self.output)

    def test_reported_assertions_are_an_explicit_separate_scope(self):
        self.review['evidence'][0].update(validation_status='assertion_pass', attribution='unknown')
        self.gold['reports'][0]['relations'][0]['attribution'] = 'unknown'
        self.gold['annotation_source'] = 'independent automated agent; not human gold'
        for scope, tp in [('attributed', 0), ('reported_assertions', 1), ('own_experiment', 0)]:
            self.gold['prediction_scope'] = scope
            result = self.run_evaluation(output=self.root / (scope + '.json'))
            self.assertEqual(result['extraction']['exact_triple']['llm']['tp'], tp)
            self.assertEqual(result['reference_source'], self.gold['annotation_source'])
            self.assertEqual(result['scientific_quality'], 'not_evaluated')

    def test_no_gold(self):
        result = self.run_evaluation(gold=False)
        self.assertEqual(result['processing_mode'], 'llm')
        self.assertEqual(result['status'], 'not_evaluated')
        self.assertNotIn('screening', result)
        self.assertNotIn('extraction', result)
        self.assertIsNone(result['provenance']['gold_sha256'])

    def test_processing_mode_without_gold(self):
        for mode in ('rules', 'llm'):
            for source in ('qc', 'manifest', 'config'):
                with self.subTest(mode=mode, source=source):
                    self.review.pop('qc', None)
                    self.review['manifest'] = {}
                    target = (self.review.setdefault('qc', {}) if source == 'qc' else
                              self.review['manifest'].setdefault('config', {}) if source == 'config' else
                              self.review['manifest'])
                    target['processing_mode'] = mode
                    result = self.run_evaluation(gold=False, output=self.root / f'{mode}-{source}.json')
                    self.assertEqual(result['processing_mode'], mode)
                    self.assertEqual(result['status'], 'not_evaluated')
                    self.assertNotIn('screening', result)
                    self.assertNotIn('extraction', result)

    def test_rules_gold_labels_and_caveats(self):
        self.review['qc'] = dict(processing_mode='rules', rule_version='test-v1')
        self.review['manifest']['config'] = dict(processing_mode='rules')
        self.review['manifest']['rule_version'] = 'test-v1'
        self.review['evidence'].append(dict(self.review['evidence'][0], validation_status='uncertain'))
        result = self.run_evaluation()
        self.assertEqual(result['processing_mode'], 'rules')
        self.assertEqual(result['screening']['rules']['tp'], 1)
        self.assertEqual(result['screening']['fulltext_eligibility']['rules']['tp'], 1)
        extraction = result['extraction']
        self.assertEqual(set(extraction['exact_triple']), {'rules', 'baseline'})
        self.assertEqual(extraction['exact_triple']['rules']['tp'], 1)
        self.assertEqual(extraction['strict_context_attribution']['rules']['tp'], 1)
        self.assertEqual(extraction['rules_abstained_relations'], 1)
        self.assertIn('pipeline-selected texts', ' '.join(extraction['limitations']))
        self.assertNotIn('llm', self.output.read_text().lower())
        self.assertEqual(json.loads(self.output.read_bytes()), result)

    def test_metrics_provenance_and_fixture_warning(self):
        result = self.run_evaluation()
        self.assertEqual(result['extraction']['exact_triple']['llm']['recall'], 1)
        self.assertEqual(result['extraction']['exact_triple']['baseline']['precision'], 1)
        self.assertEqual(result['screening']['llm']['papers'], 2)
        self.assertEqual(result['screening']['baseline']['papers'], 2)
        self.assertEqual(result['screening']['llm']['tn'], 1)
        self.assertEqual(result['scientific_quality'], 'not_evaluated')
        self.assertIn('engineering fixtures', result['interpretation'])
        self.assertEqual(result['provenance']['gold_sha256'], hashlib.sha256(self.gold_path.read_bytes()).hexdigest())
        self.assertEqual(len(result['provenance']['evaluator_sha256']), 64)
        self.assertEqual(json.loads(self.output.read_bytes()), result)

    def test_output_labels_conditioned_baseline_extraction(self):
        self.run_evaluation()
        result = json.loads(self.output.read_bytes())
        caveat = ' '.join(result['extraction']['limitations'])
        self.assertIn('conditioned on pipeline-selected texts and available annotations', caveat)
        self.assertIn('not a standalone rule pipeline on all reports', caveat)
        self.assertIn('Recall includes losses from those gates', caveat)
        self.assertIn('screening baseline is independent of pipeline decisions', caveat)
        self.assertEqual(result['extraction']['paper_ids'], ['p1', 'p2'])
        self.assertEqual(result['extraction']['exact_triple']['baseline']['tp'], 1)

    def test_abstention_is_false_negative_not_true_negative(self):
        for row in self.review['screening']:
            row['decision'] = 'unclear'
        self.review['evidence'][0]['validation_status'] = 'uncertain'
        result = self.run_evaluation()
        self.assertEqual(result['screening']['llm']['fn'], 1)
        self.assertEqual(result['screening']['llm']['tn'], 0)
        self.assertEqual(result['screening']['llm']['abstention_rate'], 1)
        self.assertEqual(result['screening']['fulltext_eligibility']['llm']['fn'], 1)
        self.assertEqual(result['extraction']['exact_triple']['llm']['fn'], 1)
        self.assertEqual(result['extraction']['llm_abstained_relations'], 1)

    def test_hallucinated_false_positive_on_negative(self):
        self.review['evidence'].append(dict(self.review['evidence'][0], document_id='negative'))
        self.review['baseline']['candidates'].append(dict(RELATION, paper_id='p2'))
        result = self.run_evaluation()
        for method in ('llm', 'baseline'):
            metrics = result['extraction']['exact_triple'][method]
            self.assertEqual((metrics['tp'], metrics['fp'], metrics['precision']), (1, 1, 0.5))

    def test_direction_and_predicate_are_exact(self):
        self.review['relations'][0].update(subject_id='B', object_id='A', predicate='DOWNREGULATES')
        metric = self.run_evaluation()['extraction']['exact_triple']['llm']
        self.assertEqual((metric['tp'], metric['fp'], metric['fn']), (0, 1, 1))

    def test_strict_context_and_attribution_separate_from_triples(self):
        self.review['relations'][0]['condition'] = 'wrong context'
        self.review['evidence'][0]['attribution'] = 'cited_result'
        extraction = self.run_evaluation()['extraction']
        self.assertEqual(extraction['exact_triple']['llm']['tp'], 1)
        self.assertEqual(extraction['strict_context_attribution']['llm']['fp'], 1)
        self.assertEqual(extraction['strict_context_attribution']['llm']['fn'], 1)
        self.assertIn('experimental_method', extraction['baseline_unsupported_fields'])
        self.assertNotIn('baseline', extraction['strict_context_attribution'])

    def test_missing_attribution_excludes_entire_paper_only_from_strict(self):
        del self.gold['reports'][0]['relations'][0]['attribution']
        extraction = self.run_evaluation()['extraction']
        self.assertEqual(extraction['exact_triple']['llm']['tp'], 1)
        self.assertEqual(extraction['strict_context_attribution']['excluded_paper_ids'], ['p1'])
        self.assertEqual(extraction['strict_context_attribution']['paper_ids'], ['p2'])

    def test_duplicate_evidence_and_abstract_fulltext_count_once(self):
        self.review['evidence'].append(dict(self.review['evidence'][0], document_id='abstract'))
        self.review['baseline']['candidates'] *= 2
        extraction = self.run_evaluation()['extraction']
        self.assertEqual(extraction['exact_triple']['llm']['tp'], 1)
        self.assertEqual(extraction['exact_triple']['baseline']['tp'], 1)
        self.assertEqual(extraction['strict_context_attribution']['llm']['tp'], 1)

    def test_duplicate_paper_same_or_different_split_rejected(self):
        for split in ('test', 'train'):
            with self.subTest(split=split):
                self.gold['reports'] = [self.gold['reports'][0], dict(self.gold['reports'][0], split=split)]
                with self.assertRaisesRegex(ValueError, 'duplicate paper_id'):
                    self.run_evaluation()
                self.assertFalse(self.output.exists())

    def test_manifest_training_leakage(self):
        for location in ('manifest', 'config'):
            with self.subTest(location=location):
                self.review['manifest'] = {'training_paper_ids': ['p1']} if location == 'manifest' else {'config': {'training_paper_ids': ['p1']}}
                with self.assertRaisesRegex(ValueError, 'leakage'):
                    self.run_evaluation()

    def test_only_test_is_scored(self):
        self.gold['reports'][1]['split'] = 'train'
        self.review['evidence'].append(dict(self.review['evidence'][0], document_id='negative'))
        result = self.run_evaluation()
        self.assertEqual(result['test_paper_ids'], ['p1'])
        self.assertEqual(result['screening']['baseline']['papers'], 1)
        self.assertEqual(result['extraction']['exact_triple']['llm']['fp'], 0)

    def test_incomplete_annotation_rejected_including_empty_negatives(self):
        for index in (0, 1):
            with self.subTest(index=index):
                gold = copy.deepcopy(self.gold)
                self.gold['reports'][index]['extraction_complete'] = False
                with self.assertRaisesRegex(ValueError, 'extraction_complete'):
                    self.run_evaluation()
                self.gold = gold

    def test_missing_test_paper_rejected(self):
        self.review['papers'].pop()
        with self.assertRaisesRegex(ValueError, 'missing from review'):
            self.run_evaluation()

    def test_missing_decision_abstains(self):
        self.review['screening'] = []
        self.review['baseline']['screening'] = []
        result = self.run_evaluation()
        for method in ('llm', 'baseline'):
            self.assertEqual(result['screening'][method]['abstentions'], 2)
            self.assertEqual(result['screening'][method]['fn'], 1)

    def test_invalid_version_context_and_broken_references(self):
        original = copy.deepcopy(self.gold)
        self.gold['version'] = 2
        with self.assertRaisesRegex(ValueError, 'version'):
            self.run_evaluation()
        self.gold = original
        del self.gold['reports'][0]['relations'][0]['condition']
        with self.assertRaisesRegex(ValueError, 'context'):
            self.run_evaluation()
        self.gold['reports'][0]['relations'][0]['condition'] = None
        self.review['evidence'][0]['document_id'] = 'missing'
        with self.assertRaisesRegex(ValueError, 'reference'):
            self.run_evaluation()

    def test_exclusive_output_preserves_inputs_and_existing_output(self):
        self.run_evaluation()
        for path in (self.gold_path, self.review_path, self.output):
            before = path.read_bytes()
            with self.assertRaises(FileExistsError):
                evaluate(self.review_path, self.gold_path, path)
            self.assertEqual(path.read_bytes(), before)
        alias = self.root / 'alias.json'
        alias.symlink_to(self.gold_path)
        with self.assertRaises(FileExistsError):
            evaluate(self.review_path, self.gold_path, alias)

    def test_real_engine_output(self):
        import test_engine
        fixture = test_engine.EngineTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        review = fixture.run_review()
        self.review = review
        self.gold['reports'] = [dict(paper_id='PMID:123', split='test', screening='include',
            fulltext_eligibility='include', extraction_complete=True,
            relations=[dict({k: review['relations'][0][k] for k in RELATION}, attribution='own_experiment')])]
        result = self.run_evaluation()
        self.assertEqual(result['extraction']['exact_triple']['llm']['tp'], 1)
        self.assertEqual(result['extraction']['exact_triple']['baseline']['tp'], 1)
        self.assertEqual(result['extraction']['strict_context_attribution']['llm']['tp'], 1)
        self.assertEqual(result['screening']['fulltext_eligibility']['llm']['tp'], 1)


if __name__ == '__main__':
    unittest.main()
