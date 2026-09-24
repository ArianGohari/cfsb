"""Deterministic, deliberately narrow text rules; not scientific validation."""
from pathlib import Path
import re

from .llm import digest, encoded, immutable

VERSION = 'litmine-rules-v2'
PROFILES = ('clock_cancer', 'task4_caco2_sarscov2', 'legacy_clock')
CLOCK = r'(?:circadian|clock|PER[123]|CRY[12]|BMAL1|ARNTL|CLOCK|NR1D[12])'
CANCER = r'(?:cancer|tumou?r|checkpoint|TP53|p53|MDM2|CDKN1A|p21|ATM|ATR|CHEK[12])'
UNSAFE = re.compile(r"\b(?:no|not|never|neither|without|failed|fails|\w+n['’]t|unlikely|likely|may|might|could|can|would|potential\w*|possible|possibly|probabl\w*|hypothes\w*|suggest\w*|speculat\w*|whether|if)\b", re.I)
VERBS = (
    ('BINDS', r'binds?', r'bound'),
    ('UPREGULATES', r'upregulates?', r'upregulated'),
    ('DOWNREGULATES', r'downregulates?', r'downregulated'),
    ('STABILIZES', r'stabilizes?', r'stabilized'),
    ('UBIQUITINATES', r'ubiquitinates?', r'ubiquitinated'),
    ('PROMOTES_DEGRADATION', r'promotes? degradation of', r'(?!)'),
    ('PROMOTES_NUCLEAR_IMPORT', r'promotes? nuclear import of', r'(?!)'),
)
OWN = re.compile(r'^We (?:measured|demonstrated|observed|showed) (?:experimentally )?that\s+', re.I)
INVESTIGATION = re.compile(r'\b(?:we (?:measured|investigated|tested|demonstrated|observed|showed)|our experiments?|in this study|mechanistic model)\b', re.I)


def sentences(text):
    for match in re.finditer(r'[^.!?\n]+[.!?]?', text):
        value = match.group().strip()
        if value:
            yield match.start() + len(match.group()) - len(match.group().lstrip()), value


def extract(data):
    text, mentions = data['text'], data.get('mentions', [])
    candidates = []
    kinds = {e['entity_id']: e['kind'] for e in data.get('entities', [])}
    for start, quote in sentences(text):
        if UNSAFE.search(quote):
            continue
        local = [m for m in mentions if start <= m['start'] < m['end'] <= start + len(quote)
                 and text[m['start']:m['end']] == m['text']]
        for left in local:
            prefix = text[start:left['start']]
            own = OWN.fullmatch(prefix)
            if prefix and not own:
                continue
            for right in local:
                if left['end'] >= right['start'] or left['entity_id'] == right['entity_id']:
                    continue
                # ponytail: accept only a bare assertion or the demo's literal cell context.
                # Other tails can change the argument or qualify the entire claim.
                tail = text[right['end']:start + len(quote)]
                if not re.fullmatch(r'(?: in human cells)?\.?', tail, re.I):
                    continue
                middle = text[left['end']:right['start']].strip()
                for predicate, active, passive in VERBS:
                    reverse = bool(re.fullmatch(r'(?:is|was|are|were) ' + passive + r' by', middle, re.I))
                    if not reverse and not re.fullmatch(active, middle, re.I):
                        continue
                    allowed = ('Gene', 'Protein') if predicate in ('UPREGULATES', 'DOWNREGULATES') else ('Protein',)
                    if kinds:
                        valid = [m for m in local if kinds.get(m['entity_id']) in allowed]
                        choices = [{m['entity_id'] for m in valid if
                                    (m['start'], m['end']) == (arg['start'], arg['end'])}
                                   for arg in (left, right)]
                        if choices != [{left['entity_id']}, {right['entity_id']}]:
                            continue  # Missing or ambiguous argument type/identity: abstain.
                    # ponytail: only literal adjacent arguments; complex clauses need reviewed rules.
                    subject, obj = (right, left) if reverse else (left, right)
                    candidate = dict(subject_id=subject['entity_id'], object_id=obj['entity_id'],
                        predicate=predicate, quote=quote, quote_start=start,
                        subject_quote=subject['text'], object_quote=obj['text'],
                        subject_start=subject['start'], object_start=obj['start'],
                        stance='supports', attribution='own_experiment' if own else 'unknown')
                    if own:
                        candidate['attribution_quote'] = prefix
                    candidates.append(candidate)
    return {'candidates': candidates}


def assertion_sentences(text):
    """Keep citations and decimals intact; never join paragraphs or reference entries."""
    end = re.search(r'(?im)^\s*(?:references|bibliography)\s*$', text)
    stop = end.start() if end else len(text)
    cursor = 0
    for boundary in re.finditer(r'(?<=[.!?])\s+(?=[A-Z])|\n+', text[:stop]):
        part = text[cursor:boundary.start()]
        if part.strip():
            yield cursor + len(part) - len(part.lstrip()), part.strip()
        cursor = boundary.end()
    if text[cursor:stop].strip():
        part = text[cursor:stop]
        yield cursor + len(part) - len(part.lstrip()), part.strip()


FAMILY = re.compile(r'(?:IFNs?|interferons?|ISGs?|STATs?|JAKs?|MAPKs?|ERKs?|NF[ -]?kB|NF-κB|type[ -]?[I12]+ IFN|RLRs?)', re.I)
CITATION = re.compile(r'\([^()]*\b(?:19|20)\d{2}[a-z]?[^()]*\)|\[\d+(?:[ ,–-]+\d+)*\]')


def extract_assertions(data):
    """Small complete-sentence grammars. Abundance-in-cell is not causal regulation."""
    text = data['text']
    kinds = {e['entity_id']: e['kind'] for e in data.get('entities', [])}
    candidates = []
    for start, quote in assertion_sentences(text):
        if UNSAFE.search(quote) or quote.endswith('?'):
            continue
        local = [m for m in data.get('mentions', [])
                 if start <= m['start'] < m['end'] <= start + len(quote)
                 and text[m['start']:m['end']] == m['text']
                 and kinds.get(m['entity_id']) in ('Gene', 'Protein', 'CellLine')]
        spans = {}
        for m in local:
            spans.setdefault((m['start'], m['end']), {})[m['entity_id']] = m
        if any(len(ids) != 1 for ids in spans.values()):
            continue
        args = [next(iter(ids.values())) for _, ids in sorted(spans.items())]
        if not args or any(a['end'] > b['start'] for a, b in zip(args, args[1:])):
            continue
        masked = quote
        for i in reversed(range(len(args))):
            m = args[i]
            masked = masked[:m['start'] - start] + f'@{i}' + masked[m['end'] - start:]
        cited = bool(CITATION.search(masked))
        masked = CITATION.sub('', masked)
        masked = re.sub(r'\s+', ' ', masked).strip()
        own = OWN.match(masked)
        prefix = own.group() if own else ''
        body = masked[len(prefix):].strip().rstrip('.').strip()
        attribution = 'cited_result' if cited else 'own_experiment' if own else 'unknown'

        def emit(i, j, predicate):
            subject, obj = args[int(i)], args[int(j)]
            if subject['entity_id'] == obj['entity_id']:
                return
            if any(FAMILY.fullmatch(m['text']) or '/' in m['text'] for m in (subject, obj)):
                return
            sk, ok = kinds[subject['entity_id']], kinds[obj['entity_id']]
            if sk not in ('Gene', 'Protein'):
                return
            if predicate.endswith('_IN'):
                if ok != 'CellLine' or re.search(r'\d+h(?:pi)?$', obj['text'], re.I):
                    return  # A timepoint fused to a cell name is not a resolved cell identity.
            elif ok not in ('Gene', 'Protein'):
                return
            item = dict(subject_id=subject['entity_id'], object_id=obj['entity_id'],
                predicate=predicate, quote=quote, quote_start=start,
                subject_quote=subject['text'], object_quote=obj['text'],
                subject_start=subject['start'], object_start=obj['start'],
                stance='supports', attribution=attribution)
            if cited:
                item['attribution_quote'] = CITATION.search(quote).group()
            elif own:
                item['attribution_quote'] = quote[:len(prefix)]
            # Unknown experimental condition/species stays null, including for Caco2 papers.
            candidates.append(item)

        # Literal directed assertions only, no suffix clauses or noun-compound arguments.
        for predicate, active, passive in (*VERBS, ('ACTIVATES', r'activates?', 'activated'),
                                            ('INHIBITS', r'inhibits?', 'inhibited')):
            match = re.fullmatch(r'@(\d+)\s+(?:' + active + r')\s+@(\d+)', body, re.I)
            reverse = re.fullmatch(r'@(\d+) (?:is|was|are|were) ' + passive + r' by @(\d+)', body, re.I)
            if match or reverse:
                a, b = (match or reverse).groups()
                if predicate not in ('UPREGULATES', 'DOWNREGULATES', 'ACTIVATES', 'INHIBITS'):
                    if any(kinds[args[int(k)]['entity_id']] != 'Protein' for k in (a, b)):
                        continue
                emit(b if reverse else a, a if reverse else b, predicate)
        # Explicit single analyte with enumerated cell lines. Contrasts retain direction.
        observation = re.fullmatch(
            r'@(\d+) (?:was|is) (upregulated|downregulated) in (?:both )?'
            r'(@\d+(?:(?:, | and )@\d+)*) cells?'
            r'(?: but was (upregulated|downregulated) in (@\d+)(?: cells?)?)?', body, re.I)
        if observation:
            analyte, direction, cells, contrast, other = observation.groups()
            for cell in re.findall(r'@(\d+)', cells):
                emit(analyte, cell, direction.upper() + '_IN')
            if other:
                emit(analyte, other[1:], contrast.upper() + '_IN')
    return {'candidates': candidates}


def outcome(evidence=None, exclusion=None):
    evidence = evidence or {}
    if exclusion:
        return dict(decision='exclude', criterion_id='E3', reason='Explicit review description; rule assessment only.',
                    evidence_quote=exclusion, criteria_evidence={'E3': exclusion})
    include = 'I1' in evidence
    return dict(decision='include' if include else 'unclear', criterion_id='I1' if include else None,
                reason='Literal rule evidence; missing criteria remain unresolved, not scientifically validated.',
                evidence_quote=evidence.get('I1'), criteria_evidence=evidence)


def legacy_screen(task, data):
    if task == 'fulltext_decision':
        assessments = data['assessments']
        evidence = {k: v for a in assessments for k, v in a['criteria_evidence'].items()}
        if any(a.get('conflicting_evidence') for a in assessments) or (
                any(a['decision'] == 'exclude' for a in assessments) and 'I1' in evidence):
            return dict(outcome(), conflicting_evidence=True)
        return outcome(evidence, evidence.get('E3'))
    text = data['text']
    if task == 'title_abstract':
        return outcome({'I1': text} if re.search(r'\b' + CLOCK + r'\b', text, re.I)
                       and re.search(r'\b' + CANCER + r'\b', text, re.I) else {})
    evidence = {}
    for _, sentence in sentences(text):
        if UNSAFE.search(sentence):
            continue
        if re.fullmatch(r'(?:this (?:article|paper) is a (?:systematic )?review|publication type: review)\.?', sentence, re.I):
            return outcome(exclusion=sentence)
        # Screening is independent of annotation availability and extraction success.
        mentions = [dict(entity_id=m.group().upper(), text=m.group(), start=m.start(), end=m.end())
                    for m in re.finditer(r'\b(?:' + CLOCK + '|' + CANCER + r')\b', sentence, re.I)]
        for candidate in extract(dict(text=sentence, mentions=mentions))['candidates']:
            args = (candidate['subject_quote'], candidate['object_quote'])
            if ((re.fullmatch(CLOCK, args[0], re.I) and re.fullmatch(CANCER, args[1], re.I)) or
                    (re.fullmatch(CLOCK, args[1], re.I) and re.fullmatch(CANCER, args[0], re.I))):
                evidence.setdefault('I1', sentence)
        if INVESTIGATION.search(sentence):
            evidence.setdefault('I2', sentence)
    return outcome(evidence)


def screening_investigation(sentence):
    if sentence.endswith('?') or re.search(
            r'\b(?:plan\w*|intend\w*|aim\w*|propos\w*|will|shall|'
            r'hypothetical\w*|imagin\w*|assum\w*|unless|provided)\b', sentence, re.I):
        return False
    if not UNSAFE.search(sentence):
        return bool(INVESTIGATION.search(sentence))
    match = re.fullmatch(
        r'(?:in this study,?\s+)?we (?:measured|investigated|tested|demonstrated|observed|showed)\s+'
        r'(?:whether|if|that)\s+(.+?)\.?', sentence, re.I)
    return bool(match and not re.search(
        r'[,;:]|\b(?:if|whether|but|yet|and|or|had we|were we)\b', match[1], re.I))


def screen(task, data):
    profile = data.get('profile', 'legacy_clock')
    if profile == 'legacy_clock':
        return legacy_screen(task, data)
    if profile not in PROFILES:
        raise ValueError('unknown_rule_profile')
    if task == 'fulltext_decision':
        return legacy_screen(task, data)
    text = data['text']
    topics = ((r'\bCaco[ -]?2\b', r'\b(?:SARS[ -]CoV[ -]?2|COVID[ -]?19)\b')
              if profile == 'task4_caco2_sarscov2' else
              (r'\b' + CLOCK + r'\b', r'\b' + CANCER + r'\b'))
    evidence = {}
    # Topic eligibility is document-level retrieval scope, not a molecular claim.
    matches = [re.search(pattern, text, re.I) for pattern in topics]
    if all(matches):
        first, last = min(m.start() for m in matches), max(m.end() for m in matches)
        evidence['I1'] = text[first:last]
    if task != 'title_abstract':
        for _, sentence in sentences(text):
            if re.fullmatch(r'(?:this (?:article|paper) is a (?:systematic )?review|publication type: review)\.?', sentence, re.I):
                return outcome(exclusion=sentence)
            if screening_investigation(sentence):
                evidence.setdefault('I2', sentence)
    return outcome(evidence)


def semantic(value):
    if isinstance(value, dict):
        return {k: semantic(v) for k, v in value.items() if k != 'source_ref'}
    if isinstance(value, list):
        return [semantic(v) for v in value]
    return value


class Client:
    mode = 'rules'
    max_input_chars = 24000
    calls = 0

    def __init__(self, config, run_dir):
        self.config = {}
        self.profile = config.get('profile', 'clock_cancer')
        if self.profile not in PROFILES:
            raise ValueError('unknown_rule_profile')
        self.events = []
        self.root = Path(run_dir) / 'rules'
        self.root.mkdir(parents=True, exist_ok=True)

    def request(self, task_id, input_data, schema, allow_remote=False):
        data = dict(semantic(input_data), profile=self.profile)
        request = dict(task_id=task_id, input_data=data, schema=schema, rule_version=VERSION)
        key = digest(request)
        task = task_id.split(':', 1)[0]
        if task not in ('extract', 'title_abstract', 'fulltext_eligibility', 'fulltext_decision'):
            raise ValueError('unknown_rule_task')
        response = ((extract(data) if self.profile == 'legacy_clock' else extract_assertions(data))
                    if task == 'extract' else screen(task, data))
        result = dict(task_id=task_id, request_id=key, input_hash=digest(data), status='ok',
                      response=response, attempt_refs=[], cached=False, origin_mode='rules', mode='rules')
        # Replay recomputes. These immutable artifacts are provenance, not an LLM cache.
        immutable(self.root / key / 'request.json', encoded(request))
        immutable(self.root / key / 'result.json', encoded(result))
        self.events.append(result)
        return result
