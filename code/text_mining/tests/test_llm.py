"""Offline checks for bounded requests, replay and upload permissions."""
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from litmine import llm


class Response(io.BytesIO):
    status = 200


class LLMTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.fixture = self.root / 'fixture.json'
        self.fixture.write_text(json.dumps({'title_abstract:*': {'decision': 'unclear'}}))
        self.config = {'llm': {'mode': 'fixture', 'fixture_path': str(self.fixture), 'model': 'test-model'}}
        self.network = patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('network forbidden'))
        self.mock_open = self.network.start()
        self.addCleanup(self.network.stop)

    def client(self, config=None, name='run'):
        return llm.Client(config or self.config, self.root / name)

    def request(self, client, **kwargs):
        return client.request('title_abstract:PMID:1', {'text': 'untrusted text'}, {'decision': 'string'}, **kwargs)

    def live(self, **kwargs):
        return self.client({'llm': dict(mode='live', model='test-model', base_url='https://example.invalid/v1', **kwargs)})

    def test_fixture_and_immutable_replay(self):
        first = self.request(self.client())
        self.assertEqual(first['status'], 'ok')
        replay = {'llm': dict(self.config['llm'], mode='replay', cache_dir=str(self.root / 'run' / 'llm'))}
        second = self.request(self.client(replay, 'replay'))
        self.assertEqual(second['response'], first['response'])
        self.assertTrue(second['cached'])
        self.assertEqual(second['origin_mode'], 'fixture')
        self.mock_open.assert_not_called()
        folder = self.root / 'run' / 'llm' / first['request_id']
        (folder / 'attempt-1.body').write_bytes(b'tampered')
        with self.assertRaises(llm.IntegrityError):
            self.request(self.client(replay, 'tampered'))

    def test_key_binds_schema_text_model_parameters(self):
        client = self.client({'llm': {'mode': 'replay'}})
        requests = [client.request('extract:x:0', data, schema) for data, schema in
                    [({'text': 'a'}, {'a': 1}), ({'text': 'b'}, {'a': 1}), ({'text': 'a'}, {'b': 1})]]
        other = self.client({'llm': {'mode': 'replay', 'temperature': 1}}, 'other')
        requests.append(other.request('extract:x:0', {'text': 'a'}, {'a': 1}))
        self.assertEqual(len({r['request_id'] for r in requests}), 4)
        self.assertTrue(all(r['status'] == 'cache_miss' for r in requests))

    def test_default_replay_and_fixture_only_explicit(self):
        client = self.client({'llm': {'fixture_path': str(self.fixture)}})
        self.assertEqual(self.request(client)['status'], 'cache_miss')
        self.assertEqual(client.calls, 0)

    def test_remote_gate_requires_both_permissions_even_abstract(self):
        for settings, permission in [({}, False), ({'allow_remote': True}, False), ({}, True)]:
            with self.subTest(settings=settings):
                result = self.request(self.live(**settings), allow_remote=permission)
                self.assertEqual(result['status'], 'remote_input_not_permitted')
        self.mock_open.assert_not_called()

    def test_http_hosted_refused(self):
        client = self.client({'llm': {'mode': 'live', 'base_url': 'http://example.invalid', 'allow_remote': True}})
        self.assertEqual(self.request(client, allow_remote=True)['status'], 'https_required')

    def test_explicit_key_no_scanning_or_recording(self):
        with patch.dict(os.environ, {'OTHER_API_KEY': 'do-not-scan', 'NAMED_KEY': 'secret-value'}):
            client = self.live(allow_remote=True, api_key_env='NAMED_KEY')
            self.mock_open.side_effect = None
            self.mock_open.return_value = Response(json.dumps({'choices': [{'message': {'content': '{"value":"secret-value"}'}}], 'usage': {'total_tokens': 9}}).encode())
            result = self.request(client, allow_remote=True)
            req = self.mock_open.call_args.args[0]
            self.assertEqual(req.get_header('Authorization'), 'Bearer secret-value')
            self.assertEqual(req.full_url, 'https://example.invalid/v1/chat/completions')
            self.assertEqual(result['response'], {'value': '[redacted]'})
            for path in (self.root / 'run').rglob('*'):
                if path.is_file():
                    self.assertNotIn(b'secret-value', path.read_bytes())
                    self.assertNotIn(b'do-not-scan', path.read_bytes())

    def test_retry_total_budget_and_timeout(self):
        client = self.live(allow_remote=True, max_calls=2, max_attempts=5, timeout=0.5)
        self.mock_open.side_effect = URLError('unavailable')
        first = self.request(client, allow_remote=True)
        second = client.request('extract:x:0', {'text': 'other'}, {}, True)
        self.assertEqual(client.calls, 2)
        self.assertEqual(len(first['attempt_refs']), 2)
        self.assertEqual(second['status'], 'budget_exhausted')
        self.assertEqual(self.mock_open.call_count, 2)
        self.assertEqual(self.mock_open.call_args.kwargs['timeout'], 0.5)

    def test_invalid_json_attempts_preserved(self):
        client = self.live(allow_remote=True, max_attempts=2)
        self.mock_open.side_effect = [Response(b'not json'), Response(b'{"choices":[{"message":{"content":"{}"}}]}')]
        result = self.request(client, allow_remote=True)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(len(result['attempt_refs']), 2)
        folder = self.root / 'run' / 'llm' / result['request_id']
        self.assertEqual((folder / 'attempt-1.body').read_bytes(), b'not json')

    def test_input_limit_no_network(self):
        client = self.live(max_input_chars=256, allow_remote=True)
        self.assertEqual(self.request(client, allow_remote=True)['status'], 'input_limit')
        self.assertEqual(client.calls, 0)
        self.mock_open.assert_not_called()

    def test_fixture_sequence(self):
        self.fixture.write_text(json.dumps({'title_abstract:*': [{'n': 1}, {'n': 2}]}))
        client = self.client()
        self.assertEqual(self.request(client)['response'], {'n': 1})
        self.assertEqual(client.request('title_abstract:PMID:2', {}, {})['response'], {'n': 2})

    def test_config_validation_and_sanitization(self):
        for field, value in [('max_calls', -1), ('max_attempts', 0), ('timeout', float('nan')), ('temperature', 3)]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.client({'llm': {field: value}})
        data = llm.sanitize({'llm': {'api_key': 'secret', 'api_key_env': 'NAME', 'max_output_tokens': 3},
                             'url': 'https://user:pass@host/path?key=secret'})
        self.assertEqual(data['llm']['api_key'], '[redacted]')
        self.assertEqual(data['llm']['api_key_env'], 'NAME')
        self.assertNotIn('secret', json.dumps(data))


if __name__ == '__main__':
    unittest.main()
