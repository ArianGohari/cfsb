#!/usr/bin/env python3
import sys
sys.dont_write_bytecode = True
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import socket
import urllib.request
from urllib.parse import unquote, urlparse
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data/runs/task4-rules-001'
OUT = ROOT / 'data/runs/task4-rules-002-offline-fixes'
sys.path.insert(0, str(ROOT))
from litmine import engine, graph, llm, rules, sources


def load(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def tree(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*')) if p.is_file()}


def delta(before, after):
    a = {canonical(v): v for v in before}
    b = {canonical(v): v for v in after}
    return {'added': [b[k] for k in sorted(b.keys() - a.keys())],
            'removed': [a[k] for k in sorted(a.keys() - b.keys())],
            'unchanged': len(a.keys() & b.keys())}


def changes(a, b):
    return {k: {'before': a.get(k), 'after': b.get(k),
                'before_present': k in a, 'after_present': k in b}
            for k in sorted(a.keys() | b.keys()) if a.get(k) != b.get(k) or (k in a) != (k in b)}


def assertions(review):
    relations = {r['relation_id']: r for r in review['relations']}
    docs = {d['document_id']: d for d in review['documents']}
    result = []
    for ev in review['evidence']:
        row = {k: v for k, v in ev.items() if k not in ('evidence_id', 'extractor_id', 'source_ref', 'relation_id')}
        row['relation'] = {k: v for k, v in relations[ev['relation_id']].items() if k != 'relation_id'}
        row['paper_id'] = docs[ev['document_id']]['paper_id']
        result.append(row)
    return result


def request_mentions(folder):
    result = []
    for path in sorted((folder / 'rules').glob('*/request.json')):
        request = load(path)
        if not request['task_id'].startswith('extract:'):
            continue
        docid = request['task_id'][len('extract:'):].rsplit(':', 1)[0]
        for mention in request['input_data']['mentions']:
            result.append(dict(document_id=docid, **{k: mention[k] for k in ('entity_id', 'start', 'end', 'text')}))
    return result


def summary(review):
    return {'tables': {k: len(review[k]) for k in graph.FIELDS},
            'prisma': review['prisma_counts'],
            'decisions': dict(Counter(p['final_decision'] for p in review['papers'])),
            'evidence_statuses': dict(Counter(e['validation_status'] for e in review['evidence'])),
            'qc_reasons': dict(Counter(e['reason'] for e in review['qc']['events'])),
            'annotation_mentions': sum(r['mentions'] for r in review['qc'].get('annotation_coverage', [])),
            'llm_calls': review['qc']['llm_calls'], 'rule_requests': review['qc']['rule_requests'],
            'incomplete': review['qc']['incomplete']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--inspect', action='store_true')
    args = parser.parse_args()
    if OUT.exists():
        raise SystemExit('STOP: exclusive output directory already exists: ' + str(OUT))
    manifest = load(BASE / 'manifest.json')
    config = deepcopy(manifest['config'])
    assert config.get('processing_mode') == 'rules'
    assert config.get('profile') == 'task4_caco2_sarscov2'
    assert Path(config.get('_base_dir', ROOT)).resolve() == ROOT
    config.update(offline=True, replay_dir=str(BASE))
    if args.inspect:
        print(json.dumps({'baseline_config': manifest['config'], 'config_changes': changes(manifest['config'], config),
                          'code_changes': changes(manifest['code_hashes'], {str(p.relative_to(ROOT)): sha(p) for p in (ROOT / 'litmine').glob('*.py')})}, indent=2))
        return

    before = tree(BASE)
    local_paths = set()
    for seed in config.get('seeds', []):
        if seed.get('fulltext_path'):
            local_paths.add((ROOT / seed['fulltext_path']).resolve())
    for filename in config.get('annotations', {}).values():
        local_paths.add((ROOT / filename).resolve())
    for path in (BASE / 'raw').glob('*/*.json'):
        url = load(path).get('url', '')
        if url.startswith('file:'):
            local_paths.add(Path(unquote(urlparse(url).path)))
    inputs_before = {str(p): sha(p) if p.is_file() else None for p in sorted(local_paths)}
    OUT.mkdir(parents=False, exist_ok=False)
    state = {'status': 'started', 'baseline': str(BASE), 'output': str(OUT),
             'config_changes': changes(manifest['config'], config),
             'baseline_config': manifest['config'], 'effective_config': config,
             'config_hashes': {'baseline': hashlib.sha256(canonical(manifest['config']).encode()).hexdigest(),
                               'effective': hashlib.sha256(canonical(config).encode()).hexdigest()},
             'baseline_hashes_before': before, 'local_input_hashes_before': inputs_before,
             'code_hashes': {str(p.relative_to(ROOT)): sha(p) for p in (ROOT / 'litmine').glob('*.py')},
             'script_sha256': sha(Path(__file__)),
             'dependency_hashes': {name: sha(ROOT / name) for name in ('pyproject.toml', 'uv.lock')},
             'offline_guards': {'blocked_calls': [], 'self_tests': [], 'rules_recomputed': True},
             'cache_lookups': [],
             'limits': ['No reference labels or evaluation metrics used.',
                        'Historical mentions reconstructed only from extraction request inputs; coverage totals also reported.',
                        'Assertions compared by text spans and interpretation, excluding execution identifiers.',
                        'No biological validation or causal attribution to individual fixes.']}
    state['code_changes'] = changes(manifest['code_hashes'], state['code_hashes'])
    state['seeds_identical'] = config['seeds'] == manifest['config']['seeds']
    guard = state['offline_guards']
    testing = False

    def deny(name):
        def blocked(*args, **kwargs):
            (guard['self_tests'] if testing else guard['blocked_calls']).append(name)
            raise RuntimeError('offline_guard:' + name)
        return blocked

    def audit(event, args):
        if event.startswith('socket.') and event not in ('socket.__new__',):
            raise RuntimeError('offline_guard:audit:' + event)
        if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
            p = Path(os.fsdecode(args[0])).resolve()
            if p.name == 'reference.json' or ('tests' in p.parts and p.suffix == '.json'):
                raise RuntimeError('forbidden_label_read:' + str(p))
            mode, flags = args[1], args[2]
            writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)))
            if writing and not p.is_relative_to(OUT):
                raise RuntimeError('write_outside_run:' + str(p))
    sys.addaudithook(audit)
    original_cached = sources._cached
    original_annotate = sources.annotate
    annotations = []

    def cached(url, cfg, dest, validator=None):
        answer = original_cached(url, cfg, dest, validator)
        state['cache_lookups'].append({'url': url, 'hit': answer is not None,
                                       'sha256': answer[2]['sha256'] if answer else None})
        return answer

    def annotate(document, paper, cfg, dest):
        answer = original_annotate(document, paper, cfg, dest)
        annotations.append({'document_id': document['document_id'], 'paper_id': paper['paper_id'], **answer})
        return answer

    targets = [(sources, 'urlopen'), (urllib.request, 'urlopen'), (socket, 'create_connection'),
               (socket.socket, 'connect'), (socket.socket, 'connect_ex'), (socket.socket, 'sendto'),
               (socket, 'getaddrinfo'), (llm, 'Client')]
    from contextlib import ExitStack
    try:
        with ExitStack() as stack:
            for obj, name in targets:
                stack.enter_context(patch.object(obj, name, deny(obj.__name__ + '.' + name)))
            testing = True
            for obj, name in targets:
                try:
                    getattr(obj, name)()
                except RuntimeError as exc:
                    assert str(exc).startswith('offline_guard:')
                else:
                    raise AssertionError('guard_failed:' + name)
            testing = False
            stack.enter_context(patch.object(sources, '_cached', cached))
            stack.enter_context(patch.object(sources, 'annotate', annotate))
            review_path = engine.run(config, OUT)
            receipt = graph.export(review_path, OUT / 'graph')
            old, new = load(BASE / 'review.json'), load(review_path)
            state['before'], state['after'] = summary(old), summary(new)
            state['qc'] = {'before': old['qc'], 'after': new['qc']}
            state['screening_changes'] = []
            for key in sorted({(e['paper_id'], e['stage']) for r in (old, new) for e in r['screening']}):
                rows = []
                for review in (old, new):
                    rows.append([{k: v for k, v in e.items() if k not in ('event_id', 'screening_run_id', 'decided_at', 'request_ids')}
                                 for e in review['screening'] if (e['paper_id'], e['stage']) == key])
                if rows[0] != rows[1]:
                    state['screening_changes'].append({'paper_id': key[0], 'stage': key[1], 'before': rows[0], 'after': rows[1]})
            state['paper_decision_changes'] = changes({p['paper_id']: p['final_decision'] for p in old['papers']},
                                                       {p['paper_id']: p['final_decision'] for p in new['papers']})
            state['mention_changes'] = delta(request_mentions(BASE), request_mentions(OUT))
            state['annotation_results'] = annotations
            state['assertion_changes'] = delta(assertions(old), assertions(new))
            state['document_changes'] = changes({d['document_id']: d['text_sha256'] for d in old['documents']},
                                                 {d['document_id']: d['text_sha256'] for d in new['documents']})
            state['baseline_declared_input_hash_mismatches'] = {p: {'declared': h, 'actual': before.get(p)}
                for p, h in manifest['input_hashes'].items() if before.get(p) != h}
            import pyarrow.parquet as pq
            import real_ladybug as lbug
            export_dir = OUT / 'graph'
            reread = load(export_dir / 'graph_export.json')
            assert reread == receipt
            assert all(sha(export_dir / p) == h for p, h in reread['output_hashes'].items())
            tables = {t: pq.read_table(export_dir / (t + '.parquet')).to_pylist() for t in graph.FIELDS}
            assert {t: len(rows) for t, rows in tables.items()} == receipt['tables']
            expected_tables, primary = graph._validated(new)
            assert tables == expected_tables
            db = lbug.Database(export_dir / 'graph.lbug', read_only=True, buffer_pool_size=64 * 1024 * 1024, max_num_threads=2)
            connection = lbug.Connection(db)
            actual = {}
            try:
                for label in receipt['primary_counts']:
                    query = (f'MATCH (n:{label}) RETURN count(n)' if label in {v[0] for v in graph.FIELDS.values()}
                             else f'MATCH ()-[e:{label}]->() RETURN count(e)')
                    result = connection.execute(query)
                    actual[label] = result.get_next()[0]
                    result.close()
            finally:
                connection.close()
                db.close()
            assert actual == receipt['primary_counts']
            svg = ET.parse(export_dir / 'graph.svg').getroot()
            assert svg.tag.endswith('svg')
            dot = (export_dir / 'graph.dot').read_text()
            assert 'digraph' in dot
            state['graph_readback'] = {'receipt': reread, 'database_counts': actual, 'parquet_rows_match_review': True,
                                       'svg_parsed': True, 'dot_read': True, 'artifact_hashes_verified': True}
            calls = load(OUT / 'rules/calls.json')
            assert all(c['cached'] is False and c['origin_mode'] == 'rules' for c in calls)
            assert new['qc']['llm_calls'] == 0 and not guard['blocked_calls']
            state['cache_misses'] = [r for r in state['cache_lookups'] if not r['hit']]
            state['status'] = 'complete'
    except BaseException as exc:
        state['status'] = 'failed'
        state['error'] = type(exc).__name__ + ':' + str(exc)
        raise
    finally:
        after = tree(BASE)
        state['baseline_hashes_after'] = after
        state['baseline_unchanged'] = before == after
        state['local_input_hashes_after'] = {str(p): sha(p) if p.is_file() else None for p in sorted(local_paths)}
        state['local_inputs_unchanged'] = inputs_before == state['local_input_hashes_after']
        state['cache_misses'] = [r for r in state['cache_lookups'] if not r['hit']]
        (OUT / 'comparison.json').write_text(json.dumps(state, indent=2, ensure_ascii=False, sort_keys=True) + '\n')
        assert state['baseline_unchanged'] and state['local_inputs_unchanged']
    print(json.dumps({k: state[k] for k in ('status', 'before', 'after', 'paper_decision_changes', 'baseline_unchanged', 'local_inputs_unchanged')}, indent=2))
    print(json.dumps({'screening_changes': len(state['screening_changes']),
                      'mention_additions': len(state['mention_changes']['added']), 'mention_removals': len(state['mention_changes']['removed']),
                      'assertion_additions': len(state['assertion_changes']['added']), 'assertion_removals': len(state['assertion_changes']['removed']),
                      'cache_misses': len(state['cache_misses'])}, indent=2))


if __name__ == '__main__':
    main()
