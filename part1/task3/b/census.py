#!/usr/bin/env python3
"""BioModels model-level pathway census; Python standard library only."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
from html import escape
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
BASE = 'https://www.biomodels.org'
QUERY = '*:* AND curationstatus:"Manually curated"'
NAMESPACES = ('kegg.pathway', 'reactome', 'pw', 'panther.pathway')


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


class Cache:
    def __init__(self, offline):
        self.offline = offline
        self.directory = ROOT / 'cache'
        self.directory.mkdir(exist_ok=True)

    def get(self, key, url, xml=False):
        path = self.directory / (key + ('.xml' if xml else '.json'))
        receipt = self.directory / (key + '.receipt.json')
        if path.exists() and receipt.exists():
            raw = path.read_bytes()
            info = json.loads(receipt.read_text())
            assert info['url'] == url and info['sha256'] == digest(raw), key
            return raw if xml else json.loads(raw)
        if self.offline:
            raise RuntimeError('Missing cached response: ' + key)
        errors = []
        for attempt in range(4):
            started = utc()
            try:
                req = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': 'BioModels-course-census/1.0'})
                with urllib.request.urlopen(req, timeout=60) as response:
                    raw = response.read()
                    data = ET.fromstring(raw) if xml else json.loads(raw)
                    info = dict(url=url, final_url=response.url, started_utc=started,
                                ended_utc=utc(), sha256=digest(raw), status=response.status,
                                prior_errors=errors)
                if not xml and not isinstance(data, dict):
                    raise ValueError('Expected JSON object')
                path.write_bytes(raw)
                save(receipt, info)
                time.sleep(0.15)
                return raw if xml else data
            except (OSError, ValueError, ET.ParseError) as exc:
                errors.append(dict(time=utc(), error=str(exc)))
                print(f'RETRY {key} {attempt + 1}/4: {exc}', flush=True)
                if isinstance(exc, urllib.error.HTTPError) and exc.code not in (408, 429, 500, 502, 503, 504):
                    break
                time.sleep(2 ** attempt)
        save(self.directory / (key + '.error.json'), dict(url=url, errors=errors))
        raise RuntimeError(f'Failed {key}: {errors[-1]}')


def enumerate_models(cache, phase):
    models = []
    total = None
    offset = 0
    while total is None or offset < total:
        url = BASE + '/search?' + urllib.parse.urlencode(dict(query=QUERY, domain='biomodels', offset=offset, numResults=100, sort='id-asc', format='json'))
        data = cache.get(f'{phase}_{offset:04d}', url)
        if total is None:
            total = data['matches']
        assert data['matches'] == total, 'Search total changed during enumeration'
        page = data['models']
        assert len(page) == min(100, total - offset), 'Incomplete page'
        models.extend(page)
        offset += len(page)
        print(f'{phase}: {offset}/{total}', flush=True)
    ids = [m['id'] for m in models]
    assert len(set(ids)) == total and ids == sorted(ids), 'Duplicate or unsorted model IDs'
    assert all(re.fullmatch(r'(BIOMD|MODEL)\d{10}', x) for x in ids)
    return models


def normalize(annotation):
    uri = urllib.parse.unquote_plus(annotation.get('uri', ''))
    if uri.startswith('urn:miriam:'):
        bits = uri[len('urn:miriam:'):].split(':', 1)
    else:
        parsed = urllib.parse.urlparse(uri)
        if parsed.hostname not in ('identifiers.org', 'www.identifiers.org'):
            return None
        path = parsed.path.strip('/')
        bits = path.split('/', 1) if '/' in path else path.split(':', 1)
    if len(bits) != 2:
        return None
    ns, identifier = bits
    identifier = identifier.strip()
    ns = ns.lower()
    if ns not in NAMESPACES:
        return None
    if ns == 'kegg.pathway':
        identifier = identifier.removeprefix('path:')
        valid = re.fullmatch(r'[a-z]{2,5}\d{5}', identifier)
    elif ns == 'reactome':
        valid = re.fullmatch(r'(REACT_\d+(?:\.\d+)?|R-[A-Z]{3}-\d+(?:\.\d+)?|\d+)', identifier)
    elif ns == 'panther.pathway':
        valid = re.fullmatch(r'P\d{5}', identifier)
    else:
        identifier = identifier.replace('PW_', 'PW:')
        valid = re.fullmatch(r'PW:\d{7}', identifier)
    if not valid:
        raise ValueError('Unexpected pathway identifier: ' + uri)
    return ns, identifier


RDF = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'


def model_annotations(raw):
    root = ET.fromstring(raw)
    ns = root.tag.split('}')[0] + '}'
    model = root.find(ns + 'model')
    assert model is not None
    annotation = model.find(ns + 'annotation')
    if annotation is None:
        return set()
    result = set()
    for description in annotation.findall(f'{{{RDF}}}RDF/{{{RDF}}}Description'):
        if description.get(f'{{{RDF}}}about') != '#' + model.get('metaid', ''):
            continue
        for qualifier in description:
            if not qualifier.tag.startswith(('{http://biomodels.net/biology-qualifiers/}', '{http://biomodels.net/model-qualifiers/}')):
                continue
            namespace, local = qualifier.tag[1:].split('}')
            prefix = 'bqbiol' if 'biology-' in namespace else 'bqmodel'
            for item in qualifier.iter(f'{{{RDF}}}li'):
                uri = item.get(f'{{{RDF}}}resource')
                if uri:
                    result.add((prefix + ':' + local, uri))
    return result


def extract(data, model_id):
    assert data.get('publicationId') == model_id or data.get('submissionId') == model_id, 'Metadata ID mismatch'
    annotations = data.get('modelLevelAnnotations')
    if not isinstance(annotations, list):
        return None
    pairs = defaultdict(list)
    for annotation in annotations:
        key = normalize(annotation)
        if key:
            pairs[key].append(annotation)
    return pairs


def csv_write(name, rows, columns):
    with (ROOT / name).open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def chart(path, title, entries):
    maximum = max((count for _, count in entries), default=1)
    h = 65 + 28 * len(entries)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{h}" viewBox="0 0 900 {h}" role="img"><title>{escape(title)}</title><rect width="100%" height="100%" fill="white"/><g font-family="sans-serif" font-size="13" fill="#222"><text x="15" y="25">{escape(title)}</text>']
    for i, (label, count) in enumerate(entries):
        y = 50 + i * 28
        parts.append(f'<text x="15" y="{y+14}">{escape(label)}</text><rect x="330" y="{y}" width="{480*count/maximum:.1f}" height="19" fill="#346c91"/><text x="{340+480*count/maximum:.1f}" y="{y+14}">{count}</text>')
    parts.append('</g></svg>')
    (ROOT / path).write_text(''.join(parts))


def run(offline):
    cache = Cache(offline)
    manifest_path = ROOT / 'snapshot.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else dict(started_utc=utc(), query=QUERY, scope='All taxa and topics; individual manually curated entries', annotation_source='API modelLevelAnnotations')
    save(manifest_path, manifest)
    cache.get('api_schema', BASE + '/docs/biomodels-jummp-swagger.json')
    models = enumerate_models(cache, 'start')
    inventory, pairs = [], []
    resources = Counter()
    for index, model in enumerate(models, 1):
        mid = model['id']
        row = dict(model_id=mid, name=model['name'], format=model['format'], status='', annotation_source='API modelLevelAnnotations', annotation_count='', pathway_count='', error='')
        try:
            data = cache.get(mid, BASE + '/' + mid + '?format=json')
            found = extract(data, mid)
            if found is None and model['format'] == 'SBML':
                main = data['files']['main']
                assert len(main) == 1, 'Ambiguous principal SBML file'
                url = BASE + '/model/download/' + mid + '?' + urllib.parse.urlencode({'filename': main[0]['name']})
                raw = cache.get(mid + '_sbml', url, xml=True)
                assert digest(raw) == main[0]['sha256sum'], 'Principal SBML hash mismatch'
                data['modelLevelAnnotations'] = [dict(qualifier=q, uri=u) for q, u in sorted(model_annotations(raw))]
                row['annotation_source'] = 'principal SBML model.annotation: ' + main[0]['name']
                found = extract(data, mid)
            if found is None:
                row['status'] = 'annotations_unavailable'
            else:
                annotations = data['modelLevelAnnotations']
                resources.update(a.get('resource', '') for a in annotations)
                row.update(status='pathway_annotations' if found else ('no_pathway_annotations' if annotations else 'empty_annotations'), annotation_count=len(annotations), pathway_count=len(found))
                for (namespace, identifier), annotations in sorted(found.items()):
                    def values(key):
                        return json.dumps(sorted({a.get(key, '') for a in annotations}), ensure_ascii=False)
                    pairs.append(dict(model_id=mid, namespace=namespace, pathway_id=identifier, names=values('name'), qualifiers=values('qualifier'), resources=values('resource'), source_uris=values('uri')))
        except (RuntimeError, ValueError, AssertionError) as exc:
            row.update(status='error', error=str(exc))
            print(f'ERROR {mid}: {exc}', flush=True)
        inventory.append(row)
        if index % 25 == 0 or index == len(models):
            print(f'metadata: {index}/{len(models)}; pairs={len(pairs)}; errors={sum(r["status"] == "error" for r in inventory)}', flush=True)
    end = enumerate_models(cache, 'end_after_fallback')
    ids = [m['id'] for m in models]
    stable = ids == [m['id'] for m in end]
    csv_write('inventory.csv', inventory, ['model_id', 'name', 'format', 'status', 'annotation_source', 'annotation_count', 'pathway_count', 'error'])
    csv_write('model_pathway_pairs.csv', pairs, ['model_id', 'namespace', 'pathway_id', 'names', 'qualifiers', 'resources', 'source_uris'])
    assert len({(p['model_id'], p['namespace'], p['pathway_id']) for p in pairs}) == len(pairs)
    assert {p['model_id'] for p in pairs} <= set(ids)
    pathway_ranking, model_ranking = [], []
    for namespace in NAMESPACES:
        selected = [p for p in pairs if p['namespace'] == namespace]
        counts = Counter(p['pathway_id'] for p in selected)
        names = defaultdict(set)
        for p in selected:
            names[p['pathway_id']].update(json.loads(p['names']))
        for pid, count in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
            pathway_ranking.append(dict(namespace=namespace, rank=1+sum(v > count for v in counts.values()), pathway_id=pid, model_count=count, names=json.dumps(sorted(names[pid]), ensure_ascii=False)))
        counts = Counter(p['model_id'] for p in selected)
        for row in inventory:
            if row['status'] not in ('error', 'annotations_unavailable'):
                counts.setdefault(row['model_id'], 0)
        for mid, count in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
            model_ranking.append(dict(namespace=namespace, rank=1+sum(v > count for v in counts.values()), model_id=mid, pathway_count=count))
        pr = [p for p in pathway_ranking if p['namespace'] == namespace and p['rank'] <= 10]
        mr = [p for p in model_ranking if p['namespace'] == namespace and p['rank'] <= 10 and p['pathway_count'] > 0]
        chart(f'{namespace}_pathways.svg', f'{namespace}: Modelle je Pathway-ID (Top 10 inkl. Gleichstand)', [(p['pathway_id'], p['model_count']) for p in pr])
        chart(f'{namespace}_models.svg', f'{namespace}: Pathway-IDs je Modell (Top 10 inkl. Gleichstand)', [(p['model_id'], p['pathway_count']) for p in mr])
    csv_write('pathway_ranking.csv', pathway_ranking, ['namespace', 'rank', 'pathway_id', 'model_count', 'names'])
    csv_write('model_ranking.csv', model_ranking, ['namespace', 'rank', 'model_id', 'pathway_count'])
    ended = max(json.loads(p.read_text())['ended_utc'] for p in cache.directory.glob('end_after_fallback_*.receipt.json'))
    manifest.update(ended_utc=ended, annotation_source='API modelLevelAnnotations; principal SBML model.annotation if absent', enumeration_stable=stable, model_count=len(models), id_sha256=digest(('\n'.join(ids)+'\n').encode()), formats=dict(Counter(m['format'] for m in models)), statuses=dict(Counter(r['status'] for r in inventory)), pair_counts=dict(Counter(p['namespace'] for p in pairs)), annotation_resources=dict(resources), offline_replay_supported=True)
    save(manifest_path, manifest)
    print(json.dumps(manifest, indent=2), flush=True)
    if not stable or any(r['status'] in ('error', 'annotations_unavailable') for r in inventory):
        raise SystemExit('Incomplete or unstable snapshot; inspect inventory before interpreting results')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true', help='Verify cached hashes and regenerate all outputs without network')
    run(parser.parse_args().offline)
