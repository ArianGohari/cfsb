"""Offline/mocked checks: python3 -m unittest discover -s text_mining/tests -p test_sources.py -v"""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

# Also runnable before the parent agent creates the package.
spec = importlib.util.spec_from_file_location('sources', Path(__file__).parents[1] / 'litmine' / 'sources.py')
sources = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sources)
FIXTURES = Path(__file__).parent / 'fixtures' / 'sources'


class Response(io.BytesIO):
    status = 200


class SourcesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = self.root / 'run'
        self.network = patch.object(sources, 'urlopen', side_effect=AssertionError('unexpected network'))
        self.urlopen = self.network.start()
        self.addCleanup(self.network.stop)
        self.sleep = patch.object(sources.time, 'sleep')
        self.sleep.start()
        self.addCleanup(self.sleep.stop)

    def config(self, **kwargs):
        return dict(_base_dir=str(FIXTURES), **kwargs)

    def paper(self, **kwargs):
        return sources._paper(dict(pmid='123', doi='10.1234/test', pmcid='PMC456',
                                   title='Test title', abstract='Only abstract', **kwargs), '')

    def document(self):
        result = sources.retrieve(self.paper(fulltext_path='fulltext.txt'), self.config(), self.run)
        self.assertEqual(result['reason'], 'retrieved')
        return result['document']

    def write_json(self, name, payload):
        path = self.root / name
        path.write_text(json.dumps(payload), encoding='utf-8')
        return str(path)

    def test_seeds_preserve_attributes_and_doi_pmid_bridge(self):
        seeds = [dict(doi='https://doi.org/10.1234/TEST', fulltext_path='fulltext.txt',
                      license='private local', allow_remote_llm=True, custom={'keep': 1}),
                 dict(pmid='123'), dict(pmid='123', doi='10.1234/test')]
        result = sources.search(self.config(seeds=seeds), self.run)
        self.assertEqual(len(result['papers']), 1)
        paper = result['papers'][0]
        self.assertEqual(paper['paper_id'], 'PMID:123')
        self.assertEqual(paper['custom'], {'keep': 1})
        self.assertEqual(paper['fulltext_path'], 'fulltext.txt')
        self.assertTrue(paper['allow_remote_llm'])
        self.assertEqual(paper['license'], 'private local')
        records = result['records']
        self.assertEqual(len(records), 3)
        self.assertEqual(records[0]['duplicate_of'], '')
        self.assertEqual([r['duplicate_of'] for r in records[1:]], [records[0]['record_id']] * 2)
        self.assertEqual({r['paper_id'] for r in records}, {'PMID:123'})
        self.assertEqual(set(records[0]), {'record_id', 'search_id', 'source_identifier', 'paper_id', 'duplicate_of', 'raw_ref'})
        self.assertEqual(result['searches'][0]['completion_status'], 'complete')
        again = sources.search(self.config(seeds=seeds), self.run)
        self.assertEqual([r['record_id'] for r in records], [r['record_id'] for r in again['records']])

    def test_identifier_conflicts_quarantine_entire_connected_component(self):
        seeds = [dict(pmid='123'), dict(doi='10.1234/test'),
                 dict(pmid='123', doi='10.1234/test'), dict(pmid='999', doi='10.1234/test')]
        result = sources.search(self.config(seeds=seeds), self.run)
        self.assertEqual(result['papers'], [])
        self.assertTrue(all(r['paper_id'] == '' and r['duplicate_of'] == '' for r in result['records']))
        self.assertEqual(result['qc'][0]['reason'], 'identifier_conflict')

    def test_invalid_and_missing_identifiers_not_invented(self):
        result = sources.search(self.config(seeds=[{'title': 'No id'}, {'pmid': 'bad'},
                                                  {'doi': 'bad'}, {'paper_id': 'PMID:3', 'pmid': '4'}]), self.run)
        self.assertEqual(result['papers'], [])
        self.assertEqual(len(result['records']), 4)
        self.assertEqual(len(result['qc']), 4)

    def test_offline_is_default_and_limit_zero_is_incomplete(self):
        for limit in (10, 0):
            result = sources.search(self.config(search={'queries': ['clock'], 'max_records': limit}), self.run)
            self.assertEqual(result['papers'], [])
            self.assertEqual(result['searches'][0]['completion_status'], 'incomplete')
        self.urlopen.assert_not_called()

    def test_pagination_multi_query_dedup_and_replay(self):
        calls = []

        def respond(request, timeout):
            params = parse_qs(urlsplit(request.full_url).query)
            calls.append(params)
            index = 0 if params['cursorMark'] == ['*'] else 1
            return Response((FIXTURES / f'search_page_{index + 1}.json').read_bytes())

        self.urlopen.side_effect = respond
        settings = {'queries': ['clock', 'cancer'], 'page_size': 2, 'max_records': 10,
                    'from_year': 2000, 'to_year': 2020}
        result = sources.search(self.config(offline=False, search=settings), self.run)
        self.assertEqual(len(calls), 4)
        self.assertIn('FIRST_PDATE:[2000-01-01 TO 2020-12-31]', calls[0]['query'][0])
        self.assertEqual(len(result['records']), 6)
        self.assertEqual(len(result['papers']), 2)
        self.assertEqual({p['paper_id'] for p in result['papers']}, {'PMID:123', 'PMID:789'})
        self.assertEqual([m['completion_status'] for m in result['searches']], ['complete', 'complete'])
        self.urlopen.side_effect = AssertionError('replay attempted network')
        replay = sources.search(self.config(search=settings, replay_dir=str(self.run)), self.root / 'replay')
        self.assertEqual([p['paper_id'] for p in replay['papers']], [p['paper_id'] for p in result['papers']])
        self.assertEqual([r['record_id'] for r in replay['records']], [r['record_id'] for r in result['records']])
        for m in replay['searches']:
            for ref in m['raw_response_refs']:
                self.assertTrue(Path(ref).is_relative_to(self.root / 'replay'))

    def test_truncation_logged(self):
        self.urlopen.side_effect = lambda *a, **k: Response((FIXTURES / 'search_page_1.json').read_bytes())
        result = sources.search(self.config(offline=False, search={'queries': ['clock'], 'max_records': 2}), self.run)
        self.assertEqual(len(result['records']), 2)
        self.assertEqual(result['searches'][0]['reported_hits'], 3)
        self.assertEqual(result['searches'][0]['completion_status'], 'incomplete')
        self.assertTrue(any(q['reason'] == 'search_incomplete' for q in result['qc']))

    def test_repeated_cursor_cannot_double_count_or_loop(self):
        payload = {'hitCount': 3, 'nextCursorMark': 'again', 'resultList': {'result': [{'id': '123', 'source': 'MED', 'pmid': '123'}]}}
        self.urlopen.side_effect = lambda *a, **k: Response(json.dumps(payload).encode())
        result = sources.search(self.config(offline=False, search={'queries': ['clock']}), self.run)
        self.assertEqual(len(result['records']), 1)
        self.assertEqual(result['records'][0]['duplicate_of'], '')
        self.assertEqual(self.urlopen.call_count, 2)
        self.assertEqual(result['searches'][0]['completion_status'], 'incomplete')

    def test_empty_search_is_complete_but_missing_page_is_not(self):
        for hits, status in ((0, 'complete'), (1, 'incomplete')):
            payload = {'hitCount': hits, 'resultList': {'result': []}}
            self.urlopen.side_effect = lambda *a, **k: Response(json.dumps(payload).encode())
            result = sources.search(self.config(offline=False, search={'queries': [str(hits)]}), self.run)
            self.assertEqual(result['searches'][0]['completion_status'], status)

    def test_malformed_later_search_page_retries_and_preserves_attempts(self):
        first = (FIXTURES / 'search_page_1.json').read_bytes()
        second = (FIXTURES / 'search_page_2.json').read_bytes()
        malformed = b'{"version":"6.9"}'
        self.urlopen.side_effect = [Response(first), Response(malformed), Response(second)]
        config = self.config(offline=False, search={'queries': ['clock'], 'page_size': 2})
        result = sources.search(config, self.run)
        self.assertEqual(self.urlopen.call_count, 3)
        self.assertEqual(self.urlopen.call_args_list[1].args[0].full_url,
                         self.urlopen.call_args_list[2].args[0].full_url)
        self.assertEqual(result['searches'][0]['completion_status'], 'complete')
        self.assertEqual(result['searches'][0]['retrieved_records'], 3)
        self.assertFalse(any(q['reason'] == 'search_failed' for q in result['qc']))
        snapshots = {p: p.read_bytes() for p in (self.run / 'raw').rglob('*') if p.is_file()}
        self.assertEqual(sum(p.suffix == '.json' for p in snapshots), 3)
        self.assertIn(malformed, snapshots.values())
        self.urlopen.reset_mock()
        replay = sources.search(dict(config, offline=True), self.run)
        self.assertEqual(replay['records'], result['records'])
        self.urlopen.assert_not_called()
        self.assertEqual(snapshots, {p: p.read_bytes() for p in snapshots})

    def test_malformed_search_retries_are_bounded_and_never_zero_hits(self):
        payloads = [b'{"version":"6.9"}', b'{"hitCount":0}',
                    b'{"resultList":{"result":[]}}', b'not json',
                    b'{"hitCount":0,"resultList":{"result":null}}']
        for index, body in enumerate(payloads):
            for configured, expected in ((1, 1), (2, 2), (99, 5)):
                with self.subTest(body=body, attempts=configured):
                    self.urlopen.reset_mock()
                    self.urlopen.side_effect = lambda *a, **k: Response(body)
                    run = self.root / f'bad-{index}-{configured}'
                    result = sources.search(self.config(offline=False,
                        network={'max_attempts': configured}, search={'queries': ['clock']}), run)
                    self.assertEqual(self.urlopen.call_count, expected)
                    manifest = result['searches'][0]
                    self.assertEqual(manifest['completion_status'], 'incomplete')
                    self.assertIsNone(manifest['reported_hits'])
                    self.assertEqual(result['records'], [])
                    self.assertTrue(any(q['reason'] == 'search_failed' for q in result['qc']))
                    self.assertEqual(len(list((run / 'raw').rglob('*.json'))), expected)
                    self.assertTrue(Path(manifest['raw_response_refs'][0]).is_file())

    def test_cached_malformed_search_offline_fails_live_can_recover(self):
        config = self.config(offline=False, network={'max_attempts': 1},
                             search={'queries': ['clock']})
        self.urlopen.side_effect = lambda *a, **k: Response(b'{"version":"6.9"}')
        sources.search(config, self.run)
        snapshots = {p: p.read_bytes() for p in (self.run / 'raw').rglob('*') if p.is_file()}
        self.urlopen.reset_mock()
        offline = sources.search(dict(config, offline=True), self.run)
        self.assertEqual(offline['searches'][0]['completion_status'], 'incomplete')
        self.assertIsNone(offline['searches'][0]['reported_hits'])
        self.urlopen.assert_not_called()
        self.urlopen.side_effect = [Response(b'{"version":"6.9"}'),
                                   Response(b'{"hitCount":0,"resultList":{"result":[]}}')]
        recovered = sources.search(dict(config, network={'max_attempts': 2}), self.run)
        self.assertEqual(self.urlopen.call_count, 2)
        self.assertEqual(recovered['searches'][0]['completion_status'], 'complete')
        self.assertEqual(snapshots, {p: p.read_bytes() for p in snapshots})
        self.assertEqual(len(list((self.run / 'raw').rglob('*.json'))), 3)

    def test_valid_cached_search_wins_over_newer_malformed_200(self):
        self.urlopen.side_effect = lambda *a, **k: Response(b'{"hitCount":0,"resultList":{"result":[]}}')
        config = self.config(offline=False, search={'queries': ['clock']})
        valid = sources.search(config, self.run)
        url = self.urlopen.call_args.args[0].full_url
        sources._save(url, b'{"version":"6.9"}', 200, self.run)
        snapshots = {p: p.read_bytes() for p in (self.run / 'raw').rglob('*') if p.is_file()}
        self.urlopen.reset_mock()
        for offline in (True, False):
            result = sources.search(dict(config, offline=offline), self.run)
            self.assertEqual(result['searches'][0], valid['searches'][0])
        replay = sources.search(self.config(replay_dir=str(self.run), search=config['search']),
                                self.root / 'replay')
        self.assertEqual(replay['searches'][0]['completion_status'], 'complete')
        self.urlopen.assert_not_called()
        self.assertEqual(snapshots, {p: p.read_bytes() for p in snapshots})

    def test_search_http_and_content_retries_share_one_budget(self):
        self.urlopen.side_effect = [HTTPError(sources.EPMC, 503, 'busy', {}, io.BytesIO(b'busy')),
                                   Response(b'{"version":"6.9"}')]
        result = sources.search(self.config(offline=False, network={'max_attempts': 2},
                                           search={'queries': ['clock']}), self.run)
        self.assertEqual(self.urlopen.call_count, 2)
        self.assertEqual(result['searches'][0]['completion_status'], 'incomplete')
        self.assertEqual(len(list((self.run / 'raw').rglob('*.json'))), 2)

    def test_invalid_config_rejected(self):
        for settings in ({'queries': 'clock'}, {'page_size': 0}, {'max_records': -1},
                         {'from_year': 2020, 'to_year': 2000}, {'source': 'unknown'}):
            with self.assertRaises(ValueError):
                sources.search(self.config(search=settings), self.run)

    def test_retry_status_body_hash_and_immutable_cache(self):
        url = sources.EPMC + 'test'
        self.urlopen.side_effect = [HTTPError(url, 503, 'failure', {}, io.BytesIO(b'busy')),
                                   Response(b'{"ok":true}')]
        result = sources._fetch(url, {'offline': False, 'network': {'timeout': 2, 'max_attempts': 2}}, self.run)
        self.assertEqual(self.urlopen.call_count, 2)
        self.assertEqual(self.urlopen.call_args.kwargs['timeout'], 2)
        self.assertEqual(result[2]['http_status'], 200)
        files = {p: p.read_bytes() for p in (self.run / 'raw').rglob('*') if p.is_file()}
        self.assertEqual(len([p for p in files if p.suffix == '.json']), 2)
        self.assertEqual(sources._fetch(url, {}, self.run)[0], b'{"ok":true}')
        self.assertEqual(files, {p: p.read_bytes() for p in files})
        self.assertEqual(result[2]['sha256'], hashlib.sha256(result[0]).hexdigest())
        self.assertIn('+00:00', result[2]['fetched_at_utc'])

    def test_retries_bounded_and_no_credentials_in_exception_cache(self):
        self.urlopen.side_effect = URLError('secret-token-never-log')
        _, _, meta = sources._fetch(sources.EPMC + 'fail', {'offline': False, 'network': {'max_attempts': 2}}, self.run)
        self.assertEqual(meta['http_status'], 0)
        self.assertEqual(self.urlopen.call_count, 2)
        self.assertNotIn('secret-token', ''.join(p.read_text() for p in (self.run / 'raw').rglob('*.json')))

    def test_access_denied_is_not_retried(self):
        self.urlopen.side_effect = HTTPError(sources.EPMC, 403, 'denied', {}, io.BytesIO(b'denied'))
        _, _, meta = sources._fetch(sources.EPMC, {'offline': False}, self.run)
        self.assertEqual(meta['http_status'], 403)
        self.assertEqual(self.urlopen.call_count, 1)

    def test_cache_tampering_fails_closed(self):
        url = sources.EPMC + 'cached'
        _, ref, meta = sources._save(url, b'original', 200, self.run)
        (Path(ref).parent / meta['body']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'cache_hash_mismatch'):
            sources._fetch(url, {'offline': False}, self.run)
        self.urlopen.assert_not_called()

    def test_local_fulltext_base_dir_hash_permission_and_snapshot(self):
        document = self.document()
        text = (FIXTURES / 'fulltext.txt').read_text()
        self.assertEqual(document['text'], text)
        self.assertEqual(document['text_sha256'], hashlib.sha256(text.encode()).hexdigest())
        self.assertFalse(document['allow_remote_llm'])
        self.assertEqual(document['kind'], 'fulltext')
        self.assertTrue(Path(document['source_ref']).is_file())
        second = sources.retrieve(self.paper(fulltext_path='fulltext.txt', license='local-only', allow_remote_llm=True), self.config(), self.run)
        self.assertTrue(second['document']['allow_remote_llm'])
        self.assertEqual(second['document']['license'], 'local-only')
        self.assertEqual(second['document']['document_id'], document['document_id'])
        self.urlopen.assert_not_called()

    def test_missing_local_text_and_abstract_never_fulltext(self):
        result = sources.retrieve(self.paper(fulltext_path='missing.txt'), self.config(), self.run)
        self.assertIsNone(result['document'])
        path = self.root / 'abstract.txt'
        path.write_text('Only abstract')
        result = sources.retrieve(self.paper(fulltext_path=str(path)), self.config(), self.run)
        self.assertEqual(result['reason'], 'abstract_or_title_only')
        self.assertIsNone(result['document'])

    def test_xml_full_article_identity_body_and_license(self):
        paper = self.paper(fulltext_path='article.xml')
        result = sources.retrieve(paper, self.config(), self.run)
        self.assertEqual(result['reason'], 'retrieved')
        self.assertIn('TP53', result['document']['text'])
        self.assertEqual(result['document']['license'], 'CC BY 4.0')
        self.assertFalse(result['document']['allow_remote_llm'])
        self.assertNotIn('Only abstract', result['document']['text'])
        raw = (FIXTURES / 'article.xml').read_text()
        variants = [('wrong.xml', raw.replace('123</article-id>', '999</article-id>'), 'article_identity_mismatch'),
                    ('abstract.xml', raw.replace('<body>', '<back>').replace('</body>', '</back>'), 'missing_article_body'),
                    ('partial.xml', '<article><body><p>TP53</p></body></article>', 'missing_article_metadata')]
        for name, body, reason in variants:
            path = self.root / name
            path.write_text(body)
            outcome = sources.retrieve(self.paper(fulltext_path=str(path)), self.config(), self.run)
            self.assertIsNone(outcome['document'])
            self.assertEqual(outcome['reason'], reason)

    def test_oa_gate_and_remote_xml_replay(self):
        result = sources.retrieve(self.paper(), self.config(offline=False), self.run)
        self.assertEqual(result['reason'], 'oa_not_confirmed')
        self.urlopen.assert_not_called()
        self.urlopen.side_effect = lambda *a, **k: Response((FIXTURES / 'article.xml').read_bytes())
        paper = self.paper(isOpenAccess='Y')
        result = sources.retrieve(paper, self.config(offline=False), self.run)
        self.assertEqual(result['reason'], 'retrieved')
        self.assertEqual(self.urlopen.call_args.args[0].full_url, sources.EPMC + 'PMC456/fullTextXML')
        replay = sources.retrieve(paper, self.config(), self.run)
        self.assertEqual(replay, result)
        self.assertEqual(self.urlopen.call_count, 1)

    def test_local_annotations_unicode_spans(self):
        document = self.document()
        result = sources.annotate(document, self.paper(), self.config(annotations={'PMID:123': 'annotations.json'}), self.run)
        self.assertEqual(result['qc'], [])
        self.assertEqual(len(result['entities']), 2)
        for mention in result['mentions']:
            self.assertEqual(document['text'][mention['start']:mention['end']], mention['text'])
        self.assertEqual({e['entity_id'] for e in result['entities']}, {'NCBIGene:7157', 'NCBITaxon:9606'})
        self.urlopen.assert_not_called()

    def test_missing_annotations_explicit_qc(self):
        result = sources.annotate(self.document(), self.paper(), self.config(), self.run)
        self.assertEqual(result['mentions'], [])
        self.assertEqual(result['entities'], [])
        self.assertEqual(result['qc'][0]['detail'], 'annotations_not_configured')

    def test_invalid_annotation_identity_hash_spans_and_ids(self):
        original = json.loads((FIXTURES / 'annotations.json').read_text())
        document = self.document()
        for i, modify in enumerate((lambda p: p.update(paper_id='PMID:999'),
                                    lambda p: p.update(text_sha256='bad'),
                                    lambda p: p.update(mentions=[dict(entity_id='NCBIGene:7157', start=0, end=4, text='nope')]),
                                    lambda p: p.update(entities=[dict(entity_id='NCBIGene:7157;1', kind='Gene', name='TP53')]))):
            payload = json.loads(json.dumps(original))
            modify(payload)
            path = self.write_json(f'bad-{i}.json', payload)
            result = sources.annotate(document, self.paper(), self.config(annotations={'PMID:123': path}), self.run)
            self.assertEqual(result['mentions'], [])
            self.assertEqual(result['entities'], [])
            self.assertTrue(result['qc'])

    def test_pubtator_exact_alignment_and_identity(self):
        document = self.document()
        self.urlopen.side_effect = lambda *a, **k: Response((FIXTURES / 'pubtator.json').read_bytes())
        result = sources.annotate(document, self.paper(), self.config(offline=False, pubtator=True), self.run)
        self.assertEqual(len(result['mentions']), 1)
        self.assertEqual(result['entities'][0]['kind'], 'Gene')
        self.assertEqual(result['entities'][0]['entity_id'], 'NCBIGene:7157')
        self.assertEqual(result['qc'], [])
        self.assertNotIn('relations', result)
        replay = sources.annotate(document, self.paper(), self.config(pubtator=True), self.run)
        self.assertEqual(replay, result)
        self.assertEqual(self.urlopen.call_count, 1)
        payload = json.loads((FIXTURES / 'pubtator.json').read_text())
        params = parse_qs(urlsplit(self.urlopen.call_args.args[0].full_url).query)
        self.assertEqual(params, {'pmids': ['123'], 'full': ['true']})
        payload[0]['passages'][0]['offset'] = 100
        payload[0]['passages'][0]['annotations'][0]['locations'][0]['offset'] = 102
        local, qc = sources._bioc(payload, document, self.paper())
        self.assertEqual(qc, [])
        self.assertEqual(local['mentions'][0]['start'], 2)
        self.assertEqual(local['mentions'][0]['provenance']['source_start'], 102)
        payload[0]['id'] = '999'
        with self.assertRaisesRegex(ValueError, 'identity'):
            sources._bioc(payload, document, self.paper())

    def test_pubtator3_wrapper_numeric_pmc_identity_and_reanchoring(self):
        payload = json.loads((FIXTURES / 'pubtator.json').read_text())[0]
        payload.update(id='456', pmid=123, pmcid='PMC456')
        passage = payload['passages'][0]
        passage['offset'] = 1000
        passage['annotations'][0]['locations'][0]['offset'] = 1002
        self.urlopen.side_effect = lambda *a, **k: Response(json.dumps({'PubTator3': [payload]}).encode())
        result = sources.annotate(self.document(), self.paper(), self.config(offline=False, pubtator=True), self.run)
        self.assertEqual(result['qc'], [])
        mention = result['mentions'][0]
        self.assertEqual((mention['start'], mention['end']), (2, 6))
        self.assertEqual(mention['provenance']['source_start'], 1002)
        self.assertEqual(mention['provenance']['source_end'], 1006)
        self.assertEqual(mention['provenance']['source_passage_offset'], 1000)
        self.assertEqual(mention['provenance']['aligned_passage_offset'], 0)
        self.assertEqual(mention['provenance']['alignment'], 'exact_unique_passage')
        self.assertTrue(Path(mention['source_ref']).is_file())
        self.assertEqual(result['entities'][0]['kind'], 'Gene')
        for key, value in (('pmid', 999), ('pmcid', 'PMC999')):
            changed = dict(payload, **{key: value})
            with self.assertRaisesRegex(ValueError, 'identity'):
                sources._bioc({'PubTator3': [changed]}, self.document(), self.paper())
        passage['infons'] = {'article-id_doi': '10.1234/wrong'}
        with self.assertRaisesRegex(ValueError, 'identity'):
            sources._bioc({'PubTator3': [payload]}, self.document(), self.paper())

    def test_unmatched_and_ambiguous_passages_do_not_discard_aligned_passage(self):
        payload = json.loads((FIXTURES / 'pubtator.json').read_text())
        passage = payload[0]['passages'][0]
        for text, reason in (('TP53 absent', 'annotation_passage_not_found'),
                             ('TP53', 'annotation_passage_ambiguous'),
                             ('α  TP53', 'annotation_passage_not_found')):
            document = self.document()
            document['text'] += 'TP53\n'
            extra = dict(offset=2000, text=text, annotations=passage['annotations'][:1])
            payload[0]['passages'] = [passage, extra]
            local, qc = sources._bioc(payload, document, self.paper())
            self.assertEqual(len(local['mentions']), 1)
            self.assertEqual(qc[0]['reason'], reason)
        payload[0]['passages'] = [dict(offset=2, text='TP53', annotations=passage['annotations'][:1])]
        local, qc = sources._bioc(payload, document, self.paper())
        self.assertEqual(local['mentions'], [])
        self.assertEqual(qc[0]['reason'], 'annotation_passage_ambiguous')

    def test_pubtator_requires_pmid_and_explicit_protein_option(self):
        paper = self.paper()
        paper['pmid'] = ''
        result = sources.annotate(self.document(), paper, self.config(offline=False, pubtator=True), self.run)
        self.assertEqual(result['mentions'], [])
        self.assertEqual(result['qc'][0]['detail'], 'missing_or_invalid_pubtator_pmid')
        self.urlopen.assert_not_called()
        path = self.write_json('protein.json', {
            'paper_id': 'PMID:123',
            'entities': [{'entity_id': 'UniProt:P04637', 'kind': 'Protein', 'name': 'p53', 'taxon_id': '9606'}],
            'mentions': [{'entity_id': 'UniProt:P04637', 'start': 2, 'end': 6, 'text': 'TP53'}]})
        result = sources.annotate(self.document(), self.paper(), self.config(annotations={'PMID:123': path}), self.run)
        self.assertEqual(result['qc'], [])
        self.assertEqual(result['entities'][0]['kind'], 'Protein')
        self.assertEqual(result['entities'][0]['entity_id'], 'UniProt:P04637')

    def test_repeated_source_identifier_with_changed_identity_is_quarantined(self):
        rows = [dict(id='same', source='MED', pmid='123'),
                dict(id='same', source='MED', pmid='999')]
        responses = [Response(json.dumps(dict(hitCount=2, nextCursorMark=str(i),
                     resultList={'result': [row]})).encode()) for i, row in enumerate(rows)]
        self.urlopen.side_effect = responses
        result = sources.search(self.config(offline=False, search={'queries': ['clock'], 'page_size': 1, 'max_records': 2}), self.run)
        self.assertEqual(result['papers'], [])
        self.assertEqual(len(result['records']), 1)
        self.assertEqual(result['records'][0]['paper_id'], '')
        self.assertTrue(any(q['reason'] == 'identifier_conflict' for q in result['qc']))

    def test_malformed_api_responses_leave_search_incomplete(self):
        payloads = [b'not JSON', b'[]', b'{"hitCount":1}',
                    b'{"hitCount":1,"resultList":{"result":[null]}}']
        for i, payload in enumerate(payloads):
            self.urlopen.side_effect = lambda *a, **k: Response(payload)
            result = sources.search(self.config(offline=False, search={'queries': [str(i)]}), self.run)
            self.assertEqual(result['papers'], [])
            self.assertEqual(result['searches'][0]['completion_status'], 'incomplete')
            self.assertTrue(result['qc'])

    def test_pubtator_unresolved_ids_and_wrong_spans_have_qc(self):
        payload = json.loads((FIXTURES / 'pubtator.json').read_text())
        annotation = payload[0]['passages'][0]['annotations'][0]
        annotation['infons']['identifier'] = '7157;123'
        local, qc = sources._bioc(payload, self.document(), self.paper())
        self.assertEqual(local['mentions'], [])
        self.assertTrue(qc)
        annotation['infons']['identifier'] = '7157'
        annotation['locations'][0]['offset'] = 3
        local, qc = sources._bioc(payload, self.document(), self.paper())
        result = sources._validate_annotations(local, self.document(), self.paper())
        self.assertEqual(result['entities'], [])
        self.assertEqual(result['mentions'], [])
        self.assertEqual(qc[0]['detail'], 'source_span_mismatch')

    def test_local_snapshot_replays_when_original_is_gone(self):
        path = self.root / 'owned-fulltext.txt'
        path.write_text('TP53 full article text.\n', encoding='utf-8')
        paper = self.paper(fulltext_path=str(path))
        before = sources.retrieve(paper, self.config(), self.run)
        path.unlink()
        after = sources.retrieve(paper, self.config(replay_dir=str(self.run)), self.root / 'replay')
        self.assertEqual(before['document']['document_id'], after['document']['document_id'])
        self.assertEqual(before['document']['text'], after['document']['text'])
        self.urlopen.assert_not_called()

    def uniprot_row(self, accession='P04637', geneid='7157', taxon=9606):
        return {'entryType': 'UniProtKB reviewed (Swiss-Prot)', 'primaryAccession': accession,
                'organism': {'taxonId': taxon},
                'proteinDescription': {'recommendedName': {'fullName': {'value': 'Cellular tumor antigen p53'}}},
                'uniProtKBCrossReferences': [{'database': 'GeneID', 'id': geneid}]}

    def protein_config(self, **extra):
        return self.config(annotations={'PMID:123': 'annotations.json'}, protein_normalization=True, **extra)

    def cache_protein(self, rows, total=None, geneid='7157'):
        return sources._save(sources._protein_url(geneid), json.dumps({'results': rows}).encode(), 200,
                             self.run, response_headers={'x-total-results': str(len(rows) if total is None else total)})

    def test_protein_mapping_offline_retains_gene_adds_candidate_and_authoritative_taxon(self):
        self.cache_protein([self.uniprot_row()])
        document = self.document()
        baseline = sources.annotate(document, self.paper(), self.config(annotations={'PMID:123': 'annotations.json'}), self.run)
        result = sources.annotate(document, self.paper(), self.protein_config(max_protein_lookups=0), self.run)
        self.assertEqual(result['qc'], [])
        self.assertEqual(result['entities'][:len(baseline['entities'])], baseline['entities'])
        self.assertEqual(result['mentions'][:len(baseline['mentions'])], baseline['mentions'])
        protein = next(e for e in result['entities'] if e['kind'] == 'Protein')
        self.assertEqual(protein['entity_id'], 'UniProt:P04637')
        self.assertEqual(protein['taxon_id'], 'NCBITaxon:9606')
        mention = next(m for m in result['mentions'] if m['entity_id'] == protein['entity_id'])
        self.assertEqual(document['text'][mention['start']:mention['end']], 'TP53')
        self.assertTrue(mention['provenance']['protein_normalization']['candidate_only'])
        self.assertTrue(Path(mention['provenance']['protein_normalization']['source_ref']).exists())
        self.urlopen.assert_not_called()

    def test_protein_duplicate_reviewed_rows_and_mentions_do_not_duplicate_candidates(self):
        row = self.uniprot_row()
        self.cache_protein([row, row])
        result = sources.annotate(self.document(), self.paper(), self.protein_config(), self.run)
        self.assertEqual(result['qc'], [])
        self.assertEqual(len([e for e in result['entities'] if e['kind'] == 'Protein']), 1)
        self.assertEqual(len([m for m in result['mentions'] if m['entity_id'] == 'UniProt:P04637']), 1)
        sources._add_protein_candidates(result, self.paper(), self.protein_config(), self.run)
        self.assertEqual(len([m for m in result['mentions'] if m['entity_id'] == 'UniProt:P04637']), 1)

    def test_protein_ambiguous_mismatched_unreviewed_and_incomplete_abstain(self):
        gene = {'entity_id': 'NCBIGene:7157', 'kind': 'Gene', 'name': 'TP53', 'taxon_id': None}
        scenarios = [([self.uniprot_row(), self.uniprot_row('Q00987')], 2, 'ambiguous'),
                     ([self.uniprot_row(geneid='71570')], 1, 'geneid_mismatch'),
                     ([dict(self.uniprot_row(), entryType='UniProtKB unreviewed (TrEMBL)')], 1, 'not_reviewed'),
                     ([self.uniprot_row()], 2, 'incomplete'),
                     ([], 0, 'missing'),
                     ([self.uniprot_row(), self.uniprot_row(taxon=10090)], 2, 'record_conflict')]
        for rows, total, reason in scenarios:
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                sources._reviewed_protein(json.dumps({'results': rows}).encode(),
                                          {'response_headers': {'x-total-results': str(total)}}, gene)
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            sources._reviewed_protein(json.dumps({'results': [self.uniprot_row()]}).encode(), {}, gene)
        gene['taxon_id'] = 'NCBITaxon:10090'
        with self.assertRaisesRegex(ValueError, 'taxon_conflict'):
            sources._reviewed_protein(json.dumps({'results': [self.uniprot_row()]}).encode(),
                                      {'response_headers': {'x-total-results': '1'}}, gene)

    def test_protein_unavailable_keeps_original_annotations_and_qc(self):
        result = sources.annotate(self.document(), self.paper(), self.protein_config(), self.run)
        self.assertEqual(len(result['entities']), 2)
        self.assertEqual(len(result['mentions']), 2)
        self.assertEqual(result['qc'][0]['detail'], 'offline_cache_miss')
        self.urlopen.assert_not_called()
        self.cache_protein([self.uniprot_row(geneid='1')])
        result = sources.annotate(self.document(), self.paper(), self.protein_config(), self.run)
        self.assertEqual(result['qc'][0]['detail'], 'protein_geneid_mismatch')
        self.assertTrue(all(e['kind'] != 'Protein' for e in result['entities']))

    def test_protein_permission_failure_preserves_genes(self):
        self.urlopen.side_effect = HTTPError(sources.UNIPROT, 403, 'denied', {}, io.BytesIO(b'denied'))
        result = sources.annotate(self.document(), self.paper(),
                                 self.protein_config(offline=False, max_protein_lookups=1), self.run)
        self.assertEqual(len(result['entities']), 2)
        self.assertTrue(all(e['kind'] != 'Protein' for e in result['entities']))
        self.assertEqual(result['qc'][0]['detail'], 'http_403')
        self.assertEqual(self.urlopen.call_count, 1)
        self.assertEqual(sources.annotate(self.document(), self.paper(), self.protein_config(), self.run), result)

    def test_protein_run_budget_counts_failures_and_is_shared_across_calls(self):
        self.urlopen.side_effect = URLError('unavailable')
        config = {'offline': False, 'max_protein_lookups': 1, 'network': {'max_attempts': 5}}
        first = sources._protein_lookup(sources._protein_url('7157'), config, self.run)
        self.assertEqual(first[2]['http_status'], 0)
        self.assertEqual(self.urlopen.call_count, 1)
        self.assertEqual(sources._protein_lookup(sources._protein_url('7157'), config, self.run), first)
        with self.assertRaisesRegex(ValueError, 'budget_exhausted'):
            sources._protein_lookup(sources._protein_url('8864'), dict(config), self.run)
        self.assertEqual(self.urlopen.call_count, 1)
        self.assertEqual(len(list((self.run / 'raw' / 'protein_lookups').glob('*.json'))), 1)

    def test_protein_mocked_network_contract_headers_cache_and_replay(self):
        def respond(request, timeout):
            params = parse_qs(urlsplit(request.full_url).query)
            self.assertEqual(params['query'], ['(xref:geneid-7157) AND (reviewed:true)'])
            self.assertEqual(params['size'], ['2'])
            response = Response(json.dumps({'results': [self.uniprot_row()]}).encode())
            response.headers = {'x-total-results': '1'}
            return response
        self.urlopen.side_effect = respond
        document = self.document()
        config = self.protein_config(offline=False, max_protein_lookups=1)
        result = sources.annotate(document, self.paper(), config, self.run)
        self.assertEqual(result['qc'], [])
        self.assertEqual(self.urlopen.call_count, 1)
        self.assertEqual(sources.annotate(document, self.paper(), self.protein_config(), self.run), result)
        replay = sources.annotate(document, self.paper(), self.protein_config(replay_dir=str(self.run)), self.root / 'replay')
        self.assertEqual(replay['entities'], result['entities'])
        self.assertEqual(replay['qc'], [])
        self.assertEqual(self.urlopen.call_count, 1)
        self.assertFalse((self.root / 'replay' / 'raw' / 'protein_lookups').exists())

    def test_protein_disabled_by_default_and_zero_budget(self):
        self.cache_protein([self.uniprot_row()])
        result = sources.annotate(self.document(), self.paper(), self.config(annotations={'PMID:123': 'annotations.json'}), self.run)
        self.assertTrue(all(e['kind'] != 'Protein' for e in result['entities']))
        for limit in (0, -1, True):
            with self.assertRaises(ValueError):
                sources._protein_lookup(sources._protein_url('8864'),
                                        {'offline': False, 'max_protein_lookups': limit}, self.run)
        self.urlopen.assert_not_called()

    def test_uniprot_not_invented_or_gene_converted(self):
        for eid in ('UniProt:P04637', 'UniProt:A0A024RBG1'):
            self.assertEqual(sources._entity({'entity_id': eid, 'kind': 'Protein', 'name': 'p53'})['entity_id'], eid)
        for eid in ('UniProt:7157', 'UniProt:UNKNOWN', 'NCBIGene:7157'):
            with self.assertRaises(ValueError):
                sources._entity({'entity_id': eid, 'kind': 'Protein', 'name': 'p53'})


if __name__ == '__main__':
    unittest.main()
