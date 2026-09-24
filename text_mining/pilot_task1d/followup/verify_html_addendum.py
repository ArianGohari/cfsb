"""Offline verification of the HTML addendum, including historical raw integrity."""
import csv
import hashlib
import json
from pathlib import Path
from html_addendum import normalized_blocks

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'html_raw'
meta = json.loads((RAW / 'gaddameedhi_html.meta.json').read_text())
body = (ROOT / meta['raw_ref']).read_bytes()
assert meta['url'] == 'https://pmc.ncbi.nlm.nih.gov/articles/PMC3466558/'
assert meta['http_status'] == 200
assert len(body) == meta['bytes'] and hashlib.sha256(body).hexdigest() == meta['sha256']
assert meta['started_utc'].endswith('+00:00') and meta['ended_utc'].endswith('+00:00')
new_calls = len(list(RAW.glob('*.meta.json')))
old_calls = len(list((ROOT / 'fulltext_raw').glob('*.meta.json')))
assert new_calls <= 3 and new_calls + old_calls <= 12
old = json.loads((RAW / 'prior_artifacts.json').read_text())
for path, sha in old.items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha, path
blocks = normalized_blocks(body.decode('utf-8'))
text = '\n'.join(blocks)
for token in ['PMC3466558', '22918252', '10.4161/cc.21771', 'Materials and Methods', 'Figure 7.', 'Figure 8.', 'Figure 9.']:
    assert token in text, token
assert normalized_blocks('<p>A <sup>2</sup> B &amp; C</p><script>bad</script>') == ['A 2 B & C']
report = (ROOT / 'html_addendum.md').read_text()
evidence = json.loads((ROOT / 'html_evidence.json').read_text())
for e in evidence:
    assert e['quote'] in blocks[e['block'] - 1], e['id']
    assert e['quote'] in report, e['id']
records = list(csv.DictReader((ROOT / 'records.csv').open()))
selected = [r for r in records if r['pmid'] == '22918252']
assert selected
for row in selected:
    assert row['current_review_ref'] == 'html_addendum.md'
    assert row['current_review_status'].startswith('superseded_abstract_interpretation:')
    assert row['evidence_level'] == 'Abstract', 'Historical record must retain its original evidence level'
for name in ['README.md', 'report.md', 'fulltext_review.md']:
    assert 'html_addendum.md' in (ROOT / name).read_text()[:1600]
print(f'PASS: {new_calls} new request; {old_calls + new_calls}/12 fulltext-phase requests; {len(old)} prior raw artifacts unchanged.')
print(f'PASS: HTML identity/hash/bytes; {len(evidence)} exact block-specific quotes; parser check; {len(selected)} records with superseding review link.')
print('Scientific classification: Fig8/9 targeted non-reproduction; Fig7 context-dependent positive apoptosis finding. No global falsification.')
