"""Rules contract and offline engine checks."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from litmine import engine, rules


def annotated(text):
    entities = [dict(entity_id=name, name=name, kind='Protein') for name in ('PER2', 'TP53')]
    import re
    mentions = [dict(entity_id=m.group(), text=m.group(), start=m.start(), end=m.end())
                for m in re.finditer(r'\b(?:PER2|TP53)\b', text)]
    return dict(text=text, entities=entities, mentions=mentions)


class RulesTests(unittest.TestCase):
    def test_direction_passive_negation_speculation_and_cooccurrence(self):
        for text, subject in [('PER2 upregulates TP53.', 'PER2'),
                              ('TP53 upregulates PER2.', 'TP53'),
                              ('TP53 is upregulated by PER2.', 'PER2')]:
            with self.subTest(text=text):
                candidates = rules.extract(annotated(text))['candidates']
                self.assertEqual(len(candidates), 1)
                self.assertEqual(candidates[0]['subject_id'], subject)
        for text in ('PER2 does not bind TP53.', 'PER2 may bind TP53.',
                     'PER2 binds TP53, possibly.', 'PER2 and TP53 were measured.',
                     'We hypothesize that PER2 binds TP53.', 'PER2 never binds TP53.'):
            self.assertEqual(rules.extract(annotated(text))['candidates'], [], text)

    def test_uncertain_investigation_abstains(self):
        for text in ("We measured binding but didn't establish a mechanism.",
                     'We measured binding but didn’t establish a mechanism.',
                     'Our experiments are unlikely to establish a mechanism.',
                     'Our experiments likely establish a mechanism.'):
            with self.subTest(text=text):
                response = rules.screen('fulltext_eligibility', {'text': text})
                self.assertEqual(response['decision'], 'unclear')
                self.assertEqual(response['criteria_evidence'], {})

    def test_complex_tails_and_questions_abstain(self):
        for text in ('PER2 binds TP53 is unlikely.',
                     "PER2 binds TP53, but didn't in our experiments.",
                     'PER2 binds TP53 expression products.',
                     'PER2 binds TP53 only in a proposed model.',
                     'PER2 binds TP53 rather than directly interacting with it.',
                     'TP53 is bound by PER2 complexes.',
                     'We demonstrated that PER2 binds TP53 was an erroneous claim.',
                     'PER2 binds TP53?'):
            with self.subTest(text=text):
                self.assertEqual(rules.extract(annotated(text))['candidates'], [])
                response = rules.screen('fulltext_eligibility', {'text': text})
                self.assertNotIn('I1', response['criteria_evidence'])
        self.assertEqual(len(rules.extract(annotated('PER2 binds TP53 in human cells.'))['candidates']), 1)

    def test_review_exclusion_requires_explicit_self_description(self):
        for text in ('Smith calls this review comprehensive.',
                     'We consulted this review for background.',
                     'This review by Smith describes clock cancer biology.',
                     'This review describes clock cancer biology.',
                     'Smith wrote: this article is a review.',
                     'This article is a review?',
                     'This article is a review of another review by Smith.'):
            with self.subTest(text=text):
                self.assertEqual(rules.screen('fulltext_eligibility', {'text': text})['decision'], 'unclear')
        for text in ('This article is a review.', 'This paper is a systematic review.',
                     'Publication type: review.'):
            self.assertEqual(rules.screen('fulltext_eligibility', {'text': text})['decision'], 'exclude')

    def test_unknown_attribution_is_uncertain_and_own_statement_is_explicit(self):
        for text, attribution, status in [
                ('PER2 binds TP53. We measured binding by assay.', 'unknown', 'uncertain'),
                ('We demonstrated that PER2 binds TP53.', 'own_experiment', 'auto_pass')]:
            data = annotated(text)
            candidate = rules.extract(data)['candidates'][0]
            _, ev, _ = engine.validate_candidate(candidate, dict(document_id='doc', text=text),
                                                  0, len(text), data, 'rule')
            self.assertEqual(ev['attribution'], attribution)
            self.assertEqual(ev['validation_status'], status)

    def test_screening_never_excludes_missing_keywords_and_requires_both_criteria(self):
        for text, expected in [('Unrelated words.', 'unclear'), ('Circadian cancer.', 'include')]:
            self.assertEqual(rules.screen('title_abstract', {'text': text})['decision'], expected)
        for text, expected in [('PER2 and TP53. We measured binding.', 'unclear'),
                               ('PER2 binds TP53.', 'unclear'),
                               ('PER2 binds TP53. We measured binding by assay.', 'include'),
                               ('This article is a review.', 'exclude'),
                               ('We review measurements of PER2 and TP53.', 'unclear')]:
            decision = rules.screen('fulltext_eligibility', {'text': text})
            final = engine.validate_fulltext_decision(decision, {'text': text}, engine.CRITERIA,
                [engine.validate_screen(decision, text, engine.CRITERIA, 'fulltext_eligibility')])
            self.assertEqual(final['decision'], expected, text)

    def test_chunk_synthesis_preserves_separate_criteria(self):
        text = 'PER2 binds TP53. We measured binding by assay.'
        assessments = [engine.validate_screen(
            rules.screen('fulltext_eligibility', {'text': chunk}), chunk,
            engine.CRITERIA, 'fulltext_eligibility')
            for chunk in ('PER2 binds TP53.', 'We measured binding by assay.')]
        self.assertTrue(all(a['response_valid'] for a in assessments))
        self.assertEqual(assessments[1]['decision'], 'unclear')
        self.assertIsNone(assessments[1]['evidence_quote'])
        self.assertEqual(assessments[1]['criteria_evidence'], {'I2': 'We measured binding by assay.'})
        i2_only = rules.screen('fulltext_decision', {'assessments': assessments[1:]})
        self.assertEqual(engine.validate_fulltext_decision(
            i2_only, {'text': text}, engine.CRITERIA, assessments[1:])['decision'], 'unclear')
        invalid = dict(i2_only, criteria_evidence={'I2': 'Invented evidence.'})
        self.assertFalse(engine.validate_screen(
            invalid, text, engine.CRITERIA, 'fulltext_eligibility')['response_valid'])
        response = rules.screen('fulltext_decision', {'assessments': assessments})
        final = engine.validate_fulltext_decision(response, {'text': text}, engine.CRITERIA, assessments)
        self.assertEqual(final['decision'], 'include')
        self.assertEqual(set(final['criteria_evidence']), {'I1', 'I2'})

    def test_gene_protein_ambiguity_abstains_for_regulation(self):
        for verb, expected in [('upregulates', 0), ('binds', 1)]:
            data = annotated(f'We demonstrated that PER2 {verb} TP53.')
            data['entities'].append(dict(entity_id='NCBIGene:8864', kind='Gene', name='PER2'))
            data['mentions'].append(dict(data['mentions'][0], entity_id='NCBIGene:8864'))
            candidates = rules.extract(data)['candidates']
            self.assertEqual(len(candidates), expected)
            if candidates:
                self.assertEqual(candidates[0]['subject_id'], 'PER2')

    def test_request_ids_ignore_source_paths_and_replay_recomputes(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = annotated('PER2 binds TP53.')
            data['mentions'][0]['source_ref'] = '/first/raw.json'
            first = rules.Client({}, Path(tmp) / 'first').request('extract:doc:0', data, {})
            data['mentions'][0]['source_ref'] = '/second/raw.json'
            client = rules.Client({'llm': {'mode': 'replay', 'cache_dir': '/nonexistent'}}, Path(tmp) / 'second')
            second = client.request('extract:doc:0', data, {})
            self.assertEqual(first, second)
            self.assertEqual(client.calls, 0)
            self.assertEqual(client.mode, 'rules')
            self.assertNotIn('/second/', (client.root / second['request_id'] / 'request.json').read_text())

    def test_demo_engine_no_llm_and_included_without_relations(self):
        text = (Path(__file__).resolve().parents[1] / 'examples/demo/fulltext.txt').read_text()
        with tempfile.TemporaryDirectory() as tmp, \
                patch('litmine.llm.Client', side_effect=AssertionError('LLM forbidden')), \
                patch('litmine.sources.urlopen', side_effect=AssertionError('network forbidden')), \
                patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('network forbidden')):
            root = Path(tmp)
            (root / 'full.txt').write_text(text)
            data = annotated(text)
            ids = {'PER2': 'UniProt:O15055', 'TP53': 'UniProt:P04637'}
            for row in data['entities'] + data['mentions']:
                row['entity_id'] = ids[row['entity_id']]
            (root / 'annotations.json').write_text(json.dumps(dict(paper_id='PMID:123', entities=data['entities'], mentions=data['mentions'])))
            config = dict(_base_dir=tmp, offline=True, synthetic_demo=True, profile='legacy_clock',
                chunking={'size': 5, 'overlap': 0},
                seeds=[dict(pmid='123', title='Circadian cancer', abstract='PER2 and TP53.', fulltext_path='full.txt')],
                annotations={'PMID:123': 'annotations.json'})
            first = json.loads(engine.run(config, root / 'first').read_bytes())
            self.assertEqual(len(first['relations']), 1)
            self.assertEqual(first['evidence'][0]['validation_status'], 'uncertain')
            self.assertEqual(first['qc']['llm_calls'], 0)
            self.assertEqual(first['qc']['processing_mode'], 'rules')
            self.assertEqual(first['manifest']['rule_version'], rules.VERSION)
            self.assertEqual(first['manifest']['chunking']['unit'], 'whole_document')
            self.assertEqual(len(first['qc']['chunk_coverage']), 2)
            self.assertTrue(first['qc']['synthetic_demo'])
            self.assertFalse((root / 'first' / 'llm').exists())
            config['replay_dir'] = str(root / 'first')
            second = json.loads(engine.run(config, root / 'second').read_bytes())
            for table in ('relations', 'evidence', 'entities'):
                self.assertEqual(first[table], second[table])
            config.pop('replay_dir')
            config.pop('annotations')
            third = json.loads(engine.run(config, root / 'third').read_bytes())
            self.assertEqual(third['prisma_counts']['included_reports'], 1)
            self.assertEqual(third['relations'], [])


if __name__ == '__main__':
    unittest.main()
