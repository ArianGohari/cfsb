"""Offline-Bereichstest; keine globale Workspace-Baseline, kein Netzverkehr."""
import ast
import hashlib
import json
from pathlib import Path
import re
import runpy
from urllib.parse import parse_qs, urlparse
import xml.etree.ElementTree as ET
from unittest.mock import Mock, patch

BASE = Path(__file__).resolve().parent
HISTORY = BASE.parent


def load(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


ast.parse((BASE / 'retrieve.py').read_text())
requests = [json.loads(line) for line in (BASE / 'requests.jsonl').read_text().splitlines()]
assert len(requests) == 12
assert len({r['id'] for r in requests}) == 12
assert len({r['url'] for r in requests}) == 12
assert [r['ordinal'] for r in requests] == list(range(1, 13))
for request in requests:
    meta = load(BASE / (request['id'] + '.meta.json'))
    assert all(meta[key] == value for key, value in request.items())
    assert request['plan_sha256'] == digest(BASE / 'plan.md')
    assert request['requested_at_utc'] <= meta['finished_at_utc']
    assert request['requested_at_utc'].endswith('+00:00')
    raw = BASE / meta['raw_ref']
    assert meta['sha256'] == digest(raw)
    assert meta['bytes'] == raw.stat().st_size
    assert meta['http_status'] == (403 if request['ordinal'] <= 4 else 200)
    if request['ordinal'] <= 4:
        assert meta['status'] == 'http_error' and not meta['pdf_magic']
    if 'hitCount' in meta:
        data = load(raw)
        params = parse_qs(urlparse(request['url']).query)
        assert data['request']['queryString'] == params['query'][0]
        assert meta['hitCount'] == data['hitCount']
        assert meta['retrieved_records'] == len(data['resultList']['result']) <= int(params['pageSize'][0])
        assert params['cursorMark'] == ['*'] and params['resultType'] == ['core']
        assert meta['hitCount'] == meta['retrieved_records'] == (10 if request['id'] == 'prior_quoted' else 0)
    if request['id'].endswith('_refs'):
        data = load(raw)['message']
        assert data['reference-count'] == len(data['reference'])

xml = ET.fromstring((BASE / 'raw/anderson_fulltext.body').read_bytes())
ids = {node.get('pub-id-type'): node.text for node in xml.findall('.//article-id')}
assert ids['pmid'] == '10695987' and ids['pmcid'] == 'PMC7127503'
assert ids['doi'].lower() == '10.1016/s0304-3835(99)00320-1'
assert xml.find('body') is not None and xml.find('.//ref-list') is not None
blocks = []


def visit(node):
    if node.tag in ('article-title', 'title', 'p', 'ref', 'table-wrap', 'fig'):
        blocks.append('[' + node.tag + ' ' + node.get('id', '') + '] ' + ' '.join(''.join(node.itertext()).split()))
    else:
        for child in node:
            visit(child)


visit(xml)
assert (BASE / 'anderson_fulltext.txt').read_text() == '\n\n'.join(blocks) + '\n'
report = (HISTORY / 'fulltext_review.md').read_text()
evidence = load(BASE / 'evidence.json')
for item in evidence:
    if item.get('element_id'):
        node = xml.find('.//*[@id="' + item['element_id'] + '"]')
        text = ' '.join(''.join(node.itertext()).split())
    else:
        data = load(BASE / item['source'])
        record = next(r for r in data['resultList']['result'] if r['pmid'] == item['pmid'])
        text = record['abstractText']
    assert item['quote'] in text, item['id']
    assert item['quote'] in report, item['id']
for link in re.findall(r'\]\(([^)]+)\)', report):
    if not link.startswith(('http://', 'https://')):
        assert (HISTORY / link).exists(), link

before = load(BASE / 'before.json')['sha256']
assert len(before) == 21
for name, expected in before.items():
    assert digest(HISTORY / name) == expected, name

namespace = runpy.run_path(str(BASE / 'retrieve.py'))
fetch = namespace['fetch']
blocked_network = Mock(side_effect=AssertionError('Offline test must not access network'))
with patch.dict(fetch.__globals__, build_opener=blocked_network):
    try:
        fetch('budget_test', 'https://example.invalid', 'Must stop before network')
    except AssertionError as error:
        assert str(error) == 'Netzbudget ausgeschöpft'
    else:
        raise AssertionError('13th request was not blocked')
    blocked_network.assert_not_called()
assert len((BASE / 'requests.jsonl').read_text().splitlines()) == 12
print('PASS: 12 Requests, 4 protokollierte HTTP-403-Blockaden; Rohdatenhashes, UTC, Suchparameter;'
      ' 10 Referenztreffer; Originalvolltext PMID 10695987; 15 wörtliche Belege;'
      ' Lesefassung und Reportlinks; 21 frühere history-Artefakte unverändert;'
      ' Budgetschutz ohne Netzverkehr. Keine globale Baseline geprüft.')
