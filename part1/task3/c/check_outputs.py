#!/usr/bin/env python3
"""Offline evidence and deterministic regeneration check; no network calls."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
OUTPUTS = ('metadata_candidates.tsv', 'species.tsv', 'reactions.tsv', 'models.json', 'search_results.json', 'inputs.json')
before = {name: (ROOT / name).read_bytes() for name in OUTPUTS}
for item in json.loads(before['inputs.json']):
    assert hashlib.sha256((PROJECT / item['path']).read_bytes()).hexdigest() == item['sha256'], item['path']
subprocess.run([sys.executable, str(ROOT / 'inspect_models.py')], check=True)
assert all((ROOT / name).read_bytes() == raw for name, raw in before.items()), 'Non-deterministic output'
models = {m['model']: m for m in json.loads(before['models.json'])}
a = models['BIOMD0000000170']
assert not a['metadata_hash_matches'] and a['metadata_hash_matches_without_trailing_newline']
assert all(m['metadata_hash_matches'] for mid, m in models.items() if mid != a['model'])
species = {(s['model'], s['id']): s for s in csv.DictReader((ROOT / 'species.tsv').open(), delimiter='\t')}
reactions = {(r['model'], r['id']): r for r in csv.DictReader((ROOT / 'reactions.tsv').open(), delimiter='\t')}
assert species[('BIOMD0000000170', 'y2')]['name'] == 'PER2_CRY_complex_cytoplasm'
assert 'y1' in reactions[('BIOMD0000000170', 'per2_cry_complex_formation')]['modifiers']
assert 'Mdm2_p_nuc' in reactions[('BIOMD0000001006', 'p53_ubiquitination_1')]['kinetic_species']
assert 'p53' in models['BIOMD0000001006']['assignment_variables']
assert reactions[('BIOMD0000000073', 'reaction_23')]['products'] == 'species_15 * 1'
assert reactions[('BIOMD0000000216', 'r6')]['reactants'] == 'CP * 2'
assert reactions[('BIOMD0000000839', 'v9_3')]['products'] == 'PERCRY * 1'
assert len(species) == 47 and len(reactions) == 123
print('PASS: source hashes, receipts, deterministic offline regeneration, named species/reaction evidence, assignment rules and BIOMD170 newline-only difference.')
