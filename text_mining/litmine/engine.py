"""Review pipeline. No graph or Parquet writes.

Task IDs: title_abstract:<paper_id>, fulltext_eligibility:<document_id>:<start>,
extract:<document_id>:<start>. start is a Unicode document offset.
Screening response: decision, criterion_id, reason, evidence_quote; optional
criteria_evidence maps criterion IDs to verbatim quotes. Fulltext inclusion needs
I1 and I2 evidence. Multiple chunks use fulltext_decision:<document_id> (fixture:
fulltext_decision:*), with the same response fields and both criteria_evidence
entries. conflicting_evidence=true preserves unresolved contradictions. Single
chunks are decided directly without synthesis. All evidence is validated first.
Extraction response: candidates list; each item uses canonical subject_id/object_id,
predicate, quote, subject_quote/object_quote, stance and attribution. Optional
quote_start/subject_start/object_start disambiguate chunk-relative spans. context
maps species_id/cell_line_id/condition/compartment to {value, quote}; attribution_quote
and experimental_method={value, quote} must occur inside the evidence quote.
Wildcard fixture task responses are documented in llm.py. Deterministic rules are
the default client; the loose baseline remains separate from validated primary
relations. Evaluation is a separate parent task.
"""
import csv
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import platform
import re

from . import sources
from .llm import IntegrityError, digest, encoded, sanitize
from . import rules

def _prompt_annotations(value):
    """Keep annotation semantics, not run-local provenance paths, in cache keys."""
    if isinstance(value, dict):
        return {k: _prompt_annotations(v) for k, v in value.items() if k != 'source_ref'}
    if isinstance(value, list):
        return [_prompt_annotations(v) for v in value]
    return value


VERSION = 'litmine-engine-v1'
CRITERIA = {
    'I1': 'Molecular relation between circadian clock and cancer/checkpoint regulation; co-mention is insufficient.',
    'I2': 'Report permits attribution to a relevant investigation or mechanistic model; extraction success is not required.',
    'E1': 'Topic outside the agreed molecular clock/cancer/checkpoint scope.',
    'E2': 'No relevant molecular connection after assessment of the available fulltext.',
    'E3': 'Publication type outside primary synthesis: reviews are search aids, not original experiments.',
}
TOPIC_CRITERIA = dict(CRITERIA, I1='Clock and cancer/checkpoint topic scope in the document; not a relation claim.')
TASK4_CRITERIA = dict(CRITERIA,
    I1='Caco2 and SARS-CoV-2/COVID-19 topic scope in the document; not cell-specific evidence.',
    I2='Explicit investigation statement; not attribution of individual assertions.',
    E1='Outside Caco2/SARS-CoV-2 document scope.',
    E2='No relevant topic evidence after assessment of available fulltext.')
PREDICATES = ('ACTIVATES', 'INHIBITS', 'UPREGULATED_IN', 'DOWNREGULATED_IN', 'UPREGULATES', 'DOWNREGULATES', 'BINDS', 'STABILIZES', 'UBIQUITINATES',
              'PROMOTES_DEGRADATION', 'PROMOTES_NUCLEAR_IMPORT')
ATTRIBUTIONS = ('own_experiment', 'model_prediction', 'cited_result', 'review_summary', 'unknown')
CONTEXT = ('species_id', 'cell_line_id', 'condition', 'compartment')
SCREEN_SCHEMA = {'decision': 'include|exclude|unclear', 'criterion_id': 'supplied criterion ID or null for unclear',
                 'reason': 'nonempty explanation', 'evidence_quote': 'nonempty verbatim text for include/exclude',
                 'criteria_evidence': 'criterion ID to verbatim quote mapping; include I1 and I2 when supported; never invent missing evidence',
                 'conflicting_evidence': 'boolean, true for unresolved contradictory evidence, including semantic unclear'}
EXTRACT_SCHEMA = {'candidates': [{'subject_id': 'supplied canonical annotation ID',
    'object_id': 'supplied canonical annotation ID', 'predicate': list(PREDICATES),
    'quote': 'one contiguous verbatim evidence region containing arguments and context',
    'subject_quote': 'verbatim annotated mention', 'object_quote': 'verbatim annotated mention',
    'quote_start': 'optional chunk-relative Unicode offset',
    'subject_start': 'optional chunk-relative Unicode offset', 'object_start': 'optional chunk-relative Unicode offset',
    'stance': 'supports|inconclusive (refutes is reserved)', 'attribution': list(ATTRIBUTIONS),
    'attribution_quote': 'verbatim supporting text, otherwise attribution unknown',
    'experimental_method': 'null or {value: verbatim method name, quote: verbatim support}',
    'context': {key: 'null or {value: supplied canonical ID or verbatim value, quote: verbatim support}' for key in CONTEXT}}]}
RECORD_FIELDS = 'record_id search_id source_identifier paper_id duplicate_of raw_ref'.split()
SCREEN_FIELDS = ('event_id paper_id record_id stage decision primary_reason_code criterion_id reason evidence_quote '
                 'document_id input_hash screening_run_id decided_at supersedes_event_id').split()


def _json_file(path, value):
    path.write_bytes(encoded(value) + b'\n')


def _csv_file(path, rows, fields):
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def _unclear(reason, response_valid=False):
    return dict(decision='unclear', criterion_id=None, primary_reason_code=reason,
                reason=reason, evidence_quote=None, response_valid=response_valid,
                criteria_evidence={}, conflicting_evidence=False)


def validate_screen(response, text, criteria, stage):
    if not isinstance(response, dict):
        return _unclear('invalid_screening_response')
    decision = response.get('decision')
    criterion = response.get('criterion_id')
    quote, reason = response.get('evidence_quote'), response.get('reason')
    if decision not in ('include', 'exclude', 'unclear') or not isinstance(reason, str) or not reason.strip():
        return _unclear('invalid_screening_decision')
    evidence = response.get('criteria_evidence', {})
    conflict = response.get('conflicting_evidence', False)
    if (not isinstance(evidence, dict) or type(conflict) is not bool
            or any(k not in criteria or not isinstance(v, str) or not v.strip() or v not in text
                   for k, v in evidence.items())):
        return _unclear('invalid_screening_criteria_evidence')
    if decision == 'unclear':
        if ((criterion is not None and (not isinstance(criterion, str) or criterion not in criteria))
                or (quote is not None and (not isinstance(quote, str) or not quote.strip() or quote not in text))):
            return _unclear('invalid_screening_evidence_or_criterion')
        return dict(_unclear(reason, True), criteria_evidence=dict(evidence),
                    evidence_quote=quote, conflicting_evidence=conflict)
    if (not isinstance(criterion, str) or criterion not in criteria or not isinstance(quote, str) or not quote.strip() or quote not in text
            or not criterion.startswith('I' if decision == 'include' else 'E')
            or stage == 'title_abstract' and criterion == 'E2'):
        return _unclear('invalid_screening_evidence_or_criterion')
    evidence = dict(evidence)
    evidence.setdefault(criterion, quote)
    return dict(decision=decision, criterion_id=criterion, reason=reason,
                evidence_quote=quote, primary_reason_code=criterion, response_valid=True,
                criteria_evidence=evidence, conflicting_evidence=conflict)


def validate_fulltext_decision(response, document, criteria, assessments):
    outcome = validate_screen(response, document['text'], criteria, 'fulltext_eligibility')
    if not outcome['response_valid']:
        return outcome
    if outcome['conflicting_evidence']:
        return _unclear('conflicting_fulltext_evidence', True)
    supplied = [q for assessment in assessments for q in
                [assessment['evidence_quote'], *assessment['criteria_evidence'].values()] if q]
    quote = outcome['evidence_quote']
    if quote and not any(quote in original for original in supplied):
        return _unclear('final_quote_not_in_bundle')
    for criterion, quote in outcome['criteria_evidence'].items():
        if not any(quote in a['criteria_evidence'].get(criterion, '') for a in assessments):
            return _unclear('final_criterion_not_in_bundle')
    if outcome['decision'] == 'include':
        if not {'I1', 'I2'} <= outcome['criteria_evidence'].keys():
            return _unclear('missing_fulltext_inclusion_criteria')
        if not any(a['decision'] == 'include' for a in assessments):
            return _unclear('no_positive_chunk_assessment')
    return outcome


def chunks(text, size, overlap):
    if type(size) is not int or type(overlap) is not int or not 0 <= overlap < size:
        raise ValueError('invalid_chunk_bounds')
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        yield start, end, text[start:end]
        if end == len(text):
            break
        start = end - overlap


def _span(text, quote, offset=None):
    if not isinstance(quote, str) or not quote:
        raise ValueError('missing_quote')
    if offset is not None:
        if type(offset) is not int or offset < 0 or text[offset:offset + len(quote)] != quote:
            raise ValueError('quote_offset_mismatch')
        return offset, offset + len(quote)
    first = text.find(quote)
    if first < 0:
        raise ValueError('quote_not_found')
    if text.find(quote, first + 1) >= 0:
        raise ValueError('ambiguous_quote')
    return first, first + len(quote)


def argument_types(predicate, skind, okind):
    if predicate in ('UPREGULATED_IN', 'DOWNREGULATED_IN'):
        return skind in ('Gene', 'Protein') and okind == 'CellLine'
    if predicate in ('UPREGULATES', 'DOWNREGULATES', 'ACTIVATES', 'INHIBITS'):
        return skind in ('Gene', 'Protein') and okind in ('Gene', 'Protein')
    return skind == okind == 'Protein'


def validate_candidate(item, document, start, end, annotations, extractor_id, reported_assertions=False):
    """Return structurally valid relation/evidence; do not accept model validation flags."""
    if not isinstance(item, dict):
        raise ValueError('candidate_not_object')
    text = document['text'][start:end]
    entities = {e['entity_id']: e for e in annotations['entities']}
    subject, obj, predicate = item['subject_id'], item['object_id'], item['predicate']
    if subject not in entities or obj not in entities:
        raise ValueError('unresolved_entity')
    if predicate not in PREDICATES:
        raise ValueError('unsupported_predicate')
    skind, okind = entities[subject]['kind'], entities[obj]['kind']
    valid = argument_types(predicate, skind, okind)
    if not valid:
        raise ValueError('invalid_argument_types')
    quote_offset = item.get('quote_start')
    quote_text = item.get('quote')
    if quote_offset is None and isinstance(quote_text, str) and quote_text and text.count(quote_text) > 1:
        positions = []
        at = text.find(quote_text)
        while at >= 0:
            if all(any(m['entity_id'] == eid and m['text'] == item.get(role + '_quote')
                       and start + at <= m['start'] < m['end'] <= start + at + len(quote_text)
                       and (item.get(role + '_start') is None or m['start'] == start + item[role + '_start'])
                       for m in annotations['mentions']) for role, eid in (('subject', subject), ('object', obj))):
                positions.append(at)
            at = text.find(quote_text, at + 1)
        if len(positions) != 1:
            raise ValueError('ambiguous_quote')
        quote_offset = positions[0]
    qstart, qend = _span(text, quote_text, quote_offset)
    arg_spans = []
    for role, eid in (('subject', subject), ('object', obj)):
        quote = item.get(role + '_quote')
        candidates = [m for m in annotations['mentions'] if m['entity_id'] == eid
                      and m['text'] == quote and start + qstart <= m['start'] < m['end'] <= start + qend]
        offset = item.get(role + '_start')
        if offset is not None:
            if type(offset) is not int:
                raise ValueError('invalid_argument_offset')
            candidates = [m for m in candidates if m['start'] == start + offset]
        if len(candidates) != 1:
            raise ValueError('unresolved_argument_span')
        m = candidates[0]
        if document['text'][m['start']:m['end']] != m['text']:
            raise IntegrityError('annotation_span_changed')
        arg_spans.append((m['start'], m['end']))
    quote = item['quote']
    issues, context = [], dict.fromkeys(CONTEXT)
    context_input = item.get('context') or {}
    if not isinstance(context_input, dict):
        raise ValueError('invalid_context')
    for key in CONTEXT:
        supplied = context_input.get(key)
        if supplied is None:
            continue
        if not isinstance(supplied, dict):
            issues.append('unproven_' + key)
            continue
        value, support = supplied.get('value'), supplied.get('quote')
        if not isinstance(support, str) or not support or support not in quote:
            issues.append('unproven_' + key)
            continue
        if key in ('species_id', 'cell_line_id'):
            kind = 'Species' if key == 'species_id' else 'CellLine'
            matches = [m for m in annotations['mentions'] if m['entity_id'] == value
                       and start + qstart <= m['start'] < m['end'] <= start + qend and m['text'] in support]
            if value not in entities or entities[value]['kind'] != kind or not matches:
                issues.append('unresolved_' + key)
                continue
        elif not isinstance(value, str) or not value or value not in support:
            issues.append('unproven_' + key)
            continue
        context[key] = value
    taxons = {entities[eid].get('taxon_id') for eid in (subject, obj)} - {None}
    if len(taxons) > 1 or context['species_id'] and taxons and context['species_id'] not in taxons:
        issues.append('mixed_or_inconsistent_species')
    stance = item.get('stance')
    if stance not in ('supports', 'inconclusive', 'refutes'):
        raise ValueError('invalid_stance')
    if stance != 'supports' or re.search(r'\b(no|not|never|neither|without|failed|fails|may|might|hypothes\w*|suggest\w*)\b', quote, re.I):
        stance = 'inconclusive'
        issues.append('negation_speculation_or_inconclusive')
    attribution = item.get('attribution', 'unknown')
    if attribution not in ATTRIBUTIONS:
        raise ValueError('invalid_attribution')
    support = item.get('attribution_quote')
    if attribution != 'unknown' and (not isinstance(support, str) or not support or support not in quote):
        attribution = 'unknown'
        issues.append('unproven_attribution')
    if attribution == 'unknown':
        issues.append('unknown_attribution')
    method = None
    supplied = item.get('experimental_method')
    if supplied is not None:
        if (isinstance(supplied, dict) and isinstance(supplied.get('value'), str) and supplied['value']
                and isinstance(supplied.get('quote'), str) and supplied['quote']
                and supplied['quote'] in quote and supplied['value'] in supplied['quote']):
            method = supplied['value']
        else:
            issues.append('unproven_experimental_method')
    if predicate == 'BINDS' and subject > obj:
        subject, obj = obj, subject
        arg_spans.reverse()
    status = 'uncertain' if issues else 'auto_pass'
    if reported_assertions and issues == ['unknown_attribution']:
        status = 'assertion_pass'
    relation = dict(subject_id=subject, predicate=predicate, object_id=obj, **context)
    relation['relation_id'] = 'relation:' + digest(relation)
    evidence = dict(relation_id=relation['relation_id'], document_id=document['document_id'],
                    start=start + qstart, end=start + qend, quote=quote,
                    subject_start=arg_spans[0][0], subject_end=arg_spans[0][1],
                    object_start=arg_spans[1][0], object_end=arg_spans[1][1],
                    section=None, source_locator=None, stance=stance, attribution=attribution,
                    experimental_method=method, validation_status=status,
                    extractor_id=extractor_id, score=None)
    if reported_assertions:
        headings = list(re.finditer(r'(?im)^(?:#{1,6} )?(Introduction|Results|Discussion|Methods|Materials and methods|Conclusion|Conclusions)\s*$',
                                    document['text'][:start + qstart]))
        evidence['section'] = headings[-1].group(1) if headings else None
        evidence['source_locator'] = f"unicode:{start + qstart}:{start + qend}"
    evidence['evidence_id'] = 'evidence:' + digest(evidence)
    return relation, evidence, issues


def _baseline(text, annotations):
    # ponytail: sentence-local literal baseline; extend only against a held-out gold set.
    candidates = []
    for sentence in re.finditer(r'[^.!?\n]+[.!?]?', text):
        mentions = [m for m in annotations['mentions'] if sentence.start() <= m['start'] < m['end'] <= sentence.end()]
        for verb, predicate in (('binds', 'BINDS'), ('upregulates', 'UPREGULATES'), ('downregulates', 'DOWNREGULATES')):
            match = re.search(r'\b' + verb + r'\b', sentence.group(), re.I)
            if not match:
                continue
            at = sentence.start() + match.start()
            for left in mentions:
                for right in mentions:
                    if left['end'] <= at < right['start']:
                        candidates.append(dict(subject_id=left['entity_id'], object_id=right['entity_id'],
                            predicate=predicate, start=sentence.start(), end=sentence.end(), quote=sentence.group()))
    return candidates


def prisma_counts(records, papers, events):
    active = {}
    for event in events:
        key = (event['paper_id'], event['stage'])
        if key in active:
            raise IntegrityError('multiple_active_screenings')
        active[key] = event
    counts = dict(identified_records=len(records), retained_records=sum(bool(r['paper_id']) and not r['duplicate_of'] for r in records),
                  duplicates=sum(bool(r['duplicate_of']) for r in records),
                  other_pre_screen_removals=sum(not r['paper_id'] for r in records),
                  reports=len(papers), studies=None, human_screening_reviewers=0)
    for stage, decisions in {'title_abstract': ('include', 'exclude', 'unclear', 'not_processed'),
                             'retrieval': ('retrieved', 'not_retrieved', 'pending', 'not_processed'),
                             'fulltext_eligibility': ('include', 'exclude', 'unclear', 'not_processed')}.items():
        counts[stage] = {d: sum(e['stage'] == stage and e['decision'] == d for e in events) for d in decisions}
    ta, ret, ft = (counts[k] for k in ('title_abstract', 'retrieval', 'fulltext_eligibility'))
    counts.update(abstract_screenings_completed=ta['include'] + ta['exclude'] + ta['unclear'],
                  forwarded_reports=ta['include'] + ta['unclear'],
                  included_reports=ft['include'], fulltext_exclusions=ft['exclude'],
                  unresolved_reports=ta['not_processed'] + ret['not_retrieved'] + ret['pending'] + ret['not_processed'] + ft['unclear'] + ft['not_processed'])
    checks = dict(records=counts['identified_records'] == counts['retained_records'] + counts['duplicates'] + counts['other_pre_screen_removals'],
                  retained=counts['retained_records'] == counts['abstract_screenings_completed'] + ta['not_processed'],
                  abstracts=counts['abstract_screenings_completed'] == ta['exclude'] + counts['forwarded_reports'],
                  retrieval=counts['forwarded_reports'] == sum(ret.values()),
                  eligibility=ret['retrieved'] == sum(ft.values()),
                  final=sum(ft.values()) == ft['include'] + ft['exclude'] + ft['unclear'] + ft['not_processed'])
    counts['identities'] = checks
    if not all(checks.values()):
        raise IntegrityError('prisma_count_identity_failed')
    counts['fulltext_exclusion_reasons'] = {code: sum(e['stage'] == 'fulltext_eligibility' and e['decision'] == 'exclude' and e['primary_reason_code'] == code for e in events)
                                         for code in sorted({e['primary_reason_code'] for e in events if e['stage'] == 'fulltext_eligibility' and e['decision'] == 'exclude'})}
    return counts


def _source_integrity(events):
    for event in events:
        detail = str(event.get('detail', '')) + str(event.get('reason', ''))
        if any(code in detail for code in ('cache_hash_mismatch', 'cache_collision', 'cache_identity_mismatch')):
            raise IntegrityError('source_cache_integrity_failed')


def _check_review(review):
    maps = {}
    for table, key in (('papers', 'paper_id'), ('documents', 'document_id'), ('entities', 'entity_id'),
                       ('relations', 'relation_id'), ('evidence', 'evidence_id')):
        rows = review[table]
        maps[table] = {r[key]: r for r in rows}
        if len(maps[table]) != len(rows):
            raise IntegrityError('duplicate_' + key)
    included = {e['paper_id'] for e in review['screening'] if e['stage'] == 'fulltext_eligibility' and e['decision'] == 'include'}
    for doc in review['documents']:
        if doc['paper_id'] not in maps['papers'] or digest(doc['text'].encode()) != doc['text_sha256']:
            raise IntegrityError('document_integrity')
    for rel in review['relations']:
        if rel['subject_id'] not in maps['entities'] or rel['object_id'] not in maps['entities']:
            raise IntegrityError('relation_integrity')
    for ev in review['evidence']:
        doc = maps['documents'].get(ev['document_id'])
        if not doc or doc['paper_id'] not in included or ev['relation_id'] not in maps['relations']:
            raise IntegrityError('evidence_foreign_key')
        if not 0 <= ev['start'] < ev['end'] <= len(doc['text']) or doc['text'][ev['start']:ev['end']] != ev['quote']:
            raise IntegrityError('evidence_span')
        for role in ('subject', 'object'):
            if not ev['start'] <= ev[role + '_start'] < ev[role + '_end'] <= ev['end']:
                raise IntegrityError('argument_span')


def run(config: dict, run_dir: Path) -> Path:
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    if (run_dir / 'review.json').exists():
        raise IntegrityError('review_already_exists_use_new_run_directory')
    processing_mode = config.get('processing_mode', 'llm' if config.get('llm') else 'rules')
    if processing_mode == 'rules':
        client = rules.Client(config, run_dir)
    elif processing_mode == 'llm':
        from .llm import Client
        client = Client(config, run_dir)
    else:
        raise ValueError('invalid_processing_mode')
    builtin = (TASK4_CRITERIA if client.profile == 'task4_caco2_sarscov2' else
               TOPIC_CRITERIA if client.profile == 'clock_cancer' else CRITERIA) if processing_mode == 'rules' else CRITERIA
    criteria = config.get('criteria', builtin)
    if not isinstance(criteria, dict) or not criteria or not all(isinstance(k, str) and isinstance(v, str) and v.strip() for k, v in criteria.items()):
        raise ValueError('criteria_must_be_id_text_mapping')
    if processing_mode == 'rules' and criteria != builtin:
        raise ValueError('rules_require_builtin_criteria')
    settings = config.get('chunking', {})
    size = settings.get('size', max(1, client.max_input_chars // 3))
    overlap = settings.get('overlap', min(500, size // 5))
    list(chunks('check', size, overlap))
    safe_config = sanitize(config)
    run_id = 'run:' + digest([safe_config, VERSION])
    source_config = sanitize(config)
    if client.mode in ('replay', 'fixture') or config.get('replay_dir'):
        source_config['offline'] = True
    acquired = sources.search(source_config, run_dir)
    _source_integrity(acquired['qc'])
    review = dict(papers=acquired['papers'], records=acquired['records'], searches=acquired['searches'],
                  documents=[], entities=[], relations=[], evidence=[], screening=[], qc=list(acquired['qc']),
                  baseline={'screening': [], 'candidates': [], 'evaluation': 'not_evaluated'})
    entities, relations, evidence = {}, {}, {}
    coverage = []
    annotation_coverage = []
    extraction_incomplete = False
    record_map = {r['paper_id']: r['record_id'] for r in review['records'] if r['paper_id'] and not r['duplicate_of']}

    def event(paper, stage, decision, document=None, calls=None):
        calls = calls or []
        row = dict(paper_id=paper['paper_id'], record_id=record_map[paper['paper_id']], stage=stage,
                   document_id=document['document_id'] if document else None,
                   input_hash=document['text_sha256'] if document else digest(paper),
                   screening_run_id='screen:' + digest([run_id, calls]),
                   decided_at=datetime.now(timezone.utc).isoformat(), supersedes_event_id=None, **decision)
        row['event_id'] = 'event:' + digest([run_id, paper['paper_id'], stage, decision, row['input_hash']])
        row['request_ids'] = calls
        review['screening'].append(row)

    def screen(task, data, document, stage):
        answer = client.request(task, data, SCREEN_SCHEMA, document.get('allow_remote_llm', False))
        if answer['status'] != 'ok':
            outcome = _unclear(answer['status'])
        else:
            outcome = validate_screen(answer['response'], data['text'], criteria, stage)
        if outcome['decision'] == 'unclear':
            review['qc'].append(dict(stage=stage, document_id=document['document_id'],
                                     reason=outcome['reason'], request_id=answer['request_id']))
        return outcome, answer['request_id'], answer['status']

    for paper in review['papers']:
        pid = paper['paper_id']
        for field in ('title', 'abstract'):
            if not isinstance(paper.get(field), str):
                review['qc'].append(dict(stage='title_abstract', paper_id=pid, reason='invalid_' + field,
                                         source_ref=paper['source_ref']))
                paper[field] = ''
        text = paper.get('title', '') + '\n' + paper.get('abstract', '')
        abstract = dict(document_id='document:' + digest([pid, 'abstract', VERSION, text]), paper_id=pid,
                        kind='abstract', text=text, text_sha256=digest(text.encode()),
                        source_ref=paper['source_ref'], allow_remote_llm=paper.get('allow_remote_llm') is True)
        review['documents'].append(abstract)
        review['baseline']['screening'].append(dict(paper_id=pid,
            decision='include' if re.search(r'\b(clock|circadian|per[12]|bmal1)\b', text, re.I) and re.search(r'\b(cancer|tumou?r|checkpoint|p53|tp53)\b', text, re.I) else 'exclude'))
        if not paper.get('abstract', '').strip():
            decision, refs = _unclear('missing_abstract'), []
        else:
            decision, ref, _ = screen('title_abstract:' + pid, dict(text=text, criteria=criteria), abstract, 'title_abstract')
            refs = [ref]
        event(paper, 'title_abstract', decision, abstract, refs)
        paper['final_decision'] = 'exclude' if decision['decision'] == 'exclude' else 'unclear'
        if decision['decision'] == 'exclude':
            continue
        fetched = sources.retrieve(paper, source_config, run_dir)
        document = fetched['document']
        reason = fetched['reason']
        if any(word in reason for word in ('cache_hash', 'cache_collision', 'cache_identity')):
            raise IntegrityError(reason)
        if document and (document.get('paper_id') != pid or not document.get('document_id')
                         or not isinstance(document.get('text'), str)
                         or digest(document['text'].encode()) != document.get('text_sha256')):
            raise IntegrityError('retrieved_document_mismatch')
        retrieval = dict(decision='retrieved' if document else 'not_retrieved', primary_reason_code=reason,
                         criterion_id=None, reason=reason, evidence_quote=None)
        event(paper, 'retrieval', retrieval, document)
        if not document:
            review['qc'].append(dict(stage='retrieval', paper_id=pid, reason=reason, source_ref=fetched['source_ref']))
            continue
        review['documents'].append(document)
        # Rules see complete sentences; arbitrary chunk cuts can remove negation.
        segments = ([(0, len(document['text']), document['text'])] if processing_mode == 'rules'
                    else list(chunks(document['text'], size, overlap)))
        decisions, refs = [], []
        for start, end, chunk in segments:
            decision, ref, status = screen(f"fulltext_eligibility:{document['document_id']}:{start}",
                dict(text=chunk, criteria=criteria, chunk_start=start, chunk_end=end,
                     document_length=len(document['text']), instruction='Assess this chunk only. All chunks are assessed separately. Missing evidence stays unclear.'),
                document, 'fulltext_eligibility')
            decisions.append(decision)
            refs.append(ref)
            coverage.append(dict(document_id=document['document_id'], stage='fulltext_eligibility', start=start, end=end,
                                 status=status if status != 'ok' or decision['response_valid'] else 'invalid_response',
                                 decision=decision['decision'], request_id=ref))
        technically_complete = bool(decisions) and all(d['response_valid'] for d in decisions)
        decisions_present = {d['decision'] for d in decisions}
        conflicting = (any(d['conflicting_evidence'] for d in decisions)
                       or {'include', 'exclude'} <= decisions_present
                       or len({d['criterion_id'] for d in decisions if d['decision'] == 'exclude'}) > 1)
        if not technically_complete:
            final = _unclear('incomplete_fulltext_eligibility')
        elif conflicting:
            final = _unclear('conflicting_fulltext_evidence', True)
        elif len(decisions) == 1:
            final = validate_fulltext_decision(decisions[0], document, criteria, decisions)
        else:
            bundle = [dict(start=start, end=end, decision=d['decision'], criterion_id=d['criterion_id'],
                           evidence_quote=d['evidence_quote'], criteria_evidence=d['criteria_evidence'],
                           conflicting_evidence=d['conflicting_evidence'])
                      for (start, end, _), d in zip(segments, decisions)]
            answer = client.request('fulltext_decision:' + document['document_id'],
                dict(criteria=criteria, assessments=bundle, document_length=len(document['text']),
                     instruction='All document chunks were assessed. Synthesize only these validated quotes and assessments. '
                     'No-evidence unclear chunks (e.g. references) need not defeat positive evidence elsewhere. '
                     'Unresolved contradictions or insufficient evidence remain unclear. Include requires separate '
                     'I1 and I2 coverage from the supplied criteria_evidence. Do not upgrade cited results, reviews '
                     'or unknown attribution into the report\'s own experiment. Return only quotes from this bundle.'),
                SCREEN_SCHEMA, document.get('allow_remote_llm', False))
            refs.append(answer['request_id'])
            final = (validate_fulltext_decision(answer['response'], document, criteria, decisions)
                     if answer['status'] == 'ok' else _unclear(answer['status']))
            coverage.append(dict(document_id=document['document_id'], stage='fulltext_decision',
                                 status=answer['status'] if final['response_valid'] else
                                 (answer['status'] if answer['status'] != 'ok' else 'invalid_response'),
                                 decision=final['decision'], request_id=answer['request_id']))
        if final['decision'] == 'unclear':
            review['qc'].append(dict(stage='fulltext_decision', document_id=document['document_id'], reason=final['reason']))
        event(paper, 'fulltext_eligibility', final, document, refs)
        paper['final_decision'] = final['decision']
        if final['decision'] != 'include':
            continue
        annotations = sources.annotate(document, paper, source_config, run_dir)
        _source_integrity(annotations['qc'])
        review['qc'].extend(annotations['qc'])
        sentence_spans = list(rules.assertion_sentences(document['text']))
        annotation_coverage.append(dict(paper_id=pid, document_id=document['document_id'],
            entities=len(annotations['entities']), mentions=len(annotations['mentions']),
            sentences=len(sentence_spans),
            sentences_with_two_mentions=sum(sum(s <= m['start'] < m['end'] <= s + len(q)
                for m in annotations['mentions']) >= 2 for s, q in sentence_spans),
            alignment_methods={method: sum(m.get('provenance', {}).get('alignment', 'local') == method
                for m in annotations['mentions']) for method in sorted({m.get('provenance', {}).get('alignment', 'local')
                for m in annotations['mentions']})}))
        if annotations['qc'] or not annotations['entities'] or not annotations['mentions']:
            extraction_incomplete = True
            coverage.append(dict(document_id=document['document_id'], stage='annotations', status='annotation_coverage_gap'))
        for entity in annotations['entities']:
            old = entities.get(entity['entity_id'])
            if old and (old['kind'] != entity['kind'] or old.get('taxon_id') != entity.get('taxon_id')):
                raise IntegrityError('conflicting_canonical_entity')
            entities.setdefault(entity['entity_id'], entity)
        for candidate in _baseline(document['text'], annotations):
            review['baseline']['candidates'].append(dict(paper_id=pid, document_id=document['document_id'], **candidate))
        for start, end, chunk in segments:
            mentions = [dict(m, start=m['start'] - start, end=m['end'] - start) for m in annotations['mentions'] if start <= m['start'] < m['end'] <= end]
            ids = {m['entity_id'] for m in mentions}
            if len(mentions) < 2:
                extraction_incomplete = True
                coverage.append(dict(document_id=document['document_id'], stage='extract', start=start, end=end, status='no_annotated_arguments'))
                continue
            answer = client.request(f"extract:{document['document_id']}:{start}",
                dict(text=chunk, chunk_start=start, entities=[e for e in annotations['entities'] if e['entity_id'] in ids],
                     mentions=_prompt_annotations(mentions), predicates=list(PREDICATES)), EXTRACT_SCHEMA, document.get('allow_remote_llm', False))
            coverage.append(dict(document_id=document['document_id'], stage='extract', start=start, end=end,
                                 status=answer['status'], request_id=answer['request_id']))
            result = answer['response']
            if answer['status'] != 'ok' or not isinstance(result, dict) or not isinstance(result.get('candidates'), list):
                extraction_incomplete = True
                coverage[-1]['status'] = answer['status'] if answer['status'] != 'ok' else 'invalid_candidates'
                review['qc'].append(dict(stage='extract', document_id=document['document_id'], reason=answer['status'] if answer['status'] != 'ok' else 'invalid_candidates', request_id=answer['request_id']))
                continue
            for item in result['candidates']:
                try:
                    relation, ev, issues = validate_candidate(item, document, start, end, annotations, answer['request_id'],
                        reported_assertions=processing_mode == 'rules' and client.profile != 'legacy_clock')
                except IntegrityError:
                    raise
                except (ValueError, KeyError, TypeError, AttributeError) as exc:
                    extraction_incomplete = True
                    coverage[-1]['status'] = 'invalid_candidate'
                    review['qc'].append(dict(stage='extract', document_id=document['document_id'],
                        validation_status='uncertain' if str(exc) in ('ambiguous_quote', 'unresolved_argument_span') else 'rejected',
                        reason=str(exc), request_id=answer['request_id']))
                    continue
                # Same argument/evidence spans and interpretation across overlaps count once.
                key = digest({k: v for k, v in ev.items() if k not in ('evidence_id', 'extractor_id')})
                if key in evidence:
                    continue
                relations[relation['relation_id']] = relation
                evidence[key] = ev
                if issues:
                    review['qc'].append(dict(stage='extract', evidence_id=ev['evidence_id'], reason=','.join(issues), validation_status=ev['validation_status']))
    review.update(entities=list(entities.values()), relations=list(relations.values()), evidence=list(evidence.values()))
    counts = prisma_counts(review['records'], review['papers'], review['screening'])
    _check_review(review)
    included = {p['paper_id'] for p in review['papers'] if p['final_decision'] == 'include'}
    docs = {d['document_id']: d for d in review['documents']}
    supported = {docs[e['document_id']]['paper_id'] for e in review['evidence'] if e['validation_status'] == 'auto_pass'}
    support_by_attribution = {attribution: sorted({docs[e['document_id']]['paper_id'] for e in review['evidence']
        if e['validation_status'] == 'auto_pass' and e['stance'] == 'supports' and e['attribution'] == attribution})
        for attribution in ATTRIBUTIONS}
    synthetic = config.get('synthetic_demo') is True or client.mode == 'fixture' or any(e.get('origin_mode') == 'fixture' for e in client.events)
    statuses = {s: sum(e['status'] == s for e in client.events) for s in sorted({e['status'] for e in client.events})}
    qc = dict(events=review['qc'], chunk_coverage=coverage, llm_calls=client.calls,
              profile=client.profile if processing_mode == 'rules' else None,
              annotation_coverage=annotation_coverage,
              evidence_status_counts={status: sum(e['validation_status'] == status for e in review['evidence'])
                  for status in ('auto_pass', 'assertion_pass', 'uncertain')},
              reported_assertion_reports=sorted({docs[e['document_id']]['paper_id'] for e in review['evidence']
                  if e['validation_status'] in ('auto_pass', 'assertion_pass') and e['stance'] == 'supports'}),
              processing_mode=processing_mode, rule_version=rules.VERSION if processing_mode == 'rules' else None,
              rule_requests=len(client.events) if processing_mode == 'rules' else 0,
              rule_statuses=statuses if processing_mode == 'rules' else {},
              llm_statuses=statuses if processing_mode == 'llm' else {},
              included_without_auto_pass_evidence=sorted(included - supported),
              extraction_incomplete=extraction_incomplete,
              machine_support_reports_by_attribution=support_by_attribution,
              evaluation={'screening': 'not_evaluated', 'extraction': 'not_evaluated',
                          'reason': 'synthetic_demo' if synthetic else 'gold_evaluation_is_separate'},
              scientific_quality='not_evaluated', synthetic_demo=synthetic,
              incomplete=bool(extraction_incomplete or counts['unresolved_reports'] or counts['other_pre_screen_removals'] or
                  any(s['completion_status'] != 'complete' for s in review['searches']) or
                  any(e['status'] != 'ok' for e in client.events)))
    review['qc'] = qc
    root = Path(__file__).resolve().parents[1]
    hash_paths = list((root / 'litmine').glob('*.py'))
    protocol_paths = list((root / 'docs' / 'prisma').glob('*.md'))
    lock_paths = [p for name in ('uv.lock', 'requirements.txt', 'pyproject.toml') for p in (root / name, root.parent / name) if p.exists()]
    manifest = dict(schema_version=1, pipeline_version=VERSION, run_id=run_id, config=safe_config,
                    processing_mode=processing_mode, rule_version=qc['rule_version'],
                    code_hashes={str(p.relative_to(root)): digest(p.read_bytes()) for p in hash_paths},
                    protocol_hashes={p.name: digest(p.read_bytes()) for p in protocol_paths},
                    dependency_hashes={str(p): digest(p.read_bytes()) for p in lock_paths},
                    runtime={'python': platform.python_version(), 'dependencies': sorted((d.metadata.get('Name', ''), d.version) for d in importlib.metadata.distributions())},
                    criteria=criteria, criteria_hash=digest(criteria), chunking={'version': VERSION, 'unit': 'whole_document' if processing_mode == 'rules' else 'characters', 'size': None if processing_mode == 'rules' else size, 'overlap': 0 if processing_mode == 'rules' else overlap, 'aggregation': 'bounded validated-evidence synthesis after complete chunk assessment; I1/I2 required; contradictions stay open'},
                    active_event_ids=[e['event_id'] for e in review['screening']],
                    screening_requests={e['screening_run_id']: e['request_ids'] for e in review['screening']},
                    evidence_requests={e['evidence_id']: e['extractor_id'] for e in review['evidence']},
                    deduplication='sources v1: seeds then query/page order, first record retained',
                    model_revision=client.config.get('model_revision'), mode='synthetic_demo' if synthetic else 'pilot_exploration',
                    evaluation=qc['evaluation'], studies=None, output_hashes={})
    _csv_file(run_dir / 'records.csv', review['records'], RECORD_FIELDS)
    _csv_file(run_dir / 'screening.csv', review['screening'], SCREEN_FIELDS)
    _json_file(run_dir / 'prisma_counts.json', counts)
    _json_file(run_dir / 'qc.json', qc)
    _json_file(client.root / 'calls.json', client.events)
    exclusions = [e for e in review['screening'] if e['decision'] == 'exclude']
    report = ['# Literature review pilot', '',
              'SYNTHETIC DEMO: not publication evidence or a scientific evaluation.' if synthetic else 'Exploratory automated run; protocol remains a draft.', '',
              'Processing: deterministic rules; no LLM execution.' if processing_mode == 'rules' else f"Processing: legacy LLM client ({client.mode}); calls: {client.calls}.",
              f"Records: {counts['identified_records']}; reports: {counts['reports']}; included reports: {counts['included_reports']}; unresolved reports: {counts['unresolved_reports']}.",
              'Studies: unknown. Human screening reviewers: 0.',
              f"Incomplete: {qc['incomplete']}. Included without auto-pass evidence: {len(included - supported)}.",
              'Screening and extraction quality: not_evaluated. Scientific quality and risk of bias: not_evaluated.',
              'auto_pass checks text and schema only. No claim of full PRISMA compliance, exhaustive search or biological validity.',
              f"Machine-attributed own-experiment support reports: {len(support_by_attribution['own_experiment'])}.",
              'Cited results, model predictions, review summaries and unknown attribution are counted separately in qc.json, never as own experiments.',
              'No study linkage or official PRISMA flow diagram is produced. Source coverage, access gaps and automation can bias results.', '',
              '## Exclusions', *[f"- {e['paper_id']} ({e['stage']}, {e['criterion_id']}): {e['reason']}" for e in exclusions], '',
              'See searches in review.json, screening.csv and qc.json for queries, decisions and chunk coverage.', '']
    (run_dir / 'report.md').write_text('\n'.join(report), encoding='utf-8')
    manifest['input_hashes'] = {str(p.relative_to(run_dir)): digest(p.read_bytes()) for folder in ('raw', 'llm', 'rules') for p in (run_dir / folder).rglob('*') if p.is_file()}
    manifest['output_hashes'] = {name: digest((run_dir / name).read_bytes()) for name in ('records.csv', 'screening.csv', 'prisma_counts.json', 'qc.json', 'report.md')}
    review['manifest'] = dict(manifest)
    review['prisma_counts'] = counts
    path = run_dir / 'review.json'
    _json_file(path, review)
    manifest['output_hashes'] = dict(manifest['output_hashes'], **{'review.json': digest(path.read_bytes())})
    manifest['hash_note'] = 'review.json embeds the pre-review manifest to avoid a circular self-hash; manifest.json is authoritative.'
    _json_file(run_dir / 'manifest.json', manifest)
    return path
