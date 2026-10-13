"""Offline scoring of frozen sentence spans; never call the paper-complete evaluator."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
from unittest.mock import patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'text_mining'))
from litmine import rules, llm  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def proportion(k, n):
    if not n:
        return dict(numerator=k, denominator=n, estimate=None, wilson95=None)
    z = 1.959963984540054
    p = k / n
    center = (p + z*z/(2*n)) / (1 + z*z/n)
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / (1 + z*z/n)
    return dict(numerator=k, denominator=n, estimate=p,
                wilson95=[max(0, center-half), min(1, center+half)])


def metrics(tp, fp, fn):
    return dict(tp=tp, fp=fp, fn=fn, precision=proportion(tp, tp+fp),
                recall=proportion(tp, tp+fn),
                f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None)


def inside(a, b):
    return b['start'] <= a['start'] < a['end'] <= b['end']


def matches(pred, ref):
    if pred['predicate'] != ref['predicate']:
        return False
    forward = inside(pred['subject'], ref['subject']) and inside(pred['object'], ref['object'])
    reverse = inside(pred['object'], ref['subject']) and inside(pred['subject'], ref['object'])
    return forward or (ref['predicate'] == 'BINDS' and reverse)


def score_pairs(predictions, references):
    # Small maximum bipartite matching prevents duplicate/nested spans earning extra TPs.
    assigned = {}
    def visit(i, seen):
        for j, ref in enumerate(references):
            if j in seen or not matches(predictions[i], ref):
                continue
            seen.add(j)
            if j not in assigned or visit(assigned[j], seen):
                assigned[j] = i
                return True
        return False
    tp = sum(visit(i, set()) for i in range(len(predictions)))
    return tp, len(predictions)-tp, len(references)-tp


def evaluate(run):
    freeze = load(HERE/'freeze.json')
    require(sha(HERE/'reference.json') == freeze['reference_sha256'], 'reference changed after freeze')
    require(sha(HERE/'freeze_reference.py') == freeze['builder_sha256'], 'reference builder changed')
    for name, digest in {**freeze['corpus_sha256'], **freeze['tool_sha256']}.items():
        require(sha(ROOT/name) == digest, 'frozen source changed: '+name)
    ref = load(HERE/'reference.json')
    review_path = run/'review.json'
    review = load(review_path)
    inputs = {str(review_path.relative_to(ROOT)): sha(review_path)}
    docs = {d['document_id']:d for d in review['documents']}
    relations = {r['relation_id']:r for r in review['relations']}
    fulltexts = {d['paper_id']:d for d in docs.values() if d['kind'] == 'fulltext'}
    test_papers = {s['paper_id'] for s in ref['sentences']}
    training = set(ref['development_excluded'])
    for config in (review['manifest'], review['manifest'].get('config', {})):
        training.update(config.get('training_paper_ids', []))
    require(not training & test_papers, 'development leakage')
    require(len(ref['sentences']) == ref['sentence_denominator'], 'wrong sentence denominator')
    require(len({s['sentence_id'] for s in ref['sentences']}) == len(ref['sentences']), 'duplicate sentence')
    code_comparison = {}
    for name, digest in review['manifest']['code_hashes'].items():
        code_comparison[name] = sha(ROOT/'text_mining'/name) == digest
    require(all(code_comparison.values()), 'current tool differs from scored run')
    mentions = defaultdict(list)
    entities = {}
    extracted = set()
    replayed = 0
    replay_candidates = 0
    # Exercise the actual rules with original annotations, never reference endpoints.
    with patch('socket.socket', side_effect=AssertionError('network forbidden')), \
         patch.object(llm.Client, '__init__', side_effect=AssertionError('LLM forbidden')):
        for path in sorted((run/'rules').glob('*/request.json')):
            request = load(path)
            if not request['task_id'].startswith('extract:'):
                continue
            result_path = path.with_name('result.json')
            stored = load(result_path)
            for p in (path, result_path):
                inputs[str(p.relative_to(ROOT))] = sha(p)
            data = request['input_data']
            require(data['chunk_start'] == 0, 'chunk offsets require explicit adaptation')
            require(request['rule_version'] == rules.VERSION, 'rule version mismatch')
            require(llm.digest(request) == path.parent.name, 'request hash mismatch')
            require(llm.digest(data) == stored['input_hash'], 'input hash mismatch')
            fresh = rules.extract_assertions(data)
            require(fresh == stored['response'], 'rule replay mismatch')
            replayed += 1
            replay_candidates += len(fresh['candidates'])
            did = request['task_id'].removeprefix('extract:').rsplit(':', 1)[0]
            require(docs[did]['text'] == data['text'], 'extract text mismatch')
            extracted.add(docs[did]['paper_id'])
            entities.update({e['entity_id']:e for e in data['entities']})
            for m in data['mentions']:
                require(m['document_id'] == did, 'mention document mismatch')
                require(data['text'][m['start']:m['end']] == m['text'], 'bad source annotation span')
                mentions[docs[did]['paper_id']].append(m)
    selected_predictions = defaultdict(list)
    accepted_all = []
    outside = 0
    for ev in review['evidence']:
        d = docs[ev['document_id']]
        rel = relations[ev['relation_id']]
        require(d['text'][ev['start']:ev['end']] == ev['quote'], 'bad evidence span')
        if ev.get('stance') != 'supports' or ev.get('validation_status') not in ('auto_pass','assertion_pass'):
            continue
        accepted_all.append((d['paper_id'], ev))
        bound = [s for s in ref['sentences'] if s['paper_id'] == d['paper_id'] and inside(ev,s)]
        if not bound:
            # A quote spanning a selected boundary must not silently disappear.
            require(not any(s['paper_id'] == d['paper_id'] and max(s['start'],ev['start']) < min(s['end'],ev['end']) for s in ref['sentences']), 'prediction crosses scoring boundary')
            outside += 1
            continue
        require(len(bound) == 1, 'ambiguous sentence boundary')
        s = bound[0]
        item = dict(predicate=rel['predicate'])
        for role in ('subject','object'):
            item[role] = dict(start=ev[role+'_start'], end=ev[role+'_end'])
            require(inside(item[role], s), 'argument outside selected sentence')
        if item not in selected_predictions[s['sentence_id']]:
            selected_predictions[s['sentence_id']].append(item)
    details = []
    counts = Counter()
    total_tp = total_fp = total_fn = 0
    binary = Counter()
    strata = Counter()
    for s in ref['sentences']:
        d = fulltexts[s['paper_id']]
        text = (ROOT/s['source_path']).read_text(encoding='utf-8')
        require(sha(ROOT/s['source_path']) == s['source_sha256'], 'corpus hash mismatch')
        require(d['text'] == text, 'run/corpus text mismatch')
        require(text[s['start']:s['end']] == s['text'], 'reference sentence span mismatch')
        a = s['paragraph_start']
        require(text[a:a+len(s['paragraph'])] == s['paragraph'], 'paragraph mismatch')
        local = [m for m in mentions[s['paper_id']] if inside(m,s)]
        counts['sentences_with_any_mention'] += bool(local)
        counts['sentences_with_two_mentions_any_type'] += len(local) >= 2
        counts['sentences_reaching_extractor'] += s['paper_id'] in extracted
        strata[s['stratum']] += 1
        predictions = selected_predictions[s['sentence_id']]
        primary = [p for p in predictions if p['predicate'] in ref['target_predicates']]
        counts['selected_predictions_outside_predicate_scope'] += len(predictions)-len(primary)
        tp, fp, fn = score_pairs(primary, s['relations'])
        total_tp += tp; total_fp += fp; total_fn += fn
        positive = bool(s['relations'])
        predicted = bool(primary)
        binary['tp' if positive and predicted else 'fn' if positive else 'fp' if predicted else 'tn'] += 1
        relation_support = []
        for relation in s['relations']:
            endpoints = []
            for role in ('subject','object'):
                endpoint = relation[role]
                require(text[endpoint['start']:endpoint['end']] == endpoint['text'], 'endpoint span mismatch')
                hits = [dict(m, kind=entities[m['entity_id']]['kind']) for m in local if inside(m,endpoint) and entities[m['entity_id']]['kind'] in ('Gene','Protein')]
                endpoints.append(hits)
            supported = all(endpoints)
            gate = ('candidate_supported' if supported else 'entity_missing_in_extracted_document' if s['paper_id'] in extracted else 'not_annotated_screening_gate')
            counts[gate] += 1
            relation_support.append(dict(gate=gate, endpoint_candidates=endpoints))
        details.append(dict(sentence_id=s['sentence_id'], stratum=s['stratum'], reached_extractor=s['paper_id'] in extracted, source_mentions=len(local), relation_support=relation_support, predictions=predictions, tp=tp, fp=fp, fn=fn))
    cov = review['qc']['annotation_coverage']
    positive_papers = {s['paper_id'] for s in ref['sentences'] if s['relations']}
    yielded_papers = {pid for pid,ev in accepted_all}
    result = dict(status='evaluated_against_machine_reference', created_at_utc=datetime.now(timezone.utc).isoformat(), reference_sha256=sha(HERE/'reference.json'), freeze_sha256=sha(HERE/'freeze.json'), evaluator_sha256=sha(Path(__file__)), input_sha256=inputs, annotation_source=ref['annotation_source'], prediction_scope=ref['prediction_scope'], unit='bounded sentence-local molecular relations; normalized identity/context accuracy NOT scored', sentence_denominator=len(ref['sentences']), test_papers=sorted(test_papers), strata=dict(strata),
        relation_metrics=metrics(total_tp,total_fp,total_fn),
        sentence_detection=dict(metrics(binary['tp'],binary['fp'],binary['fn']), tn=binary['tn'], false_positive_rate=proportion(binary['fp'],binary['fp']+binary['tn'])),
        positive_paper_detection=proportion(len(positive_papers & yielded_papers),len(positive_papers)),
        bounded_coverage=dict(counts, sentence_yield=proportion(sum(bool(x) for x in selected_predictions.values()),len(ref['sentences'])), candidate_supported_recall=proportion(0,counts['candidate_supported']) if total_tp == 0 else None),
        corpus_coverage=dict(papers=len(review['papers']), fulltexts=len(fulltexts), annotated_documents=len(cov), source_mentions=sum(c['mentions'] for c in cov), parser_sentences=sum(c['sentences'] for c in cov), parser_sentences_with_two_mentions=sum(c['sentences_with_two_mentions'] for c in cov), accepted_evidence=len(accepted_all), predicted_papers=len(yielded_papers), heldout_paper_yield=proportion(len(yielded_papers-training),len(set(fulltexts)-training)), accepted_evidence_outside_bound=outside),
        replay=dict(extraction_requests=replayed, candidates=replay_candidates, all_match=True, network_blocked=True, llm_construction_blocked=True, run_reported_llm_calls=review['qc']['llm_calls'], code_matches_run=code_comparison),
        limitations=['Purposive clustered sample; Wilson intervals are descriptive binomial model limits, not population confidence guarantees.', 'No complete-paper, screening-accuracy, clinical-validity, normalized-ID or strict-context score.', 'Candidate-supported means both endpoint spans contain molecular source mentions; this does not certify identity or type suitability.', 'Missing upstream candidates remain FNs in end-to-end recall. No reference annotations are injected into replay.', 'Aggregate run results were disclosed in required documentation before freeze; not fully blinded.', 'Binding uses undirected span matching; other predicates preserve direction. This differs from the built-in exact-ID paper evaluator.'],
        details=details)
    for name,digest in {**freeze['corpus_sha256'],**freeze['tool_sha256'],**inputs}.items():
        require(sha(ROOT/name) == digest, 'input changed during evaluation: '+name)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path, default=ROOT/'text_mining/data/runs/task4-rules-001')
    parser.add_argument('--out', type=Path, default=HERE/'results.json')
    parser.add_argument('--check', action='store_true', help='Recompute and compare without writing')
    args = parser.parse_args()
    require(args.out.resolve().is_relative_to(HERE), 'output must remain under evaluation/')
    result = evaluate(args.run.resolve())
    if args.check:
        old = load(args.out)
        for key in ('created_at_utc',):
            result.pop(key); old.pop(key)
        require(result == old, 'results changed')
        print('PASS: frozen inputs, replay and recomputed results match')
    else:
        with args.out.open('x', encoding='utf-8') as stream:
            json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False)
            stream.write('\n')
        print(json.dumps({k:result[k] for k in ('relation_metrics','sentence_detection','bounded_coverage','replay')},indent=2))

if __name__ == '__main__':
    main()
