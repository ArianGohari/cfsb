"""Engineering checks, not extra biological test labels or fabricated corpus snippets."""
import copy
import json
from pathlib import Path
import sys
from unittest.mock import patch

sys.dont_write_bytecode = True
import evaluate_bounded as ev


def main():
    checks = []
    ref = ev.load(ev.HERE/'reference.json')
    directed = next(r for s in ref['sentences'] for r in s['relations'] if r['predicate'] == 'INHIBITS')
    binding = next(r for s in ref['sentences'] for r in s['relations'] if r['predicate'] == 'BINDS')
    reverse = dict(directed, subject=directed['object'], object=directed['subject'])
    assert not ev.matches(reverse, directed)
    assert ev.matches(dict(binding,subject=binding['object'],object=binding['subject']),binding)
    assert ev.score_pairs([directed,directed],[directed]) == (1,1,0)
    assert ev.metrics(0,0,15)['precision']['estimate'] is None
    assert ev.metrics(0,0,0)['recall']['wilson95'] is None
    assert 0.20 < ev.proportion(0,15)['wilson95'][1] < 0.21
    checks.append('direction, undirected binding, duplicate predictions, undefined metrics and Wilson limits')
    run = ev.ROOT/'text_mining/data/runs/task4-rules-001'
    real_load = ev.load
    for mode in ('changed_hash','development_leakage'):
        def altered(path):
            value = real_load(path)
            if mode == 'changed_hash' and path == ev.HERE/'freeze.json':
                value['reference_sha256'] = 'bad'
            if mode == 'development_leakage' and path == ev.HERE/'reference.json':
                value['sentences'][0]['paper_id'] = 'PMID:33898942'
            return value
        with patch.object(ev,'load',side_effect=altered):
            try:
                ev.evaluate(run)
            except ValueError as error:
                assert str(error) == ('reference changed after freeze' if mode == 'changed_hash' else 'development leakage')
            else:
                raise AssertionError('tamper/leakage was not rejected')
        checks.append(mode+' rejected without modifying frozen files')
    request = run/'rules/8b3087474f524a81f11aefc4a9e89420f74c123080fa15f6708106df09561f4c/request.json'
    data = ev.load(request)['input_data']
    original = ev.rules.extract_assertions(data)['candidates']
    assert len(original) == 2
    source_id = original[0]['subject_id']
    source_start = original[0]['subject_start']
    for mode in ('missing_mentions','wrong_offsets','ambiguous_identity'):
        changed = copy.deepcopy(data)
        if mode == 'missing_mentions':
            changed['mentions'] = []
        elif mode == 'wrong_offsets':
            for m in changed['mentions']:
                if m['start'] == source_start and m['entity_id'] == source_id:
                    m['start'] += 1
        else:
            other = next(e for e in changed['entities'] if e['kind'] == 'Gene' and e['entity_id'] != source_id)
            m = next(m for m in changed['mentions'] if m['start'] == source_start and m['entity_id'] == source_id)
            changed['mentions'].append(dict(m,entity_id=other['entity_id']))
        assert ev.rules.extract_assertions(changed)['candidates'] == []
        checks.append(mode+' abstains on unchanged development corpus text')
    result = dict(status='pass', checks=checks, development_only=True,
                  biological_reference_unchanged=True,
                  source_request_sha256=ev.sha(request),
                  script_sha256=ev.sha(Path(__file__)),
                  limitation='Development-only annotation perturbations test rejection guards. Held-out negatives have poor annotation coverage, so zero false positives do not establish biological safety.')
    output = ev.HERE/'checks.json'
    with output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print('PASS:',len(checks),'engineering checks; no corpus text fabricated or changed')

if __name__ == '__main__':
    main()
