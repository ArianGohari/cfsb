#!/usr/bin/env python3
"""Begrenzter Europe-PMC-Pilot; nur Python-Standardbibliothek."""
import csv
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]


def utc():
    return datetime.now(timezone.utc).isoformat()


def load(name):
    return json.loads((BASE / name).read_text())


def save(name, value):
    (BASE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def fetch():
    plan = load('plan.json')
    # ponytail: eine Seite pro Query; weitere Seiten erst in einem neuen Suchplan.
    (BASE / 'raw').mkdir(exist_ok=False)
    manifest = {'prepared_at_utc': utc(), 'plan_sha256': digest(BASE / 'plan.json'),
                'script_sha256': digest(Path(__file__)), 'searches': []}
    for query in plan['queries']:
        params = dict(plan['parameters'], query=query['query'])
        manifest['searches'].append(dict(query, source='Europe PMC',
            platform=plan['endpoint'], source_kind='database', method='GET',
            url=plan['endpoint'] + '?' + urlencode(params), parameters=params,
            sort_order=plan['sort_order'], limits=plan['limits'],
            completion_status='planned', http_status=None, hitCount=None,
            retrieved_records=0, raw_ref='raw/' + query['search_id'] + '.json'))
    save('manifest.json', manifest)  # Alle Requests vor dem ersten Netzabruf fixieren.
    for entry in manifest['searches']:
        entry['requested_at_utc'] = utc()
        save('manifest.json', manifest)
        body = None
        try:
            request = Request(entry['url'], headers={'Accept': 'application/json',
                'User-Agent': 'task1d-history-pilot/1.0 (stdlib; academic pilot)'})
            with urlopen(request, timeout=30) as response:
                entry['http_status'] = response.status
                entry['response_headers'] = dict(response.headers)
                body = response.read()
            (BASE / entry['raw_ref']).write_bytes(body)
            data = json.loads(body)
            results = data['resultList']['result']
            entry['hitCount'] = data['hitCount']
            entry['retrieved_records'] = len(results)
            entry['completion_status'] = ('complete_query' if len(results) == data['hitCount']
                                          else 'limited_first_page')
        except (HTTPError, URLError, OSError, ValueError, KeyError) as error:
            entry['completion_status'] = 'error'
            entry['error'] = type(error).__name__ + ': ' + str(error)
            if isinstance(error, HTTPError):
                entry['http_status'] = error.code
                body = error.read()
                entry['raw_ref'] = 'raw/' + entry['search_id'] + '.error-body'
                (BASE / entry['raw_ref']).write_bytes(body)
            elif body is None:
                entry['raw_ref'] = None
        entry['finished_at_utc'] = utc()
        if entry['raw_ref'] and (BASE / entry['raw_ref']).exists():
            entry['raw_sha256'] = digest(BASE / entry['raw_ref'])
        save('manifest.json', manifest)
        print(entry['search_id'], entry['http_status'], entry['completion_status'],
              'hits=', entry['hitCount'], 'retrieved=', entry['retrieved_records'])
    return int(any(e['completion_status'] == 'error' for e in manifest['searches']))


def rows():
    evidence = load('evidence.json') if (BASE / 'evidence.json').exists() else {}
    seen = {}
    for entry in load('manifest.json')['searches']:
        if entry['completion_status'] == 'error':
            continue
        for index, result in enumerate(load(entry['raw_ref'])['resultList']['result'], 1):
            identifier = result['source'] + ':' + result['id']
            record_id = entry['search_id'] + ':' + str(index)
            row = dict(record_id=record_id, search_id=entry['search_id'],
                source_identifier=identifier, paper_id=identifier,
                duplicate_of=seen.get(identifier, ''), raw_ref=entry['raw_ref'],
                doi=result.get('doi', ''), pmid=result.get('pmid', ''),
                title=result.get('title', ''), year=result.get('pubYear', ''),
                first_publication_date=result.get('firstPublicationDate', ''),
                authors='; '.join(a.get('fullName', '') for a in
                                 result.get('authorList', {}).get('author', [])),
                api_publication_types='; '.join(result.get('pubTypeList', {}).get('pubType', [])),
                source_url='https://europepmc.org/article/' + result['source'] + '/' + result['id'],
                selected='no', article_kind='unassessed', source_level='API metadata',
                claim_de='', context_de='', quote_1='', quote_2='',
                selection_note='Nicht manuell bewertet',
                fulltext_status='not_requested', priority_status='not_assessed',
                replication_status='not_assessed')
            row.update(evidence.get(identifier, {}))
            seen.setdefault(identifier, record_id)
            yield row


def export():
    records = list(rows())
    if not records:
        raise SystemExit('Keine Records exportierbar; manifest.json prüfen.')
    with (BASE / 'records.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    print('Export:', len(records), 'Records')


def check():
    manifest, plan = load('manifest.json'), load('plan.json')
    assert manifest['plan_sha256'] == digest(BASE / 'plan.json')
    assert manifest['script_sha256'] == digest(Path(__file__))
    assert len(manifest['searches']) == len(plan['queries']) == 4
    for entry, query in zip(manifest['searches'], plan['queries']):
        assert entry['query'] == query['query']
        assert entry['url'] == plan['endpoint'] + '?' + urlencode(dict(plan['parameters'], query=query['query']))
        assert manifest['prepared_at_utc'] <= entry['requested_at_utc'] <= entry['finished_at_utc']
        if entry.get('raw_sha256'):
            assert digest(BASE / entry['raw_ref']) == entry['raw_sha256']
        if entry['completion_status'] == 'error':
            assert entry['error']
            continue
        data = load(entry['raw_ref'])
        assert entry['http_status'] == 200
        assert entry['hitCount'] == data['hitCount']
        assert entry['retrieved_records'] == len(data['resultList']['result']) <= 10
        assert entry['retrieved_records'] <= entry['hitCount']
    with (BASE / 'records.csv').open(newline='') as stream:
        actual = list(csv.DictReader(stream))
    assert actual == list(rows()), 'CSV weicht von Rohdaten/manueller Evidenz ab'
    assert len(actual) == sum(e['retrieved_records'] for e in manifest['searches'])
    selected = [r for r in actual if r['selected'] == 'yes']
    assert len(selected) == 4, 'Zielarbeiten nicht vollständig identifiziert'
    for row in selected:
        result = next(r for r in load(row['raw_ref'])['resultList']['result'] if r['pmid'] == row['pmid'])
        assert row['quote_1'] and row['quote_2']
        assert all(row[key] in result['abstractText'] for key in ('quote_1', 'quote_2'))
        assert row['source_level'] == 'Originalarbeit: Abstract via Europe PMC API'
        assert 'finkielstein' not in row['authors'].lower()
        assert row['doi'] in (BASE / 'report.md').read_text()
    before = load('workspace_before.json')['sha256']
    after = {str(p.relative_to(ROOT)): digest(p) for p in ROOT.rglob('*')
             if p.is_file() and not p.is_relative_to(BASE)}
    assert before == after, 'Dateien außerhalb history/ verändert'
    print('PASS: 4 Zielarbeiten; Requests, UTC, Hashes, Limits, CSV, Abstractzitate, Report-DOIs;'
          ' alle', len(before), 'vorhandenen Dateien unverändert; keine neuen Dateien außerhalb history/')


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ('fetch', 'export', 'check'):
        raise SystemExit('Usage: python3 pilot.py {fetch|export|check}')
    if sys.argv[1] == 'fetch':
        sys.exit(fetch())
    elif sys.argv[1] == 'export':
        export()
    else:
        check()
