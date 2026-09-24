"""Offline-Prüfung: Fehlerpfade, erster Versuch und Reportverweise."""
import ast
import contextlib
import io
import json
from pathlib import Path
import re
import runpy
import tempfile
from urllib.error import HTTPError, URLError
from unittest.mock import Mock, patch

BASE = Path(__file__).resolve().parent
namespace = runpy.run_path(str(BASE / 'pilot.py'))
fetch = namespace['fetch']
ast.parse((BASE / 'pilot.py').read_text())

# Simulierte Antworten testen Limits und Fehlerprotokollierung ohne Netzverkehr.
class Response(io.BytesIO):
    status = 200
    headers = {'Content-Type': 'application/json'}


def response(hits, results):
    return Response(json.dumps({'hitCount': hits, 'resultList': {'result': results}}).encode())


with tempfile.TemporaryDirectory(prefix='offline-test-', dir=BASE) as directory:
    temporary = Path(directory)
    (temporary / 'plan.json').write_bytes((BASE / 'plan.json').read_bytes())
    mock = Mock(side_effect=[
        response(2, [{'source': 'MED', 'id': '1'}]),
        response(0, []),
        URLError('offline injected failure'),
        HTTPError('https://example.invalid', 503, 'offline injected failure', {}, io.BytesIO(b'unavailable')),
    ])
    with patch.dict(fetch.__globals__, BASE=temporary, urlopen=mock):
        with contextlib.redirect_stdout(io.StringIO()):
            assert fetch() == 1
        entries = json.loads((temporary / 'manifest.json').read_text())['searches']
        assert mock.call_count == 4, 'Unexpected retry'
        assert [e['completion_status'] for e in entries] == [
            'limited_first_page', 'complete_query', 'error', 'error']
        assert entries[0]['hitCount'] == 2 and entries[0]['retrieved_records'] == 1
        assert entries[2]['raw_ref'] is None and entries[2]['http_status'] is None
        assert 'URLError' in entries[2]['error']
        assert entries[3]['http_status'] == 503
        assert (temporary / entries[3]['raw_ref']).read_bytes() == b'unavailable'
        try:
            fetch()
        except FileExistsError:
            pass
        else:
            raise AssertionError('Existing raw responses must not be overwritten')
        assert mock.call_count == 4

old = BASE / 'attempt1'
manifest = json.loads((old / 'manifest.json').read_text())
digest = namespace['digest']
assert manifest['plan_sha256'] == digest(old / 'plan.json')
assert manifest['script_sha256'] == digest(old / 'pilot.py')
assert len(manifest['searches']) == 4
for entry in manifest['searches']:
    assert entry['http_status'] == 200
    assert entry['hitCount'] == entry['retrieved_records'] == 0
    assert entry['raw_sha256'] == digest(old / entry['raw_ref'])
amended = json.loads((BASE / 'amendment.json').read_text())['prepared_at_utc']
assert max(e['finished_at_utc'] for e in manifest['searches']) < amended
assert amended < json.loads((BASE / 'manifest.json').read_text())['prepared_at_utc']
report = (BASE / 'report.md').read_text()
for link in re.findall(r'\]\(([^)]+)\)', report):
    if not link.startswith(('http://', 'https://')):
        assert (BASE / link).exists(), link
for evidence in json.loads((BASE / 'evidence.json').read_text()).values():
    if evidence.get('selected') == 'yes':
        assert all(evidence[key] in report for key in ('quote_1', 'quote_2'))
print('PASS: Syntax; Limit-/Leertreffer-/Netzfehler-/HTTP-Fehlerpfade; kein Retry;'
      ' Überschreibschutz; archivierter Erstversuch; Änderung vor Abruf; Reportlinks und Zitate')
