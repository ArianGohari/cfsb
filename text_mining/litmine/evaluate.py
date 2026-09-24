"""Offline, paper-level evaluation of engine review.json; invoked by the parent CLI.

Gold v1 JSON: {"version": 1, "reports": [{"paper_id": "PMID:1",
"split": "test", "screening": "include", "fulltext_eligibility": "include",
"extraction_complete": true, "relations": [{"subject_id": "A",
"predicate": "UPREGULATES", "object_id": "B", "species_id": null,
"cell_line_id": null, "condition": null, "compartment": null,
"attribution": "own_experiment"}]}], "synthetic_demo": false}.

split is train/test; screening and optional fulltext_eligibility are include/exclude.
Context fields are required, with null meaning annotated absence. Attribution is
optional: omit it on ANY relation to exclude that whole paper from the separate
strict context+attribution metric (never treat missing annotation as unknown).
Use attribution='unknown' for an explicitly annotated unknown attribution.
extraction_complete must be true, including for empty relations (true negatives).
Annotations cover the entire report, including abstract and fulltext. paper_id
must be canonical and unique across all splits. Only test papers are scored.
Manifest training_paper_ids (also in config) must be disjoint from test papers.

Metrics are micro set counts keyed by paper: repeated chunks/documents count once.
Triples preserve exact IDs, direction and predicate, including BINDS; no alias or
symmetry normalization. Strict matches also require all context and attribution.
By default only auto_pass, supports evidence is a prediction. Gold may explicitly
set prediction_scope=reported_assertions to also score assertion_pass, or
own_experiment to restrict attribution. annotation_source records who supplied
labels; machine-agent labels are not human gold. Uncertain evidence is reported
as abstention and cannot earn true positives. Missing decisions abstain; include
gold then counts as FN. Undefined ratios are null. Missing test papers are errors.
Baseline extraction is conditioned on pipeline-selected texts and available
annotations, not a standalone rule pipeline on all reports. Candidates are scored
as emitted against all test reports, so recall includes losses from those gates.
The screening baseline is independent of pipeline decisions. Baseline extraction
context, attribution and experimental_method are unsupported, not scored as null.
Scientific quality is never inferred from these metrics. Fixture runs measure
engineering behavior only, even when a gold file is supplied.
"""
import hashlib
import json
from pathlib import Path

TRIPLE = ('subject_id', 'predicate', 'object_id')
CONTEXT = ('species_id', 'cell_line_id', 'condition', 'compartment')
ATTRIBUTIONS = ('own_experiment', 'model_prediction', 'cited_result', 'review_summary', 'unknown')


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _index(rows, key):
    result = {}
    for row in rows:
        value = row[key]
        if not isinstance(value, str) or not value or value in result:
            raise ValueError('invalid or duplicate ' + key)
        result[value] = row
    return result


def _metrics(tp, fp, fn):
    return dict(tp=tp, fp=fp, fn=fn,
                precision=tp / (tp + fp) if tp + fp else None,
                recall=tp / (tp + fn) if tp + fn else None,
                f1=2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None)


def _sets(expected, predicted):
    return _metrics(len(expected & predicted), len(predicted - expected), len(expected - predicted))


def _screen(reports, predictions, label):
    tp = fp = fn = tn = abstentions = 0
    for pid, report in reports.items():
        decision = predictions.get(pid, 'unclear')
        if decision not in ('include', 'exclude', 'unclear', 'uncertain'):
            raise ValueError('invalid screening decision')
        positive = report[label] == 'include'
        tp += positive and decision == 'include'
        fp += not positive and decision == 'include'
        fn += positive and decision != 'include'
        tn += not positive and decision == 'exclude'
        abstentions += decision in ('unclear', 'uncertain')
    return dict(_metrics(tp, fp, fn), tn=tn, papers=len(reports), abstentions=abstentions,
                abstention_rate=abstentions / len(reports) if reports else None)


def _key(pid, relation, fields):
    values = tuple(relation.get(field) for field in fields)
    if any(not isinstance(relation.get(field), str) or not relation[field] for field in TRIPLE):
        raise ValueError('invalid relation triple')
    if any(value is not None and not isinstance(value, str) for value in values):
        raise ValueError('invalid relation field')
    return (pid, *values)


def evaluate(review_path: Path, gold_path: Path | None, output_path: Path) -> dict:
    """Write a new JSON artifact exclusively; never overwrite any existing file.

    Invalid gold, leakage, ambiguous screening events or broken references raise
    ValueError before writing. No gold produces not_evaluated without metrics.
    Provenance hashes refer to the exact input bytes and this evaluator's code.
    """
    review_bytes = review_path.read_bytes()
    review = json.loads(review_bytes)
    manifest = review.get('manifest', {})
    processing_mode = review.get('qc', {}).get('processing_mode',
        manifest.get('processing_mode', manifest.get('config', {}).get('processing_mode', 'llm')))
    synthetic = (manifest.get('mode') == 'synthetic_demo'
                 or review.get('qc', {}).get('synthetic_demo') is True)
    result = dict(status='not_evaluated', scientific_quality='not_evaluated',
                  processing_mode=processing_mode,
                  provenance=dict(review_sha256=_sha(review_bytes), gold_sha256=None,
                                  evaluator_sha256=_sha(Path(__file__).read_bytes()),
                                  pipeline_code_hashes=manifest.get('code_hashes', {})))
    if gold_path is None:
        result['reason'] = 'no_gold'
    else:
        gold_bytes = gold_path.read_bytes()
        gold = json.loads(gold_bytes)
        if type(gold.get('version')) is not int or gold['version'] != 1 or not isinstance(gold.get('reports'), list):
            raise ValueError('expected gold version 1 reports list')
        reports = _index(gold['reports'], 'paper_id')
        for report in reports.values():
            if report.get('split') not in ('train', 'test') or report.get('screening') not in ('include', 'exclude'):
                raise ValueError('invalid gold split or screening')
            if 'fulltext_eligibility' in report and report['fulltext_eligibility'] not in ('include', 'exclude'):
                raise ValueError('invalid gold fulltext_eligibility')
            if report.get('extraction_complete') is not True or not isinstance(report.get('relations'), list):
                raise ValueError('gold requires extraction_complete=true and relations list')
            for relation in report['relations']:
                if not all(field in relation for field in CONTEXT):
                    raise ValueError('gold requires explicit context fields')
                _key(report['paper_id'], relation, TRIPLE + CONTEXT)
                if 'attribution' in relation and relation['attribution'] not in ATTRIBUTIONS:
                    raise ValueError('invalid gold attribution')
        tests = {pid: r for pid, r in reports.items() if r['split'] == 'test'}
        training = {pid for pid, r in reports.items() if r['split'] == 'train'}
        for config in (manifest, manifest.get('config', {})):
            ids = config.get('training_paper_ids', [])
            if not isinstance(ids, list) or any(not isinstance(pid, str) for pid in ids):
                raise ValueError('invalid training_paper_ids')
            training.update(ids)
        if training & tests.keys():
            raise ValueError('training/test paper leakage')
        if not tests:
            raise ValueError('gold has no test papers')
        papers = _index(review['papers'], 'paper_id')
        if tests.keys() - papers.keys():
            raise ValueError('test papers missing from review')
        result['provenance']['gold_sha256'] = _sha(gold_bytes)
        synthetic = synthetic or gold.get('synthetic_demo') is True
        scope = gold.get('prediction_scope', 'attributed')
        if scope not in ('attributed', 'reported_assertions', 'own_experiment'):
            raise ValueError('invalid gold prediction_scope')
        result['prediction_scope'] = scope
        result['reference_source'] = gold.get('annotation_source', 'unspecified; not assumed human')
        accepted = ('auto_pass', 'assertion_pass') if scope == 'reported_assertions' else ('auto_pass',)
        baseline = review['baseline']
        decisions = {}
        active = manifest.get('active_event_ids')
        for stage in ('title_abstract', 'fulltext_eligibility'):
            rows = [r for r in review['screening'] if r['stage'] == stage
                    and (active is None or r.get('event_id') in active)]
            decisions[stage] = {pid: r['decision'] for pid, r in _index(rows, 'paper_id').items()}
        baseline_decisions = {pid: r['decision'] for pid, r in _index(baseline['screening'], 'paper_id').items()}
        fulltext = {pid: r for pid, r in tests.items() if 'fulltext_eligibility' in r}
        result['screening'] = {
            processing_mode: _screen(tests, decisions['title_abstract'], 'screening'),
            'baseline': _screen(tests, baseline_decisions, 'screening'),
            'fulltext_eligibility': {
                processing_mode: _screen(fulltext, decisions['fulltext_eligibility'], 'fulltext_eligibility'),
                'baseline': {'status': 'unsupported'}}}
        strict = {pid for pid, r in tests.items() if all('attribution' in rel for rel in r['relations'])}
        fields = TRIPLE + CONTEXT + ('attribution',)
        expected = {_key(pid, rel, TRIPLE) for pid, r in tests.items() for rel in r['relations']}
        expected_strict = {_key(pid, rel, fields) for pid in strict for rel in tests[pid]['relations']}
        relations = _index(review['relations'], 'relation_id')
        documents = _index(review['documents'], 'document_id')
        predicted, predicted_strict, abstained = set(), set(), set()
        for ev in review['evidence']:
            if ev['document_id'] not in documents or ev['relation_id'] not in relations:
                raise ValueError('broken evidence reference')
            pid = documents[ev['document_id']]['paper_id']
            if pid not in papers:
                raise ValueError('unknown document paper')
            if pid not in tests:
                continue
            rel = dict(relations[ev['relation_id']], attribution=ev.get('attribution', 'unknown'))
            if (ev.get('validation_status') not in accepted or ev.get('stance') != 'supports'
                    or scope == 'own_experiment' and ev.get('attribution') != 'own_experiment'):
                abstained.add(_key(pid, rel, fields))
                continue
            predicted.add(_key(pid, rel, TRIPLE))
            if pid in strict:
                predicted_strict.add(_key(pid, rel, fields))
        baseline_predictions = {_key(r['paper_id'], r, TRIPLE) for r in baseline['candidates'] if r['paper_id'] in tests}
        result['extraction'] = dict(
            unit='unique paper-level relation; micro counts; emitted predictions against all test reports',
            limitations=[
                'Baseline extraction is conditioned on pipeline-selected texts and available annotations; '
                'it is not a standalone rule pipeline on all reports. Recall includes losses from those gates.',
                'The screening baseline is independent of pipeline decisions.'],
            paper_ids=sorted(tests),
            exact_triple={processing_mode: _sets(expected, predicted), 'baseline': _sets(expected, baseline_predictions)},
            strict_context_attribution={processing_mode: _sets(expected_strict, predicted_strict),
                'paper_ids': sorted(strict), 'excluded_paper_ids': sorted(tests.keys() - strict),
                'status': 'evaluated' if strict else 'not_evaluated'},
            **{processing_mode + '_abstained_relations': len(abstained)},
            baseline_unsupported_fields=[*CONTEXT, 'attribution', 'experimental_method'],
            experimental_method='not_annotated_in_gold_v1')
        result.update(status='evaluated', test_paper_ids=sorted(tests), training_paper_ids=sorted(training))
    result['synthetic_demo'] = synthetic
    result['interpretation'] = ('engineering fixtures only; not validated biological quality' if synthetic
                                else 'agreement with supplied gold only; scientific quality not evaluated')
    payload = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n'
    with output_path.open('x', encoding='utf-8') as stream:
        stream.write(payload)
    return result
