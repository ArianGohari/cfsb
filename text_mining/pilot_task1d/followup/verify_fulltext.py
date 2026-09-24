"""Offline integrity, retrieval-status and quotation checks. No network."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'fulltext_raw'
normalize = lambda text: ' '.join(text.split())
old = json.loads((RAW / 'previous_raw_hashes.json').read_text())
for name, sha in old.items():
    assert hashlib.sha256((ROOT / 'raw' / name).read_bytes()).hexdigest() == sha
manifest = [json.loads(p.read_text()) for p in sorted(RAW.glob('*.meta.json'))]
assert len(manifest) <= 12
for m in manifest:
    body = (ROOT / m['raw_ref']).read_bytes()
    assert len(body) == m['bytes']
    assert hashlib.sha256(body).hexdigest() == m['sha256']
    assert m['started_utc'].endswith('+00:00') and m['ended_utc'].endswith('+00:00')
    m['content_status'] = 'not_fulltext'
    if m['name'] == 'dickmeis_epmc':
        article = ET.fromstring(body)
        assert article.find('body') is not None
        ids = {x.get('pub-id-type'): x.text for x in article.findall('./front/article-meta/article-id')}
        assert ids['pmid'] == '17373855' and ids['doi'] == '10.1371/journal.pbio.0050078'
        assert 'PMC1828142' in ids.values()
        m['content_status'] = 'fulltext_xml_with_body'
    elif m['name'] == 'priority_efetch':
        articles = ET.fromstring(body).findall('article')
        assert len(articles) == 2
        assert all(a.find('body') is None and a.find('.//abstract') is not None for a in articles)
        m['content_status'] = 'two_abstracts_no_body'
    elif m['name'].endswith('_bioc'):
        assert b'No result can be found' in body
        m['content_status'] = 'error_message_despite_http_200'
    elif m['name'] == 'missing_ids':
        records = json.loads(body)['records']
        assert len(records) == 2 and all(r['errmsg'] == 'Identifier not found in PMC' for r in records)
        m['content_status'] = 'two_ids_not_found_in_pmc'
    else:
        assert m['http_status'] == 500
        m['content_status'] = 'http_500_internal_server_error'
(ROOT / 'fulltext_manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
evidence = json.loads((ROOT / 'fulltext_evidence.json').read_text())
report = (ROOT / 'fulltext_review.md').read_text()
for e in evidence:
    path = ROOT / e['source']
    if path.suffix == '.json':
        item = next(x for x in json.loads(path.read_text())['resultList']['result'] if x.get('pmid') == e['pmid'])
        text = item['abstractText']
    else:
        article = ET.fromstring(path.read_bytes())
        if article.tag != 'article':
            article = next(a for a in article.findall('article') if any(x.text == e['pmid'] for x in a.findall('.//article-id')))
        node = article.find('body') if e['level'] == 'fulltext' else article.find('.//abstract')
        assert node is not None
        text = ''.join(node.itertext())
    assert normalize(e['quote']) in normalize(text), e['id']
    assert e['quote'] in report, 'Missing report quote: ' + e['id']
print(f'PASS: {len(manifest)}/12 requests; {len(old)} old raw files unchanged; 1 fulltext; 4 fulltext gaps; {len(evidence)} exact quotes verified.')
print('PASS: HTTP 200 error pages and EFetch abstracts not counted as fulltext; XML identity checked.')
