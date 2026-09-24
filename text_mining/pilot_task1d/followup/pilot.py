#!/usr/bin/env python3
"""Bounded public API retrieval; cached responses are never overwritten."""
import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
EPMC = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search'
SEEDS = {
    'fu2002': 'AUTH_LAST:Fu AND PUB_YEAR:2002 AND (period2 OR "period 2")',
    'matsuo2003': 'AUTH_LAST:Matsuo AND PUB_YEAR:2003 AND circadian',
    'gery2006': 'AUTH_LAST:Gery AND PUB_YEAR:2006 AND (per1 OR period1)',
}
QUERIES = {
    'per2_tumor': '(PER2 OR "period 2") AND (tumor OR cancer) AND (deficient OR mutation OR suppression)',
    'per1_damage': '(PER1 OR "period 1") AND ("DNA damage" OR irradiation) AND (knockdown OR apoptosis)',
    'wee1_cycle': 'WEE1 AND (circadian OR clock) AND (liver OR proliferation OR regeneration)',
    'clock_resistance': '(clock OR circadian) AND (deficient OR knockout OR loss) AND ("tumor resistance" OR "cancer resistant" OR "tumor development")',
    'cry_p53': '(cryptochrome OR Cry1 OR Cry2) AND (p53 OR Tp53) AND (cancer OR tumor)',
    'period_loss': '(Per1 OR Per2 OR period) AND (deficiency OR deficient OR knockout) AND (carcinogenesis OR "tumor incidence" OR "tumor suppression")',
}


def fetch(name, url):
    meta_path = ROOT / 'raw' / (name + '.meta.json')
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        assert meta['url'] == url, 'Cached URL differs'
        return json.loads((ROOT / meta['raw_ref']).read_bytes()) if meta['http_status'] == 200 else None
    meta_path.parent.mkdir(exist_ok=True)
    assert len(list(meta_path.parent.glob('*.meta.json'))) < 39
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    status, error = None, ''
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'task1d-bounded-public-pilot/1.0'}), timeout=35) as response:
            status, body = response.status, response.read()
    except urllib.error.HTTPError as exc:
        status, body, error = exc.code, exc.read(), str(exc)
    except (urllib.error.URLError, TimeoutError) as exc:
        body, error = b'', str(exc)
    try:
        data = json.loads(body)
    except (ValueError, UnicodeError):
        data = None
    items = (data.get('resultList', {}).get('result', []) if 'europepmc' in url else data.get('results', [data] if data.get('id') else [])) if isinstance(data, dict) else []
    hits = (data.get('hitCount') if 'europepmc' in url else data.get('meta', {}).get('count', 1 if data.get('id') else None)) if isinstance(data, dict) else None
    raw = 'raw/' + name + ('.json' if data is not None else '.body')
    (ROOT / raw).write_bytes(body)
    meta = dict(search_id=name, source='Europe PMC' if 'europepmc' in url else 'OpenAlex', url=url,
                searched_at=started, completed_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                http_status=status, error=error, reported_hits=hits, retrieved_records=len(items),
                pagination='first page only', completion_status='bounded_page' if status == 200 else 'blocked_or_failed',
                raw_ref=raw, sha256=hashlib.sha256(body).hexdigest())
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + '\n')
    print(name, status, 'hits=', hits, 'retrieved=', len(items), flush=True)
    return data if status == 200 else None


def epmc(name, query, size):
    return fetch(name, EPMC + '?' + urllib.parse.urlencode(dict(query=query, format='json', resultType='core', pageSize=size)))


def export():
    manifest = [json.loads(p.read_text()) for p in sorted((ROOT / 'raw').glob('*.meta.json'))]
    for meta in manifest:
        params = urllib.parse.parse_qs(urllib.parse.urlsplit(meta['url']).query)
        meta.update(source_kind='database', full_query=params.get('query', params.get('filter', [meta['url']]))[0],
                    sort_order=params.get('sort', ['service_default_not_explicitly_set'])[0],
                    requested_page_size=params.get('pageSize', params.get('per-page', ['single_work']))[0],
                    deduplication_version='v1: sorted search_id, PMID else lowercase DOI else source:id; first record retained')
    (ROOT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    seen, records = {}, []
    for meta in manifest:
        if meta['source'] != 'Europe PMC' or meta['http_status'] != 200:
            continue
        data = json.loads((ROOT / meta['raw_ref']).read_text())
        for i, item in enumerate(data['resultList']['result'], 1):
            paper = 'PMID:' + item['pmid'] if item.get('pmid') else ('DOI:' + item['doi'].lower() if item.get('doi') else item['source'] + ':' + item['id'])
            rid = meta['search_id'] + ':' + str(i)
            records.append(dict(record_id=rid, search_id=meta['search_id'], source_identifier=item['source'] + ':' + item['id'], paper_id=paper, duplicate_of=seen.get(paper, ''), raw_ref=meta['raw_ref'], title=item['title'], year=item.get('pubYear', ''), doi=item.get('doi', ''), pmid=item.get('pmid', ''), evidence_level='Abstract' if item.get('abstractText') else 'Metadata', decision='not_processed'))
            seen.setdefault(paper, rid)
    extraction_path = ROOT / 'extraction.json'
    selected = {r['pmid']: r for r in json.loads(extraction_path.read_text())} if extraction_path.exists() else {}
    seeds = {name: json.loads((ROOT / 'raw' / ('oa_' + name + '.json')).read_text())['id'] for name in SEEDS if (ROOT / 'raw' / ('oa_' + name + '.json')).exists()}
    for row in records:
        evidence = selected.get(row['pmid'], {})
        row.update({key: evidence.get(key, '') for key in ['claim_de', 'context_de', 'interpretation_de', 'quote']})
        row['public_url'] = 'https://europepmc.org/article/MED/' + row['pmid'] if row['pmid'] else ''
        row['doi_url'] = 'https://doi.org/' + row['doi'] if row['doi'] else ''
        edge_path = ROOT / 'raw' / ('edge_' + row['pmid'] + '.json')
        work = json.loads(edge_path.read_text()) if edge_path.exists() else {}
        row['openalex_seed_edges'] = '; '.join(name + '=' + ('present' if wid in work.get('referenced_works', []) else 'not_in_retrieved_references') for name, wid in seeds.items()) if work.get('id') else 'not_checked'
        row['citation_qc'] = 'temporal_conflict: Gauger2005 -> Gery2006; API edge not historically verified' if row['pmid'] == '16061665' else 'API metadata only; original references not checked'
        row['fulltext_eligibility'] = 'not_processed'
        row['current_review_ref'] = 'html_addendum.md' if row['pmid'] == '22918252' else ''
        row['current_review_status'] = 'superseded_abstract_interpretation: fulltext Fig8/9 direct non-reproduction; Fig7 reduced UV apoptosis after PER1/2 knockdown' if row['pmid'] == '22918252' else 'historical_abstract_pilot'
        if evidence:
            row['decision'] = 'exploratory_abstract_selected'
        elif row['pmid'] in ['12372299', '12934012', '16678109']:
            row['decision'] = 'verified_seed'
    if records:
        with (ROOT / 'records.csv').open('w', newline='') as out:
            writer = csv.DictWriter(out, fieldnames=records[0])
            writer.writeheader()
            writer.writerows(records)
    print('records=', len(records), 'unique_reports=', len(seen))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['seeds', 'openalex', 'search', 'clarify', 'edges', 'export'])
    parser.add_argument('--name')
    parser.add_argument('--query')
    args = parser.parse_args()
    if args.stage == 'seeds':
        for name, query in SEEDS.items():
            epmc(name, query, 5)
    elif args.stage == 'openalex':
        for name, resolved in [('fu2002', 'fu'), ('matsuo2003', 'matsuo'), ('gery2006', 'gery')]:
            data = json.loads((ROOT / 'raw' / ('clarify_' + resolved + '.json')).read_text())
            items = data['resultList']['result']
            assert len(items) == 1, 'Resolve ambiguous seed manually first'
            doi = items[0]['doi']
            work = fetch('oa_' + name, 'https://api.openalex.org/works/https://doi.org/' + doi)
            if work and work.get('id'):
                fetch('cites_' + name, 'https://api.openalex.org/works?' + urllib.parse.urlencode({'filter': 'cites:' + work['id'].rsplit('/', 1)[-1], 'per-page': 25, 'sort': 'publication_date:asc'}))
    elif args.stage == 'search':
        for name, query in QUERIES.items():
            epmc(name, '(' + query + ') AND FIRST_PDATE:[2004-01-01 TO 2026-09-20]', 20)
    elif args.stage == 'edges':
        for row in json.loads((ROOT / 'extraction.json').read_text()):
            fetch('edge_' + row['pmid'], 'https://api.openalex.org/works/https://doi.org/' + row['doi'])
    elif args.stage == 'clarify':
        assert args.name and args.query
        assert args.name.replace('_', '').isalnum()
        epmc('clarify_' + args.name, args.query, 5)
    export()


if __name__ == '__main__':
    main()
