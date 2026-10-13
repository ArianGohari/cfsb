"""Temporary synthetic inputs only; never contact a service."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from litmine import engine, llm, sources

TEXT = 'PER2 binds TP53 in human cells. We measured binding by assay.'
ENTITIES = [{'entity_id': 'UniProt:O15055', 'kind': 'Protein', 'name': 'PER2', 'taxon_id': 'NCBITaxon:9606'},
            {'entity_id': 'UniProt:P04637', 'kind': 'Protein', 'name': 'TP53', 'taxon_id': 'NCBITaxon:9606'},
            {'entity_id': 'NCBITaxon:9606', 'kind': 'Species', 'name': 'human'}]
MENTIONS = [{'entity_id': ENTITIES[i]['entity_id'], 'start': TEXT.index(word), 'end': TEXT.index(word) + len(word), 'text': word}
            for i, word in enumerate(('PER2', 'TP53', 'human'))]
CANDIDATE = dict(subject_id=ENTITIES[0]['entity_id'], object_id=ENTITIES[1]['entity_id'], predicate='BINDS',
                 quote=TEXT, subject_quote='PER2', object_quote='TP53', stance='supports', attribution='own_experiment',
                 attribution_quote='We measured binding by assay.', experimental_method={'value': 'assay', 'quote': 'by assay'},
                 context={'species_id': {'value': 'NCBITaxon:9606', 'quote': 'human cells'}})


def include(quote):
    return dict(decision='include', criterion_id='I1', reason='Synthetic relevant mechanism and investigation.',
                evidence_quote=quote, criteria_evidence={'I1': quote, 'I2': quote})


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'full.txt').write_text(TEXT)
        (self.root / 'annotation.json').write_text(json.dumps(dict(paper_id='PMID:123', entities=ENTITIES, mentions=MENTIONS)))
        self.fixture = self.root / 'fixture.json'
        self.responses = {'title_abstract:*': include('Circadian cancer'), 'fulltext_eligibility:*': include('PER2 binds TP53'),
                          'extract:*': {'candidates': [CANDIDATE]}}
        self.config = dict(_base_dir=str(self.root), seeds=[dict(pmid='123', title='Circadian cancer', abstract='PER2 and TP53.', fulltext_path='full.txt')],
                           annotations={'PMID:123': 'annotation.json'},
                           llm={'mode': 'fixture', 'fixture_path': 'fixture.json', 'model': 'synthetic'})
        for target in ('litmine.sources.urlopen', 'urllib.request.OpenerDirector.open'):
            mock = patch(target, side_effect=AssertionError('network forbidden'))
            mock.start()
            self.addCleanup(mock.stop)

    def run_review(self, name='run'):
        self.fixture.write_text(json.dumps(self.responses))
        path = engine.run(self.config, self.root / name)
        return json.loads(path.read_bytes())

    def validate(self, item=None, text=TEXT, annotations=None):
        document = dict(document_id='doc', text=text)
        return engine.validate_candidate(item or copy.deepcopy(CANDIDATE), document, 0, len(text),
            annotations or {'entities': ENTITIES, 'mentions': MENTIONS}, 'extractor')

    def test_end_to_end_artifacts_counts_schema(self):
        review = self.run_review()
        self.assertEqual(review['papers'][0]['final_decision'], 'include')
        self.assertEqual(len(review['documents']), 2)
        self.assertEqual(len(review['relations']), 1)
        self.assertEqual(review['evidence'][0]['validation_status'], 'auto_pass')
        self.assertEqual(review['relations'][0]['species_id'], 'NCBITaxon:9606')
        self.assertIsNone(review['relations'][0]['condition'])
        self.assertEqual(review['prisma_counts']['included_reports'], 1)
        self.assertIsNone(review['prisma_counts']['studies'])
        self.assertTrue(all(review['prisma_counts']['identities'].values()))
        self.assertTrue(review['qc']['synthetic_demo'])
        self.assertEqual(review['qc']['evaluation']['extraction'], 'not_evaluated')
        for filename in ('records.csv', 'screening.csv', 'prisma_counts.json', 'qc.json', 'manifest.json', 'report.md'):
            self.assertTrue((self.root / 'run' / filename).exists())
        manifest = json.loads((self.root / 'run' / 'manifest.json').read_bytes())
        for name, expected in manifest['output_hashes'].items():
            self.assertEqual(llm.digest((self.root / 'run' / name).read_bytes()), expected)
        self.assertTrue(review['baseline']['candidates'])
        self.assertFalse(list((self.root / 'run').glob('*.parquet')))

    def test_replay_revalidates_without_network(self):
        first = self.run_review()
        self.config['llm'].update(mode='replay', cache_dir=str(self.root / 'run' / 'llm'))
        self.config['replay_dir'] = str(self.root / 'run')
        second = self.run_review('replay')
        for table in ('entities', 'relations', 'evidence'):
            self.assertEqual(first[table], second[table])
        self.assertEqual(second['qc']['llm_calls'], 0)
        self.assertTrue(second['qc']['synthetic_demo'])

    def test_prompt_annotations_keep_semantics_not_local_paths(self):
        original = dict(entity_id='UniProt:O15055', source_ref='/first/raw/annotation.json',
                        provenance={'protein_normalization': {
                            'gene_entity_id': 'NCBIGene:8864', 'candidate_only': True,
                            'source_ref': '/first/raw/mapping.json'}})
        replay = json.loads(json.dumps(original).replace('/first/', '/replay/'))
        prompt = engine._prompt_annotations([original])
        self.assertEqual(prompt, engine._prompt_annotations([replay]))
        self.assertNotIn('source_ref', json.dumps(prompt))
        self.assertIn('source_ref', original['provenance']['protein_normalization'])
        replay['provenance']['protein_normalization']['candidate_only'] = False
        self.assertNotEqual(prompt, engine._prompt_annotations([replay]))

    def test_empty_extraction_does_not_change_inclusion(self):
        self.responses['extract:*'] = {'candidates': []}
        review = self.run_review()
        self.assertEqual(review['prisma_counts']['included_reports'], 1)
        self.assertEqual(review['relations'], [])
        self.assertEqual(review['qc']['included_without_auto_pass_evidence'], ['PMID:123'])

    def test_unclear_abstract_forwards_and_unclear_fulltext_stays_open(self):
        unclear = dict(decision='unclear', reason='Insufficient evidence.', criterion_id=None, evidence_quote=None)
        self.responses.update({'title_abstract:*': unclear, 'fulltext_eligibility:*': unclear})
        review = self.run_review()
        self.assertEqual([e['decision'] for e in review['screening']], ['unclear', 'retrieved', 'unclear'])
        self.assertEqual(review['evidence'], [])
        self.assertEqual(review['qc']['llm_calls'], 2)

    def test_missing_abstract_still_retrieves(self):
        self.config['seeds'][0]['abstract'] = ''
        review = self.run_review()
        self.assertEqual(review['screening'][0]['decision'], 'unclear')
        self.assertEqual(review['prisma_counts']['included_reports'], 1)

    def test_missing_fulltext_is_not_exclusion(self):
        self.config['seeds'][0]['fulltext_path'] = 'missing.txt'
        review = self.run_review()
        self.assertEqual(review['screening'][-1]['decision'], 'not_retrieved')
        self.assertEqual(review['papers'][0]['final_decision'], 'unclear')
        self.assertEqual(review['prisma_counts']['fulltext_exclusions'], 0)

    def test_abstract_exclusion_stops_retrieval(self):
        self.responses['title_abstract:*'] = dict(decision='exclude', criterion_id='E1', reason='Outside scope.', evidence_quote='Circadian cancer')
        review = self.run_review()
        self.assertEqual(len(review['screening']), 1)
        self.assertEqual(review['prisma_counts']['forwarded_reports'], 0)

    def test_exclusion_requires_exact_nonempty_applicable_evidence(self):
        for quote, criterion in [('', 'E1'), ('invented', 'E1'), ('text', 'E99'), ('text', 'E2'), ('text', 'I1')]:
            with self.subTest(quote=quote, criterion=criterion):
                result = engine.validate_screen(dict(decision='exclude', reason='Reason', evidence_quote=quote, criterion_id=criterion),
                                                'text', engine.CRITERIA, 'title_abstract')
                self.assertEqual(result['decision'], 'unclear')

    def test_all_chunks_coverage_and_budget_incomplete(self):
        self.config['chunking'] = {'size': 30, 'overlap': 5}
        self.config['llm']['max_calls'] = 2
        review = self.run_review()
        coverage = [c for c in review['qc']['chunk_coverage'] if c['stage'] == 'fulltext_eligibility']
        self.assertEqual(coverage[0]['start'], 0)
        self.assertEqual(coverage[-1]['end'], len(TEXT))
        self.assertTrue(any(c['status'] == 'budget_exhausted' for c in coverage))
        self.assertEqual(review['papers'][0]['final_decision'], 'unclear')
        self.assertTrue(review['qc']['incomplete'])

    def test_contradictory_chunks_do_not_include(self):
        self.config['chunking'] = {'size': 35, 'overlap': 0}
        self.responses['fulltext_eligibility:*'] = [include('PER2 binds TP53'),
            dict(decision='exclude', criterion_id='E1', reason='Outside scope', evidence_quote='measured binding')]
        review = self.run_review()
        self.assertEqual(review['papers'][0]['final_decision'], 'unclear')

    def test_overlap_dedup(self):
        sentence = 'PER2 binds TP53.'
        text = 'x' * 30 + sentence + 'y' * 30
        (self.root / 'full.txt').write_text(text)
        mentions = [dict(m, start=m['start'] + 30, end=m['end'] + 30) for m in MENTIONS[:2]]
        (self.root / 'annotation.json').write_text(json.dumps(dict(paper_id='PMID:123', entities=ENTITIES[:2], mentions=mentions)))
        self.config['chunking'] = {'size': 60, 'overlap': 40}
        self.responses['fulltext_eligibility:*'] = include(sentence)
        self.responses['fulltext_decision:*'] = include(sentence)
        candidate = dict(CANDIDATE, quote=sentence, context={}, attribution='unknown', experimental_method=None)
        self.responses['extract:*'] = {'candidates': [candidate]}
        review = self.run_review()
        self.assertEqual(len(review['evidence']), 1)
        self.assertEqual(review['evidence'][0]['start'], 30)

    def test_unknown_entity_never_invents_relation(self):
        self.responses['extract:*']['candidates'] = [dict(CANDIDATE, subject_id='UniProt:P99999')]
        review = self.run_review()
        self.assertEqual(review['relations'], [])
        self.assertEqual(review['qc']['events'][-1]['validation_status'], 'rejected')
        self.assertEqual(review['prisma_counts']['included_reports'], 1)

    def test_offsets_quotes_and_types(self):
        for update in ({'quote': 'fabricated'}, {'subject_quote': 'TP53'}, {'subject_start': 1},
                       {'predicate': 'UNSUPPORTED'}, {'quote_start': True}):
            with self.subTest(update=update), self.assertRaises(ValueError):
                self.validate(dict(CANDIDATE, **update))
        annotations = copy.deepcopy({'entities': ENTITIES, 'mentions': MENTIONS})
        annotations['entities'][0]['kind'] = 'Gene'
        with self.assertRaises(ValueError):
            self.validate(annotations=annotations)

    def test_negation_reserved_stance_and_model_validation_flag(self):
        for stance in ('refutes', 'inconclusive'):
            rel, evidence, issues = self.validate(dict(CANDIDATE, stance=stance, validated=True, validation_status='auto_pass'))
            self.assertEqual(evidence['stance'], 'inconclusive')
            self.assertEqual(evidence['validation_status'], 'uncertain')
        text = TEXT + ' This may not be causal.'
        _, evidence, _ = self.validate(dict(CANDIDATE, quote=text), text=text)
        self.assertEqual(evidence['validation_status'], 'uncertain')

    def test_context_and_attribution_require_support(self):
        item = dict(CANDIDATE, attribution_quote='invented', context={
            'species_id': {'value': 'NCBITaxon:10090', 'quote': 'human'},
            'condition': {'value': 'cancer', 'quote': 'human'}})
        rel, evidence, issues = self.validate(item)
        self.assertIsNone(rel['species_id'])
        self.assertIsNone(rel['condition'])
        self.assertEqual(evidence['attribution'], 'unknown')
        self.assertEqual(evidence['validation_status'], 'uncertain')

    def test_binds_canonicalizes_argument_spans(self):
        item = dict(CANDIDATE, subject_id=CANDIDATE['object_id'], object_id=CANDIDATE['subject_id'],
                    subject_quote='TP53', object_quote='PER2')
        relation, evidence, _ = self.validate(item)
        self.assertEqual(relation['subject_id'], CANDIDATE['subject_id'])
        self.assertEqual(evidence['subject_start'], 0)

    def test_missing_annotations_no_primary_fallback(self):
        self.config.pop('annotations')
        review = self.run_review()
        self.assertEqual(review['relations'], [])
        self.assertEqual(review['prisma_counts']['included_reports'], 1)

    def test_duplicate_records_and_identity_checks(self):
        self.config['seeds'] *= 2
        review = self.run_review()
        self.assertEqual(review['prisma_counts']['identified_records'], 2)
        self.assertEqual(review['prisma_counts']['duplicates'], 1)
        with self.assertRaises(llm.IntegrityError):
            engine.prisma_counts(review['records'], review['papers'], review['screening'] * 2)

    def test_replay_miss_no_fabricated_inclusion(self):
        self.config['llm']['mode'] = 'replay'
        review = self.run_review()
        self.assertEqual(review['prisma_counts']['included_reports'], 0)
        self.assertEqual(review['papers'][0]['final_decision'], 'unclear')

    def test_malformed_screen_response_does_not_break_batch(self):
        self.responses['title_abstract:*'] = dict(decision='exclude', criterion_id=['E1'], reason='bad type', evidence_quote='Circadian cancer')
        review = self.run_review()
        self.assertEqual(review['screening'][0]['decision'], 'unclear')
        self.assertEqual(review['prisma_counts']['included_reports'], 1)

    def test_malformed_abstract_does_not_break_batch(self):
        self.config['seeds'][0]['abstract'] = ['not a string']
        review = self.run_review()
        self.assertEqual(review['screening'][0]['decision'], 'unclear')
        self.assertEqual(review['prisma_counts']['included_reports'], 1)

    def test_duplicate_quote_disambiguated_by_annotations(self):
        text = TEXT + '\n' + TEXT
        _, evidence, _ = self.validate(text=text)
        self.assertEqual(evidence['start'], 0)
        duplicated = MENTIONS + [dict(m, start=m['start'] + len(TEXT) + 1, end=m['end'] + len(TEXT) + 1) for m in MENTIONS]
        with self.assertRaisesRegex(ValueError, 'ambiguous_quote'):
            self.validate(text=text, annotations={'entities': ENTITIES, 'mentions': duplicated})

    def test_source_cache_integrity_errors_are_fatal(self):
        self.fixture.write_text(json.dumps(self.responses))
        with patch.object(sources, 'search', return_value={'qc': [{'reason': 'search_failed', 'detail': 'ValueError:cache_hash_mismatch'}]}):
            with self.assertRaises(llm.IntegrityError):
                engine.run(self.config, self.root / 'bad')

    def test_config_secrets_not_persisted(self):
        self.config['api_key'] = 'never-store-this'
        self.config['seeds'][0]['password'] = 'neither-this'
        self.run_review()
        for path in (self.root / 'run').rglob('*'):
            if path.is_file():
                self.assertNotIn(b'never-store-this', path.read_bytes())
                self.assertNotIn(b'neither-this', path.read_bytes())

    def mixed_chunks(self):
        (self.root / 'full.txt').write_text(TEXT + ' References only.'.ljust(len(TEXT)))
        self.config['chunking'] = {'size': len(TEXT), 'overlap': 0}
        positive = include('PER2 binds TP53')
        positive['criteria_evidence']['I2'] = 'We measured binding by assay.'
        self.responses['fulltext_eligibility:*'] = [positive,
            dict(decision='unclear', reason='No relevant evidence in references.', criterion_id=None, evidence_quote=None)]
        self.responses['fulltext_decision:*'] = positive

    def calls(self, name='run'):
        return json.loads((self.root / name / 'llm' / 'calls.json').read_bytes())

    def test_mixed_irrelevant_and_positive_chunks_synthesized_after_all_chunks(self):
        self.mixed_chunks()
        review = self.run_review()
        self.assertEqual(review['papers'][0]['final_decision'], 'include')
        calls = self.calls()
        stages = [c['task_id'].split(':')[0] for c in calls]
        self.assertEqual(stages[:4], ['title_abstract', 'fulltext_eligibility', 'fulltext_eligibility', 'fulltext_decision'])
        final = next(c for c in calls if c['task_id'].startswith('fulltext_decision:'))
        request = json.loads((self.root / 'run' / 'llm' / final['request_id'] / 'request.json').read_bytes())
        data = json.loads(request['payload']['messages'][1]['content'])['input_data']
        self.assertEqual(len(data['assessments']), 2)
        self.assertEqual(data['assessments'][0]['criteria_evidence']['I2'], 'We measured binding by assay.')
        self.assertEqual(data['assessments'][1]['decision'], 'unclear')
        self.assertEqual(review['screening'][-1]['request_ids'][-1], final['request_id'])
        # Eligibility succeeds, but unannotated reference chunks remain an explicit extraction gap.
        self.assertTrue(review['qc']['extraction_incomplete'])
        self.config['llm'].update(mode='replay', cache_dir=str(self.root / 'run' / 'llm'))
        self.config['replay_dir'] = str(self.root / 'run')
        replay = self.run_review('replay')
        self.assertEqual(replay['papers'][0]['final_decision'], 'include')
        self.assertEqual(replay['evidence'], review['evidence'])
        self.assertEqual(replay['qc']['llm_calls'], 0)

    def test_technical_or_invalid_chunk_blocks_synthesis(self):
        for case in ('budget', 'invalid_quote', 'invalid_unclear_quote', 'invalid_schema'):
            with self.subTest(case=case):
                self.mixed_chunks()
                self.config['llm']['max_calls'] = 2 if case == 'budget' else 100
                if case == 'invalid_quote':
                    self.responses['fulltext_eligibility:*'][1] = include('fabricated')
                elif case == 'invalid_unclear_quote':
                    self.responses['fulltext_eligibility:*'][1]['evidence_quote'] = 'fabricated'
                elif case == 'invalid_schema':
                    self.responses['fulltext_eligibility:*'][1] = {'decision': 'unclear'}
                review = self.run_review(case)
                self.assertEqual(review['papers'][0]['final_decision'], 'unclear')
                self.assertFalse(any(c['task_id'].startswith('fulltext_decision:') for c in self.calls(case)))
                self.assertTrue(review['qc']['incomplete'])
                self.assertEqual(len([c for c in review['qc']['chunk_coverage'] if c['stage'] == 'fulltext_eligibility']), 2)

    def test_explicit_semantic_conflict_blocks_synthesis(self):
        self.mixed_chunks()
        self.responses['fulltext_eligibility:*'][1]['conflicting_evidence'] = True
        review = self.run_review()
        self.assertEqual(review['papers'][0]['final_decision'], 'unclear')
        self.assertFalse(any(c['task_id'].startswith('fulltext_decision:') for c in self.calls()))

    def test_final_quotes_must_be_in_document_and_supplied_bundle(self):
        for quote in ('fabricated', 'in human cells'):
            with self.subTest(quote=quote):
                self.mixed_chunks()
                self.responses['fulltext_decision:*'] = dict(self.responses['fulltext_decision:*'], evidence_quote=quote)
                review = self.run_review('bad' if quote == 'fabricated' else 'outside_bundle')
                self.assertEqual(review['papers'][0]['final_decision'], 'unclear')

    def test_final_inclusion_needs_both_criteria_from_chunks(self):
        for case in ('final_missing_I1', 'chunk_missing_I1', 'chunk_missing_I2'):
            with self.subTest(case=case):
                self.mixed_chunks()
                final = copy.deepcopy(self.responses['fulltext_decision:*'])
                if case == 'final_missing_I1':
                    final.update(criterion_id='I2', evidence_quote='We measured binding by assay.',
                                 criteria_evidence={'I2': 'We measured binding by assay.'})
                else:
                    positive = self.responses['fulltext_eligibility:*'][0]
                    missing = case.removeprefix('chunk_missing_')
                    del positive['criteria_evidence'][missing]
                    if missing == 'I1':
                        positive.update(criterion_id='I2', evidence_quote='We measured binding by assay.')
                self.responses['fulltext_decision:*'] = final
                review = self.run_review(case)
                self.assertEqual(review['papers'][0]['final_decision'], 'unclear')

    def test_single_generic_I2_cannot_include(self):
        self.responses['fulltext_eligibility:*'] = dict(decision='include', criterion_id='I2',
            reason='An investigation', evidence_quote='We measured binding by assay.')
        review = self.run_review()
        self.assertEqual(review['papers'][0]['final_decision'], 'unclear')
        self.assertFalse(any(c['task_id'].startswith('fulltext_decision:') for c in self.calls()))

    def test_full_bundle_over_input_limit_stays_open_without_truncation(self):
        size = 1500
        text = ('A' * size) + ('B' * size) + ('C' * size)
        (self.root / 'full.txt').write_text(text)
        self.config['chunking'] = {'size': size, 'overlap': 0}
        self.config['llm']['max_input_chars'] = 4000
        self.responses['fulltext_eligibility:*'] = [dict(include(c), criteria_evidence={'I1': c}) for c in ('A' * size, 'B' * size, 'C' * size)]
        self.responses['fulltext_decision:*'] = include('A')
        review = self.run_review()
        coverage = review['qc']['chunk_coverage']
        # Each chunk fits; the combined validated evidence bundle does not.
        self.assertTrue(all(c['status'] == 'ok' for c in coverage if c['stage'] == 'fulltext_eligibility'))
        self.assertEqual(next(c['status'] for c in coverage if c['stage'] == 'fulltext_decision'), 'input_limit')
        self.assertEqual(review['papers'][0]['final_decision'], 'unclear')
        self.assertEqual(review['qc']['llm_calls'], 4)

    def test_missing_annotations_and_invalid_extraction_flag_incomplete(self):
        for case in ('absent', 'invalid_annotation', 'invalid_candidates', 'invalid_candidate'):
            with self.subTest(case=case):
                self.config['annotations'] = {'PMID:123': 'annotation.json'}
                self.responses['extract:*'] = {'candidates': []}
                if case == 'absent':
                    self.config['annotations'] = {}
                elif case == 'invalid_annotation':
                    self.config['annotations'] = {'PMID:123': 'missing.json'}
                elif case == 'invalid_candidates':
                    self.responses['extract:*'] = {'candidates': 'bad'}
                else:
                    self.responses['extract:*'] = {'candidates': [{'subject_id': 'invented'}]}
                review = self.run_review(case)
                self.assertEqual(review['prisma_counts']['included_reports'], 1)
                self.assertTrue(review['qc']['incomplete'])
                self.assertTrue(review['qc']['extraction_incomplete'])
                self.assertTrue(any(c['status'] != 'ok' for c in review['qc']['chunk_coverage']))

    def test_valid_empty_extraction_is_complete(self):
        self.responses['extract:*'] = {'candidates': []}
        review = self.run_review()
        self.assertFalse(review['qc']['incomplete'])
        self.assertFalse(review['qc']['extraction_incomplete'])
        self.assertEqual(review['relations'], [])

    def test_unknown_and_cited_attribution_never_count_as_own_experiments(self):
        for attribution in ('unknown', 'cited_result', 'model_prediction', 'review_summary'):
            with self.subTest(attribution=attribution):
                self.responses['extract:*'] = {'candidates': [dict(CANDIDATE, attribution=attribution)]}
                review = self.run_review(attribution)
                self.assertEqual(review['evidence'][0]['attribution'], attribution)
                counts = review['qc']['machine_support_reports_by_attribution']
                self.assertEqual(counts['own_experiment'], [])
                self.assertEqual(counts[attribution], [] if attribution == 'unknown' else ['PMID:123'])
                if attribution == 'unknown':
                    self.assertEqual(review['evidence'][0]['validation_status'], 'uncertain')

    def test_refuse_overwrite_and_tampered_document(self):
        self.run_review()
        with self.assertRaises(llm.IntegrityError):
            engine.run(self.config, self.root / 'run')
        with patch.object(sources, 'retrieve', return_value={'reason': 'retrieved', 'source_ref': '',
                'document': {'paper_id': 'PMID:123', 'text': TEXT, 'text_sha256': 'bad'}}):
            with self.assertRaises(llm.IntegrityError):
                self.run_review('bad')


if __name__ == '__main__':
    unittest.main()
