#!/usr/bin/env python3
"""Compare the first ten API model annotation lists with principal SBML RDF."""
import argparse
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from census import ROOT, BASE, Cache, digest, model_annotations, normalize, save, utc


def run(offline):
    report = []
    for n in range(1, 11):
        mid = f'BIOMD{n:010d}'
        data = Cache(offline).get(mid, BASE + '/' + mid + '?format=json')
        filename = data['files']['main'][0]['name']
        url = BASE + '/model/download/' + mid + '?' + urllib.parse.urlencode({'filename': filename})
        path = ROOT / 'probe' / (mid + '.xml')
        receipt = path.with_suffix('.xml.receipt.json')
        if not path.exists():
            assert not offline, 'Missing SBML cache'
            for attempt in range(4):
                try:
                    started = utc()
                    with urllib.request.urlopen(url, timeout=60) as response:
                        raw = response.read()
                    ET.fromstring(raw)
                    path.write_bytes(raw)
                    save(receipt, dict(url=url, started_utc=started, ended_utc=utc(), sha256=digest(raw)))
                    break
                except (OSError, ET.ParseError) as exc:
                    print(f'RETRY {mid}: {exc}', flush=True)
                    if attempt == 3:
                        raise
                    time.sleep(2 ** attempt)
        raw = path.read_bytes()
        assert digest(raw) == json.loads(receipt.read_text())['sha256']
        sbml = model_annotations(raw)
        api = {(a['qualifier'], a['uri']) for a in data['modelLevelAnnotations']}
        row = dict(model_id=mid, sbml_count=len(sbml), api_count=len(api), sbml_only=sorted(sbml-api), api_only=sorted(api-sbml))
        def pathways(items):
            return {(qualifier, normalize({'uri': uri})) for qualifier, uri in items if normalize({'uri': uri})}
        row['pathways_equal'] = pathways(sbml) == pathways(api)
        report.append(row)
        print(mid, row, flush=True)
    save(ROOT / 'api_sbml_validation.json', report)
    assert all(row['pathways_equal'] for row in report), 'API/SBML pathway mismatch'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--offline', action='store_true')
    run(parser.parse_args().offline)
