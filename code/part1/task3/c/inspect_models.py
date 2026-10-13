#!/usr/bin/env python3
"""Targeted BioModels evidence extraction. Default: offline; --fetch permits GETs."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
CACHE = ROOT / 'cache'
BASE = 'https://www.biomodels.org'
SELECTED = (170, 1006, 73, 216, 839)
QUERIES = ('PER2', '(circadian OR CLOCK OR BMAL1 OR PER2) AND (p53 OR TP53 OR MDM2)', '"PER2" AND "p53"')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def get(key, url, fetch):
    path = CACHE / key
    receipt = CACHE / (key + '.receipt.json')
    if not path.exists():
        if not fetch:
            raise RuntimeError('Offline cache missing: ' + str(path))
        started = datetime.now(timezone.utc).isoformat()
        request = urllib.request.Request(url, headers={'User-Agent': 'Task3c-evidence/1.0'})
        try:
            response = urllib.request.urlopen(request, timeout=60)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            raw = response.read()
            path.write_bytes(raw)
            save(receipt, dict(url=url, final_url=response.url, method='GET', status=response.code,
                              started_utc=started, ended_utc=datetime.now(timezone.utc).isoformat(),
                              sha256=digest(raw)))
    raw = path.read_bytes()
    info = json.loads(receipt.read_text())
    assert info['sha256'] == digest(raw) and info['url'] == url
    if info['status'] != 200:
        raise RuntimeError(f"Archived HTTP {info['status']}: {url}")
    return raw


def table(name, rows, fields):
    with (ROOT / name).open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)


def resources(element):
    if element is None:
        return []
    return sorted({v for e in element.iter() for k, v in e.attrib.items() if k.endswith('}resource')})


def extract(raw, mid):
    root = ET.fromstring(raw)
    ns = {'s': root.tag.split('}')[0][1:], 'm': 'http://www.w3.org/1998/Math/MathML'}
    model = root.find('s:model', ns)
    species = []
    for s in model.findall('s:listOfSpecies/s:species', ns):
        species.append(dict(model=mid, id=s.get('id'), name=s.get('name', ''),
                            compartment=s.get('compartment'), annotation='; '.join(resources(s))))
    ids = {s['id'] for s in species}
    reactions = []
    for r in model.findall('s:listOfReactions/s:reaction', ns):
        row = dict(model=mid, id=r.get('id'), name=r.get('name', ''), reversible=r.get('reversible', 'true'))
        for role, tag in [('reactants', 'Reactants'), ('products', 'Products'), ('modifiers', 'Modifiers')]:
            refs = r.find('s:listOf' + tag, ns)
            row[role] = '; '.join(e.get('species') + ((' * ' + e.get('stoichiometry', '1')) if role != 'modifiers' else '') for e in refs) if refs is not None else ''
            assert refs is None or all(e.get('species') in ids for e in refs)
        kinetic = r.find('s:kineticLaw', ns)
        symbols = sorted({e.text.strip() for e in kinetic.findall('.//m:ci', ns)}) if kinetic is not None else []
        row['kinetic_symbols'] = '; '.join(symbols)
        row['kinetic_species'] = '; '.join(sorted(set(symbols) & ids))
        row['mathml'] = ET.tostring(kinetic, encoding='unicode').replace('\n', ' ') if kinetic is not None else ''
        reactions.append(row)
    rules = model.find('s:listOfRules', ns)
    info = dict(model=mid, name=model.get('name', ''), species=len(species), reactions=len(reactions),
                rules=len(rules) if rules is not None else 0,
                annotations=resources(model.find('s:annotation', ns)),
                rule_mathml=ET.tostring(rules, encoding='unicode') if rules is not None else '',
                assignment_variables=[r.get('variable') for r in rules] if rules is not None else [])
    return species, reactions, info


def run(fetch):
    CACHE.mkdir(exist_ok=True)
    candidates, inputs = [], []
    # ponytail: literal metadata screening, not an ontology-complete protein search.
    for path in sorted((PROJECT / 'part1/task3/b/cache').glob('BIOMD*.json')):
        if '.receipt.' in path.name:
            continue
        raw = path.read_bytes()
        d = json.loads(raw)
        text = ' '.join([d.get('name', ''), d.get('description', ''), json.dumps(d.get('publication', {}))])
        hits = [term for term in ('per2', 'per1', 'cry', 'bmal', 'clock', 'circadian', 'p53', 'tp53', 'mdm2') if term in text.lower()]
        inputs.append(dict(path=str(path.relative_to(PROJECT)), sha256=digest(raw)))
        if hits:
            candidates.append(dict(model=path.stem, name=d.get('name'), terms='; '.join(hits),
                                   clock_and_p53=bool(set(hits) & {'per2', 'bmal', 'clock', 'circadian'}) and bool(set(hits) & {'p53', 'tp53', 'mdm2'})))
    table('metadata_candidates.tsv', candidates, ['model', 'name', 'terms', 'clock_and_p53'])
    searches = []
    for i, query in enumerate(QUERIES):
        url = BASE + '/search?' + urllib.parse.urlencode(dict(query=query, domain='biomodels', offset=0, numResults=100, format='json'))
        d = json.loads(get(f'search_{i}.json', url, fetch))
        searches.append(dict(query=query, matches=d.get('matches'), returned=len(d.get('models', [])), models=d.get('models', [])))
    save(ROOT / 'search_results.json', searches)
    all_species, all_reactions, models = [], [], []
    for n in SELECTED:
        mid = f'BIOMD{n:010d}'
        metadata = PROJECT / 'part1/task3/b/cache' / (mid + '.json')
        d = json.loads(metadata.read_text())
        filename = d['files']['main'][0]['name']
        path = PROJECT / 'part1/task1/sbml' / filename
        if path.exists():
            raw = path.read_bytes()
        else:
            url = BASE + '/model/download/' + mid + '?' + urllib.parse.urlencode({'filename': filename})
            raw = get(mid + '.xml', url, fetch)
            path = CACHE / (mid + '.xml')
        inputs.append(dict(path=str(path.relative_to(PROJECT)), sha256=digest(raw)))
        sp, rx, info = extract(raw, mid)
        info.update(source=str(path.relative_to(PROJECT)), sha256=digest(raw),
                    metadata_hash_matches=digest(raw) == d['files']['main'][0].get('sha256sum'),
                    metadata_hash_matches_without_trailing_newline=digest(raw.rstrip(b'\r\n')) == d['files']['main'][0].get('sha256sum'),
                    publication=d.get('publication', {}), api_annotations=d.get('modelLevelAnnotations', []))
        all_species.extend(sp)
        all_reactions.extend(rx)
        models.append(info)
    table('species.tsv', all_species, ['model', 'id', 'name', 'compartment', 'annotation'])
    table('reactions.tsv', all_reactions, ['model', 'id', 'name', 'reversible', 'reactants', 'products', 'modifiers', 'kinetic_symbols', 'kinetic_species', 'mathml'])
    save(ROOT / 'models.json', models)
    save(ROOT / 'inputs.json', inputs)
    assert len(models) == 5 and all(m['species'] and m['reactions'] for m in models)
    assert next(m for m in models if m['model'].endswith('0170'))['species'] == 7
    assert any('p53' in s['name'].lower() for s in all_species if s['model'].endswith('1006'))
    print(f"PASS: {len(inputs)} input hashes; {len(candidates)} metadata candidates; {len(searches)} cached searches; {len(models)} SBML models; {len(all_species)} species; {len(all_reactions)} reactions; references valid. No simulation.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true')
    run(parser.parse_args().fetch)
