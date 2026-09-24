"""Offline checks for the frozen pilot artifacts."""
import csv
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
manifest = json.loads((root / 'manifest.json').read_text())
assert len(manifest) <= 39
for m in manifest:
    body = (root / m['raw_ref']).read_bytes()
    assert hashlib.sha256(body).hexdigest() == m['sha256']
    assert m['searched_at'].endswith('+00:00')
    if m['http_status'] == 200:
        data = json.loads(body)
        items = data.get('resultList', {}).get('result', []) if m['source'] == 'Europe PMC' else data.get('results', [data])
        assert len(items) == m['retrieved_records']
records = list(csv.DictReader((root / 'records.csv').open()))
by_id = {r['record_id']: r for r in records}
assert len(by_id) == len(records)
for r in records:
    if r['duplicate_of']:
        first = by_id[r['duplicate_of']]
        assert not first['duplicate_of'] and first['paper_id'] == r['paper_id']
    assert r['fulltext_eligibility'] == 'not_processed'
selected = json.loads((root / 'extraction.json').read_text())
assert 4 <= len(selected) <= 8
for e in selected:
    matches = [r for r in records if r['pmid'] == e['pmid']]
    assert matches
    for r in matches:
        data = json.loads((root / r['raw_ref']).read_text())
        item = next(x for x in data['resultList']['result'] if x.get('pmid') == e['pmid'])
        assert item['doi'].lower() == e['doi'].lower()
        assert e['quote'] in item['abstractText'], e['pmid']
        assert r['quote'] == e['quote'] and r['evidence_level'] == 'Abstract'
    work = json.loads((root / 'raw' / ('edge_' + e['pmid'] + '.json')).read_text())
    assert work['doi'].lower() == 'https://doi.org/' + e['doi'].lower()
    assert work['ids']['pmid'].rsplit('/', 1)[-1] == e['pmid']
print(f'PASS: {len(manifest)} requests; {len(records)} records; {len(set(r["paper_id"] for r in records))} unique reports; {len(selected)} selected abstracts; hashes, IDs, quotes and deduplication valid.')
print('QC OPEN: OpenAlex lists Gauger2005 -> Gery2006; temporal conflict, not a verified historical citation.')
