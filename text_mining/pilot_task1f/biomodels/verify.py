"""Offline-Belegprüfung; sendet keine Requests und schreibt keine Dateien."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from inspect_sbml import ROOT, inspect

HERE = Path(__file__).resolve().parent
saved = json.loads((HERE / 'local_inventory.json').read_text())
current = [inspect(ROOT / model['path']) for model in saved]
assert current == saved, 'Lokale XML-Dateien oder Extraktion verändert'
assert [(len(m['species']), len(m['reactions']), len(m['rules_xml']), len(m['events_xml']))
        for m in current] == [(7, 17, 3, 0), (10, 21, 4, 2)]
clock, checkpoint = current
assert {s['id'] for s in clock['species']} == {f'y{i}' for i in range(1, 8)}
assert {s['id'] for s in checkpoint['species']} == {
    'DNA_damage', 'IR', 'p53_total', 'p53_ub', 'p53_ub_ub',
    'Mdm2_cyt', 'Mdm2_p_cyt', 'Mdm2_p_nuc', 'p53', 'MDM2_total'}
for model, absent in [(clock, ('p53', 'mdm2')), (checkpoint, ('per2', 'cry', 'bmal'))]:
    text = (ROOT / model['path']).read_text().lower()
    assert all(word not in text for word in absent)
reactions = {r['id']: r for r in checkpoint['reactions']}
assert {x['species'] for x in reactions['p53_ubiquitination_1']['modifiers']} == {'Mdm2_p_nuc', 'p53'}
assert [x['species'] for x in reactions['p53_ubiquitination_1']['products']] == ['p53_ub']
assert 'p53_total' in reactions['Mdm2_cyt_production']['math_identifiers']
assert 'DNA_damage' in checkpoint['rules_xml'][0]
assert any('y3' in rule and 'y7' in rule and 'trans_per2_cry' in rule for rule in clock['rules_xml'])
for m in current:
    tree = ET.parse(ROOT / m['path'])
    initial = tree.findall('.//{*}initialAssignment')
    assert len(initial) == (1 if m is checkpoint else 0)
    if initial:
        assert initial[0].get('symbol') == 'ModelValue_6'
        assert initial[0].find('.//{*}ci').text.strip() == 'vratio'
    assert not tree.findall('.//{*}rateRule')
    assert not tree.findall('.//{*}algebraicRule')
rows = [json.loads(line) for line in (HERE / 'requests.jsonl').read_text().splitlines()]
assert len(rows) == 10
assert [r['number'] for r in rows] == list(range(1, 11))
assert [r['curl']['http_code'] for r in rows] == [301] * 6 + [200] * 4
for row in rows:
    n = row['number']
    body = (HERE / f'request_{n:02}.body').read_bytes()
    assert hashlib.sha256(body).hexdigest() == row['body_sha256']
    assert row['exit_code'] == 0 and row['curl']['num_redirects'] == 0
    assert '-q' in row['command'] and '--location' not in row['command'] and '-L' not in row['command']
    assert row['utc_start'].endswith('+00:00') and row['utc_end'].endswith('+00:00')
for n in (7, 8):
    assert '<title>Unsupported Media Type | BioModels</title>' in (HERE / f'request_{n:02}.body').read_text()
for model, n, model_id, submission_id, pmid in [
    (clock, 9, 'BIOMD0000000170', 'MODEL8378813456', '15347590'),
    (checkpoint, 10, 'BIOMD0000001006', 'MODEL2104140001', '15725723')]:
    api = json.loads((HERE / f'request_{n:02}.body').read_text())
    assert (api['publicationId'], api['submissionId'], api['publication']['accession']) == (model_id, submission_id, pmid)
    assert api['curationStatus'] == 'CURATED'
    assert any(model_id in uri for uri in model['model_resources'])
    assert any(submission_id in uri for uri in model['model_resources'])
    assert any('/pubmed/' + pmid in uri for uri in model['model_resources'])
    assert (api['files']['main'][0]['sha256sum'] == model['sha256']) == (n == 10)
print('PASS: 2 XML unverändert; 7/17/3/0 und 10/21/4/2 Species/Reaktionen/Regeln/Events; Referenzen konsistent.')
print('PASS: 10 Requests, Raw-Hashes und UTC; 2 API-IDs/Publikationen bestätigt; Ciliberto-Hash gleich, Uhr-Hash abweichend.')
print('Keine Simulation, kein SBML-Schema-Validator, keine Remote-Requests bei diesem Test.')
