"""Task4 development checks. The source paragraph is not held-out evaluation data."""
import copy
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from litmine import engine, graph, rules, sources

FIXTURE = Path(__file__).parent / 'fixtures/task4_selected.json'


def annotated(text, names=None):
    names = names or {'STAT1': ('NCBIGene:6772', 'Gene'),
                      'IRF3': ('NCBIGene:3661', 'Gene'),
                      'Caco2': ('Cellosaurus:CVCL_0025', 'CellLine')}
    entities = [dict(entity_id=eid, kind=kind, name=name, taxon_id=None)
                for name, (eid, kind) in names.items()]
    mentions = [dict(entity_id=eid, start=m.start(), end=m.end(), text=m.group())
                for name, (eid, _) in names.items() for m in re.finditer(re.escape(name), text)]
    return dict(text=text, entities=entities, mentions=mentions)


class Task4Tests(unittest.TestCase):
    def test_real_selected_paragraph_and_provenance(self):
        data = json.loads(FIXTURE.read_text())
        candidates = rules.extract_assertions(data)['candidates']
        self.assertEqual({(c['subject_id'], c['predicate'], c['object_id']) for c in candidates}, {
            ('NCBIGene:3430', 'UPREGULATED_IN', 'Cellosaurus:CVCL_0025'),
            ('NCBIGene:3430', 'UPREGULATED_IN', 'Cellosaurus:CVCL_0609')})
        for candidate in candidates:
            relation, ev, issues = engine.validate_candidate(candidate,
                dict(document_id='doc', text=data['text']), 0, len(data['text']), data, 'rules', True)
            self.assertEqual(ev['attribution'], 'unknown')
            self.assertEqual(ev['validation_status'], 'assertion_pass')
            self.assertEqual(issues, ['unknown_attribution'])
            self.assertTrue(all(relation[k] is None for k in engine.CONTEXT))
            self.assertEqual(data['text'][ev['start']:ev['end']], ev['quote'])
            self.assertTrue(ev['source_locator'].startswith('unicode:'))

    def test_screening_is_independent_of_relation_detector(self):
        text = ('We investigated the proteomic response in Caco2 cells following SARS-CoV-2 infection. '
                'No direct interactions were measured.')
        with patch('litmine.rules.extract', side_effect=AssertionError('screening coupled to extraction')), \
             patch('litmine.rules.extract_assertions', side_effect=AssertionError('coupled')):
            response = rules.screen('fulltext_eligibility', dict(text=text, profile='task4_caco2_sarscov2'))
        final = engine.validate_fulltext_decision(response, {'text': text}, engine.TASK4_CRITERIA,
            [engine.validate_screen(response, text, engine.TASK4_CRITERIA, 'fulltext_eligibility')])
        self.assertEqual(final['decision'], 'include')
        self.assertEqual(rules.screen('fulltext_eligibility', dict(text=text, profile='clock_cancer'))['decision'], 'unclear')
        clock = 'We investigated circadian checkpoint regulation using proteomics.'
        self.assertEqual(rules.screen('fulltext_eligibility', dict(text=clock, profile='clock_cancer'))['decision'], 'include')
        self.assertEqual(rules.screen('fulltext_eligibility', dict(text=clock, profile='legacy_clock'))['decision'], 'unclear')

    def test_direction_attribution_and_unsupported_language(self):
        for text, subject, attribution in [
            ('STAT1 activates IRF3.', 'NCBIGene:6772', 'unknown'),
            ('STAT1 is inhibited by IRF3.', 'NCBIGene:3661', 'unknown'),
            ('STAT1 activates IRF3 (Smith et al., 2020).', 'NCBIGene:6772', 'cited_result'),
            ('We observed that STAT1 activates IRF3.', 'NCBIGene:6772', 'own_experiment')]:
            with self.subTest(text=text):
                items = rules.extract_assertions(annotated(text))['candidates']
                self.assertEqual(len(items), 1)
                self.assertEqual(items[0]['subject_id'], subject)
                self.assertEqual(items[0]['attribution'], attribution)
        for text in ['STAT1 does not activate IRF3.', 'STAT1 may activate IRF3.',
                     'STAT1 activates IRF3, possibly.', 'STAT1 activates IRF3 expression.',
                     'STAT1 and IRF3 were upregulated.', 'STAT1 activates IRF3?',
                     'STAT1 activates IRF3 but failed in Caco2 cells.',
                     'STAT1 activates IRF3 only in a proposed model.',
                     'STAT1 is upregulated in Caco2 cells relative to IRF3.',
                     'References\nSTAT1 activates IRF3.']:
            self.assertEqual(rules.extract_assertions(annotated(text))['candidates'], [], text)
        data = annotated('STAT1 activates IRF3.')
        data['mentions'].append(dict(data['mentions'][0], entity_id='NCBIGene:999'))
        data['entities'].append(dict(entity_id='NCBIGene:999', kind='Gene', name='ambiguous'))
        self.assertEqual(rules.extract_assertions(data)['candidates'], [])
        data = annotated('IFN activates IRF3.', {'IFN': ('NCBIGene:3456', 'Gene'), 'IRF3': ('NCBIGene:3661', 'Gene')})
        self.assertEqual(rules.extract_assertions(data)['candidates'], [])

    def test_unknown_does_not_bypass_other_validation_failures(self):
        data = annotated('STAT1 activates IRF3.')
        item = rules.extract_assertions(data)['candidates'][0]
        item['context'] = {'cell_line_id': {'value': 'Cellosaurus:CVCL_0025', 'quote': 'Caco2'}}
        _, ev, _ = engine.validate_candidate(item, dict(document_id='doc', text=data['text']),
                                             0, len(data['text']), data, 'rule', True)
        self.assertEqual(ev['validation_status'], 'uncertain')

    def test_real_end_to_end_offline_and_scopes(self):
        data = json.loads(FIXTURE.read_text())
        with tempfile.TemporaryDirectory() as tmp, \
             patch('litmine.llm.Client', side_effect=AssertionError('LLM forbidden')), \
             patch('litmine.sources.urlopen', side_effect=AssertionError('network forbidden')):
            root = Path(tmp)
            # Separate explicit eligibility text; never used as an evidence context.
            text = 'Caco2 SARS-CoV-2\nIn this study, we investigated protein abundance.\n' + data['text']
            delta = text.index(data['text'])
            (root / 'full.txt').write_text(text)
            payload = dict(data, mentions=[dict(m, start=m['start'] + delta, end=m['end'] + delta) for m in data['mentions']])
            (root / 'annotations.json').write_text(json.dumps(payload))
            config = dict(_base_dir=tmp, offline=True, profile='task4_caco2_sarscov2',
                seeds=[dict(pmid='33898942', title='Task4', fulltext_path='full.txt')],
                annotations={'PMID:33898942': 'annotations.json'}, graph={'scope': 'reported_assertions'})
            path = engine.run(config, root / 'run')
            review = json.loads(path.read_text())
            self.assertEqual(review['qc']['llm_calls'], 0)
            self.assertEqual(review['qc']['evidence_status_counts']['assertion_pass'], 2)
            result = graph.export(path, root / 'export')
            self.assertEqual(result['primary_counts']['Relation'], 2)
            self.assertEqual(result['primary_counts']['Evidence'], 2)
            self.assertIn('assertion_pass / unknown', (root / 'export/graph.dot').read_text())
            for scope in ('own_experiment', 'attributed'):
                scoped = copy.deepcopy(review)
                scoped['manifest']['config']['graph']['scope'] = scope
                self.assertEqual(graph._validated(scoped)[1]['evidence'], [])
            config['replay_dir'] = str(root / 'run')
            replay = json.loads(engine.run(config, root / 'replay').read_text())
            for table in ('entities', 'relations', 'evidence'):
                self.assertEqual(review[table], replay[table])

    def test_sentence_alignment_without_terminal_punctuation(self):
        sentence = 'IFI35 was upregulated in both Calu-3 and Caco2 cells'
        paper = {'pmid': '33898942', 'paper_id': 'PMID:33898942'}
        for ending in ('', '\nDifferent trailing passage'):
            with self.subTest(ending=ending):
                source = 'Different source introduction. ' + sentence + ending
                local = 'α Local introduction. ' + sentence.replace('both ', 'both\u00a0')
                annotation = dict(text='IFI35', infons={'type': 'Gene', 'identifier': '3430'},
                                  locations=[dict(offset=100 + source.index('IFI35'), length=5)])
                payload = {'id': '33898942', 'passages': [dict(
                    offset=100, text=source, annotations=[annotation])]}
                aligned, _ = sources._bioc(payload, {'text': local}, paper)
                self.assertEqual(len(aligned['mentions']), 1)
                mention = aligned['mentions'][0]
                self.assertEqual(mention['start'], local.index('IFI35'))
                self.assertEqual(local[mention['start']:mention['end']], 'IFI35')
                self.assertEqual(mention['provenance']['alignment'], 'whitespace_unique_sentence')
                self.assertEqual(sources._bioc(payload, {'text': local + '\n' + local}, paper)[0]['mentions'], [])
                annotation['locations'][0]['offset'] += 1
                aligned, qc = sources._bioc(payload, {'text': local}, paper)
                self.assertEqual(aligned['mentions'], [])
                self.assertTrue(any(q.get('detail') == 'source_span_mismatch' for q in qc))

    def test_sentence_alignment_and_pmid_link_require_exact_evidence(self):
        sentence = 'IFI35 was upregulated in both Calu-3 and Caco2 cells.'
        source = 'Prior work (citation removed). ' + sentence
        local = 'Prior work (Author et al., 2020). ' + sentence.replace('both ', 'both\u00a0')
        offset = 100
        annotation = dict(text='IFI35', infons={'type': 'Gene', 'identifier': '3430'},
                          locations=[dict(offset=offset + source.index('IFI35'), length=5)])
        payload = {'id': '8056843', 'passages': [dict(offset=offset, text=source, annotations=[annotation],
                   infons={'article-id_pmid': '33898942', 'article-id_pmc': '8056843'})]}
        paper = {'pmid': '33898942', 'paper_id': 'PMID:33898942'}
        aligned, _ = sources._bioc(payload, {'text': local}, paper)
        self.assertEqual(len(aligned['mentions']), 1)
        m = aligned['mentions'][0]
        self.assertEqual(local[m['start']:m['end']], 'IFI35')
        self.assertEqual(m['provenance']['alignment'], 'whitespace_unique_sentence')
        self.assertEqual(sources._bioc(payload, {'text': local + '\n' + local}, paper)[0]['mentions'], [])
        with self.assertRaisesRegex(ValueError, 'identity'):
            sources._bioc(payload, {'text': local}, dict(paper, pmid='123'))


if __name__ == '__main__':
    unittest.main()
