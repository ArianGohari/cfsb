"""Real local Arrow/LadybugDB/Graphviz integration; no network or fake DB fallback."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from litmine import engine, graph
from litmine.llm import digest

MISSING = [name for name in ('pyarrow', 'real_ladybug') if importlib.util.find_spec(name) is None]
if shutil.which('dot') is None:
    MISSING.append('Graphviz dot executable')

TEXT = 'PER2 binds TP53 in human cells. We measured binding by assay.'
ENTITIES = [dict(entity_id='UniProt:O15055', kind='Protein', name='PER2', taxon_id='NCBITaxon:9606'),
            dict(entity_id='UniProt:P04637', kind='Protein', name='TP53', taxon_id='NCBITaxon:9606'),
            dict(entity_id='NCBITaxon:9606', kind='Species', name='human')]
MENTIONS = [dict(entity_id=e['entity_id'], text=word, start=TEXT.index(word), end=TEXT.index(word) + len(word))
            for e, word in zip(ENTITIES, ('PER2', 'TP53', 'human'))]
CANDIDATE = dict(subject_id=ENTITIES[0]['entity_id'], object_id=ENTITIES[1]['entity_id'], predicate='BINDS',
                 quote=TEXT, subject_quote='PER2', object_quote='TP53', stance='supports', attribution='own_experiment',
                 attribution_quote='We measured binding by assay.',
                 context={'species_id': {'value': 'NCBITaxon:9606', 'quote': 'human'}})


def fixture():
    paper = dict(paper_id='PMID:123', pmid='123', doi=None, title='Circadian cancer',
                 publication_date='2020-01-02', source_ref='raw/source.json')
    document = dict(document_id='document:full', paper_id=paper['paper_id'], kind='fulltext',
                    text=TEXT, text_sha256=digest(TEXT.encode()), source_ref='raw/source.json')
    relation, evidence, _ = engine.validate_candidate(CANDIDATE, document, 0, len(TEXT),
                                                      dict(entities=ENTITIES, mentions=MENTIONS), 'extractor:fixture')
    event = dict(event_id='event:1', paper_id=paper['paper_id'], document_id=document['document_id'],
                 stage='fulltext_eligibility', decision='include', input_hash=document['text_sha256'], evidence_quote=TEXT)
    return dict(papers=[paper], documents=[document], entities=copy.deepcopy(ENTITIES), relations=[relation],
                evidence=[evidence], screening=[event], manifest=dict(schema_version=1, input_hashes={},
                active_event_ids=['event:1'], config={}))


def rehash(review):
    for row in review['relations']:
        old = row['relation_id']
        row['relation_id'] = 'relation:' + digest({k: v for k, v in row.items() if k != 'relation_id'})
        for ev in review['evidence']:
            if ev['relation_id'] == old:
                ev['relation_id'] = row['relation_id']
    for row in review['evidence']:
        row['evidence_id'] = 'evidence:' + digest({k: v for k, v in row.items() if k != 'evidence_id'})


@unittest.skipIf(bool(MISSING), 'Real export dependencies missing: ' + ', '.join(MISSING) + '; install pyarrow real-ladybug and Graphviz before parent verification')
class GraphTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / 'review.json'
        self.output = self.root / 'exports'
        self.review = fixture()

    def export(self, review=None):
        self.path.write_text(json.dumps(self.review if review is None else review), encoding='utf-8')
        return graph.export(self.path, self.output)

    def snapshot(self):
        return {p.name: p.read_bytes() for p in self.output.iterdir() if p.is_file()}

    def test_real_exports_queries_schema_and_rebuild(self):
        import pyarrow.parquet as pq
        import real_ladybug as lbug
        result = self.export()
        self.assertEqual(result['primary_counts'], dict(Paper=1, Document=1, Entity=3, Relation=1, Evidence=1,
                         HAS_DOCUMENT=1, HAS_EVIDENCE=1, ASSESSES=1, SUBJECT_OF=1, OBJECT=1))
        for table, schema in graph.schemas().items():
            data = pq.read_table(self.output / (table + '.parquet'))
            self.assertEqual(data.schema, schema)
            self.assertEqual(data.num_rows, len(self.review[table]))
        db = lbug.Database(self.output / 'graph.lbug', read_only=True, buffer_pool_size=64*1024*1024)
        try:
            conn = lbug.Connection(db)
            try:
                query = conn.execute('MATCH (p:Paper)-[:HAS_DOCUMENT]->(:Document)-[:HAS_EVIDENCE]->(:Evidence)-[:ASSESSES]->(r:Relation) RETURN p.pmid, r.predicate')
                self.assertEqual(query.get_next(), ['123', 'BINDS'])
                query.close()
            finally:
                conn.close()
        finally:
            db.close()
        self.assertEqual(ET.parse(self.output / 'graph.svg').getroot().tag, '{http://www.w3.org/2000/svg}svg')
        old_dot = (self.output / 'graph.dot').read_bytes()
        (self.output / 'user.txt').write_text('preserve')
        again = self.export()
        self.assertEqual(result['primary_counts'], again['primary_counts'])
        self.assertEqual(old_dot, (self.output / 'graph.dot').read_bytes())
        self.assertEqual((self.output / 'user.txt').read_text(), 'preserve')

    def test_empty_typed_tables(self):
        for table in graph.FIELDS:
            self.review[table] = []
        self.review['screening'] = []
        self.review['manifest']['active_event_ids'] = []
        result = self.export()
        self.assertTrue(all(n == 0 for n in result['primary_counts'].values()))
        import pyarrow.parquet as pq
        for table, schema in graph.schemas().items():
            actual = pq.read_table(self.output / (table + '.parquet'))
            self.assertEqual(actual.schema, schema)
            self.assertEqual(actual.num_rows, 0)

    def test_synthetic_notice_is_visible_with_either_flag_even_when_empty(self):
        for flag in ('qc', 'manifest', None):
            for empty in (False, True):
                with self.subTest(flag=flag, empty=empty):
                    self.review = fixture()
                    self.review['qc'] = {'synthetic_demo': flag == 'qc'}
                    self.review['manifest']['mode'] = 'synthetic_demo' if flag == 'manifest' else 'pilot_exploration'
                    if empty:
                        for table in graph.FIELDS:
                            self.review[table] = []
                        self.review['screening'] = []
                        self.review['manifest']['active_event_ids'] = []
                    result = self.export()
                    dot = (self.output / 'graph.dot').read_text()
                    root = ET.parse(self.output / 'graph.svg').getroot()
                    visible = ' '.join(e.text or '' for e in root.iter() if e.tag.endswith('}text'))
                    for content in (dot, visible, result['scientific_disclaimer']):
                        self.assertEqual('SYNTHETIC DEMO' in content, flag is not None)
                        self.assertIn('auto_pass is not biological truth', content)
                        if empty:
                            self.assertIn('No primary graph nodes; no biological proof.', content)
                    self.assertEqual(result['synthetic_demo'], flag is not None)
                    self.assertEqual(result['rendering']['max_nodes'], 500)

    def test_uncertain_and_empty_extraction_keep_included_report(self):
        self.review['evidence'][0]['validation_status'] = 'uncertain'
        rehash(self.review)
        result = self.export()
        self.assertEqual(result['tables']['evidence'], 1)
        self.assertEqual(result['primary_counts']['Evidence'], 0)
        self.assertEqual(result['primary_counts']['Relation'], 0)
        self.assertEqual(result['primary_counts']['Paper'], 1)
        self.assertEqual(result['primary_counts']['Document'], 1)
        self.review['evidence'] = []
        self.review['relations'] = []
        result = self.export()
        self.assertEqual(result['primary_counts']['HAS_DOCUMENT'], 1)

    def test_nonincluded_and_abstract_evidence_never_primary(self):
        self.review['screening'][0]['decision'] = 'unclear'
        result = self.export()
        self.assertEqual(result['tables']['evidence'], 1)
        self.assertTrue(all(n == 0 for n in result['primary_counts'].values()))
        self.review = fixture()
        abstract = dict(self.review['documents'][0], document_id='document:abstract', kind='abstract')
        self.review['documents'].append(abstract)
        self.review['evidence'][0]['document_id'] = abstract['document_id']
        rehash(self.review)
        result = self.export()
        self.assertEqual(result['primary_counts']['Document'], 1)
        self.assertEqual(result['primary_counts']['Evidence'], 0)

    def test_invalid_data_fails_before_any_publication(self):
        mutations = [
            lambda r: r['papers'].append(copy.deepcopy(r['papers'][0])),
            lambda r: r['documents'][0].update(paper_id='missing'),
            lambda r: r['documents'][0].update(text_sha256='0'*64),
            lambda r: r['evidence'][0].update(start=True),
            lambda r: r['evidence'][0].update(quote='invented'),
            lambda r: r['evidence'][0].update(subject_end=999),
            lambda r: r['evidence'][0].update(relation_id='missing'),
            lambda r: r['evidence'][0].update(stance='refutes'),
            lambda r: r['evidence'][0].update(score=float('nan')),
            lambda r: r['relations'][0].update(species_id='NCBITaxon:999'),
            lambda r: r['relations'][0].update(cell_line_id=ENTITIES[0]['entity_id']),
            lambda r: r['relations'][0].update(condition='invented'),
            lambda r: r['relations'][0].update(predicate='ACTIVATES'),
            lambda r: r['entities'][0].update(kind='Gene'),
            lambda r: r['entities'][0].update(taxon_id='9606'),
            lambda r: r['screening'][0].update(input_hash='bad'),
            lambda r: r['screening'].append(dict(r['screening'][0])),
            lambda r: r['documents'][0].update(kind='abstract'),
        ]
        for mutate in mutations:
            review = fixture()
            mutate(review)
            with self.subTest(mutate=mutate), self.assertRaises((ValueError, TypeError)):
                self.export(review)
            self.assertFalse(self.output.exists())

    def test_input_hash_and_authoritative_review_hash(self):
        source = self.root / 'source.txt'
        source.write_text('original')
        self.review['manifest']['input_hashes'] = {'source.txt': digest(source.read_bytes())}
        source.write_text('tampered')
        with self.assertRaisesRegex(ValueError, 'input_hash_mismatch'):
            self.export()
        self.review = fixture()
        outer = dict(self.review['manifest'], output_hashes={'review.json': 'bad'})
        (self.root / 'manifest.json').write_text(json.dumps(outer))
        with self.assertRaisesRegex(ValueError, 'review_hash_mismatch'):
            self.export()
        self.assertFalse(self.output.exists())

    def test_node_limit_refuses_without_truncation_and_null_is_unlimited(self):
        self.review['manifest']['config']['graph'] = {'max_nodes': 2}
        with self.assertRaisesRegex(ValueError, 'graph_max_nodes_exceeded'):
            self.export()
        self.assertFalse(self.output.exists())
        self.review['manifest']['config']['graph']['max_nodes'] = None
        self.assertTrue(self.export()['rendering']['complete'])
        self.assertEqual(graph._validated(self.review)[0]['evidence'][0]['quote'], TEXT)

    def test_dot_injection_and_deterministic_order(self):
        attack = '"]; evil [URL="https://evil.test", image="/etc/passwd"]; // <script>alert(1)</script> \\N\n'
        self.review['papers'][0]['paper_id'] = attack
        self.review['papers'][0]['title'] = attack
        self.review['documents'][0]['paper_id'] = attack
        self.review['screening'][0]['paper_id'] = attack
        self.export()
        root = ET.parse(self.output / 'graph.svg').getroot()
        titles = [e.text for e in root.iter() if e.tag.endswith('}title')]
        self.assertNotIn('evil', titles)
        self.assertFalse(any(e.tag.endswith('}script') or e.tag.endswith('}image') for e in root.iter()))
        first = (self.output / 'graph.dot').read_bytes()
        for table in graph.FIELDS:
            self.review[table].reverse()
        self.export()
        self.assertEqual(first, (self.output / 'graph.dot').read_bytes())

    def test_foreign_outputs_directories_and_symlinks_are_preserved(self):
        self.output.mkdir()
        path = self.output / 'graph.lbug'
        path.mkdir()
        with self.assertRaisesRegex(ValueError, 'unsafe_output'):
            self.export()
        self.assertTrue(path.is_dir())
        path.rmdir()
        path.write_text('user database')
        with self.assertRaisesRegex(ValueError, 'unowned_output_files'):
            self.export()
        self.assertEqual(path.read_text(), 'user database')
        path.unlink()
        path.symlink_to(self.path)
        with self.assertRaisesRegex(ValueError, 'unsafe_output'):
            self.export()
        self.assertTrue(path.is_symlink())

    def test_render_failure_keeps_previous_outputs_and_cleans_staging(self):
        self.export()
        before = self.snapshot()
        with patch.object(graph.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, ['dot'])):
            with self.assertRaises(subprocess.CalledProcessError):
                self.export()
        self.assertEqual(before, self.snapshot())
        self.assertFalse(list(self.root.glob('.litmine-graph-*')))
        with patch.object(graph, '_svg', side_effect=ValueError('bad svg')):
            with self.assertRaisesRegex(ValueError, 'bad svg'):
                self.export()
        self.assertEqual(before, self.snapshot())

    def test_publication_failure_rolls_back(self):
        self.export()
        before = self.snapshot()
        replace = graph.os.replace
        failed = False
        def fail_once(src, dst):
            nonlocal failed
            if not failed and Path(dst) == self.output / 'graph.dot':
                failed = True
                raise OSError('simulated publication failure')
            return replace(src, dst)
        with patch.object(graph.os, 'replace', side_effect=fail_once):
            with self.assertRaisesRegex(OSError, 'simulated'):
                self.export()
        self.assertEqual(before, self.snapshot())

    def test_changed_managed_file_is_not_overwritten(self):
        self.export()
        path = self.output / 'graph.dot'
        path.write_text('user edit')
        with self.assertRaisesRegex(ValueError, 'input_hash_mismatch'):
            self.export()
        self.assertEqual(path.read_text(), 'user edit')

    def test_actual_engine_review_contract(self):
        (self.root / 'full.txt').write_text(TEXT)
        (self.root / 'annotations.json').write_text(json.dumps(dict(paper_id='PMID:123', entities=ENTITIES, mentions=MENTIONS)))
        include = dict(decision='include', criterion_id='I1', reason='Relevant mechanism', evidence_quote='PER2')
        fulltext_include = dict(include, criteria_evidence={'I1': 'PER2 binds TP53', 'I2': 'We measured binding by assay.'},
                                conflicting_evidence=False)
        responses = {'title_abstract:*': include, 'fulltext_eligibility:*': fulltext_include,
                     'extract:*': {'candidates': [CANDIDATE]}}
        (self.root / 'fixture.json').write_text(json.dumps(responses))
        config = dict(_base_dir=str(self.root), seeds=[dict(pmid='123', title='PER2 and cancer', abstract='PER2 binds TP53', fulltext_path='full.txt')],
            annotations={'PMID:123': 'annotations.json'}, llm=dict(mode='fixture', fixture_path='fixture.json', model='synthetic'))
        path = engine.run(config, self.root / 'run')
        result = graph.export(path, self.output)
        self.assertEqual(result['tables']['documents'], 2)
        self.assertEqual(result['primary_counts']['Document'], 1)
        self.assertEqual(result['primary_counts']['Relation'], 1)
        self.assertTrue(result['synthetic_demo'])
        self.assertIn('SYNTHETIC DEMO', (self.output / 'graph.svg').read_text())
        # Exercise the updated multi-chunk evidence-bundle decision contract.
        (self.root / 'full.txt').write_text(TEXT + '\nReferences.')
        config['chunking'] = {'size': len(TEXT), 'overlap': 0}
        responses['fulltext_eligibility:*'] = [fulltext_include,
            dict(decision='unclear', criterion_id=None, reason='References only', evidence_quote=None,
                 criteria_evidence={}, conflicting_evidence=False)]
        responses['fulltext_decision:*'] = fulltext_include
        (self.root / 'fixture.json').write_text(json.dumps(responses))
        aggregate_path = engine.run(config, self.root / 'aggregate')
        aggregate = json.loads(aggregate_path.read_bytes())
        self.assertTrue(any(c['stage'] == 'fulltext_decision' and c['decision'] == 'include'
                            for c in aggregate['qc']['chunk_coverage']))
        aggregate_result = graph.export(aggregate_path, self.root / 'aggregate-export')
        self.assertEqual(aggregate_result['primary_counts']['Evidence'], 1)
        self.assertEqual(aggregate_result['primary_counts']['Relation'], 1)
        # A missing fulltext produces a paper-hash retrieval event, not a document.
        config['seeds'][0]['fulltext_path'] = 'missing.txt'
        path = engine.run(config, self.root / 'missing')
        self.assertEqual(graph.export(path, self.root / 'missing-export')['primary_counts']['Paper'], 0)


if __name__ == '__main__':
    unittest.main()
