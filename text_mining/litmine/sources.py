"""Public literature acquisition, using only the standard library.

Contract
--------
search(config, run_dir) returns papers, records, searches, qc (lists of dicts).
``offline`` defaults to True: only local inputs and verified raw caches are read.
Set it to the literal False to permit public GET requests. ``replay_dir`` names
another run directory (or its raw directory); snapshots are copied into this run.
``_base_dir`` resolves relative seed fulltext_path and annotation paths.
``network`` optionally sets timeout (seconds, default 20, capped at 60) and
max_attempts (default 3, capped at 5). No authentication or text uploads exist.

``search`` accepts source='europepmc', queries (strings), from_year/to_year
(inclusive, optional), max_records (per query, default 1000), page_size (1..1000,
default 100), mode (descriptive, default 'exploratory'). Limits/failures produce
incomplete manifests, not exclusions. Seeds precede queries deterministically;
seed attributes survive normalization/merging. PMID/DOI/PMCID can be supplied
as lower-case keys, or paper_id can be PMID:<id>/DOI:<doi>. Only PMID or DOI
can establish paper_id. Connected identifier conflicts quarantine the whole
component, leaving its records with empty paper_id and a QC entry.

retrieve returns document/None, reason, source_ref. A local UTF-8 plain text
fulltext_path is an explicit assertion that it is the full article (not a title
or abstract). XML paths additionally undergo article/body/identity validation.
Remote fulltext requires is_open_access=True (or Europe PMC isOpenAccess='Y'),
a PMCID, and the Europe PMC fullTextXML endpoint. XML needs a nonempty body,
matching article IDs, and no conflicting supplied identifier. XML text is the
article title and body paragraphs/titles joined by newlines (parser version v1).
No fallback to abstracts, publishers, or restricted endpoints is attempted.
allow_remote_llm is True only for an explicit boolean True on the paper; neither
OA nor license text grants upload permission. A document ID binds paper, parser,
raw bytes and extracted text. Local inputs are snapshotted just like HTTP bodies.

annotate returns entities, mentions, qc; it never returns relations.
``annotations`` maps canonical paper_id to a local JSON filename. JSON requires
paper_id, entities and mentions; optional document_id/text_sha256 must match.
Entities require entity_id, kind (Gene/Protein/Species), name, optional taxon_id.
Namespaces are NCBIGene:<digits>, UniProt:<accession>, NCBITaxon:<digits>.
Mentions require entity_id, integer start/end (Unicode, half open), and text or
quote exactly matching document.text[start:end]. Invalid items yield QC.
``pubtator=True`` fetches public BioC JSON with pmids=<PMID>&full=true for
fulltext documents (full=false otherwise). This endpoint requires PMID; PMC-only
papers return QC. Responses may use the PubTator3 wrapper and numeric PMC id.
Explicit response PMID/PMCID/DOI values must agree with the paper.
Each annotated passage must occur exactly once in document.text. Its original
BioC spans are validated before translation to that exact occurrence. Mentions
retain source_ref and provenance (source_start/end, source_passage_offset,
aligned_passage_offset, passage_index, passage_text_sha256, alignment).
Missing or repeated passages yield QC and no mentions for that passage; other
aligned passages survive. No whitespace normalization or fuzzy matching occurs.
PubTator Gene stays Gene. ``protein_normalization=True`` (default False) adds
separate Protein candidates at the same literal spans using public UniProt search
by exact NCBIGene cross-reference. Only a complete result set with one distinct
reviewed accession is accepted; ambiguous, unreviewed, mismatched or missing
records yield QC. Protein taxon and name come from UniProt, never from prose.
``max_protein_lookups`` (default 20, nonnegative integer) bounds uncached HTTP
attempts across the run via exclusive raw/protein_lookups slots. Failed attempts
consume a slot; protein requests have one attempt and the usual bounded timeout.
Cached responses, including replay_dir, consume no slots; offline never requests.
Completeness requires UniProt's x-total-results header, saved in raw metadata.
Protein mentions retain the Gene span/provenance and add protein_normalization
with gene_entity_id, source_ref, method, candidate_only=True. Gene annotations
are unchanged. Mapping verifies identity, not whether a passage refers to the
protein or supports BINDS/STABILIZES; the evidence selector must decide that.
For independently verified explicit protein annotations,
set annotations={paper_id: 'annotations.json'} with kind='Protein', a supported
UniProt entity_id, and exact mentions as specified above. No ID is inferred.

raw/<sha256(url)>/<sha256(body)>.body and immutable *.json manifests contain URL,
UTC timestamp, HTTP status, body filename and SHA256. All reads verify hashes.
A successful snapshot wins over failed attempts; offline replay never retries.
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

EPMC = 'https://www.ebi.ac.uk/europepmc/webservices/rest/'
PUBTATOR = 'https://www.ncbi.nlm.nih.gov/research/pubtator-api/publications/export/biocjson'
UNIPROT = 'https://rest.uniprot.org/uniprotkb/search'
PARSER = 'sources-v1'


def _hash(value):
    return hashlib.sha256(value).hexdigest()


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True).encode('utf-8')


def _utc():
    return datetime.now(timezone.utc).isoformat()


def _qc(reason, **fields):
    return dict(stage='sources', reason=reason, code=reason, **fields)


def _immutable(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('xb') as handle:
            handle.write(body)
    except FileExistsError:
        if path.read_bytes() != body:
            raise ValueError('cache_collision')


def _save(url, body, status, run_dir, **extra):
    folder = Path(run_dir) / 'raw' / _hash(url.encode())
    digest = _hash(body)
    _immutable(folder / (digest + '.body'), body)
    meta = dict(url=url, fetched_at_utc=_utc(), http_status=status,
                body=digest + '.body', sha256=digest, **extra)
    encoded = _json(meta)
    path = folder / (_hash(encoded) + '.json')
    _immutable(path, encoded)
    return body, str(path), meta


def _cached(url, config, run_dir, validator=None):
    roots = [Path(run_dir) / 'raw']
    if config.get('replay_dir'):
        replay = Path(config['replay_dir'])
        if not replay.is_absolute():
            replay = Path(config.get('_base_dir', '.')) / replay
        roots.append(replay if replay.name == 'raw' else replay / 'raw')
    for root in roots:
        candidates = []
        for path in sorted((root / _hash(url.encode())).glob('*.json')):
            meta = json.loads(path.read_bytes())
            if meta['url'] != url or Path(meta['body']).name != meta['body']:
                raise ValueError('cache_identity_mismatch')
            body = (path.parent / meta['body']).read_bytes()
            if _hash(body) != meta['sha256'] or meta['body'] != meta['sha256'] + '.body':
                raise ValueError('cache_hash_mismatch')
            candidates.append((body, path, meta))
        if candidates:
            candidates.sort(key=lambda x: (x[2]['http_status'] == 200 and
                                           (validator is None or validator(x[0])),
                                           x[2]['http_status'] == 200, x[2]['fetched_at_utc']))
            body, path, meta = candidates[-1]
            dest = Path(run_dir) / 'raw' / path.parent.name
            _immutable(dest / meta['body'], body)
            _immutable(dest / path.name, path.read_bytes())
            return body, str(dest / path.name), meta
    return None


def _fetch(url, config, run_dir, validator=None):
    cached = _cached(url, config, run_dir, validator)
    if cached and (config.get('offline', True) is not False or
                   cached[2]['http_status'] != 200 or validator is None or validator(cached[0])):
        return cached
    if config.get('offline', True) is not False:
        raise ValueError('offline_cache_miss')
    network = config.get('network', {})
    attempts = max(1, min(5, int(network.get('max_attempts', 3))))
    timeout = max(0.1, min(60, float(network.get('timeout', 20))))
    for attempt in range(attempts):
        error, response_headers = '', {}
        try:
            with urlopen(Request(url, headers={'User-Agent': 'litmine/1 public acquisition'}),
                         timeout=timeout) as response:
                status, body = response.status, response.read()
                total = getattr(response, 'headers', {}).get('x-total-results')
                if total is not None:
                    response_headers['x-total-results'] = str(total)
        except HTTPError as exc:
            with exc:
                status, body = exc.code, exc.read()
        except (URLError, TimeoutError, OSError) as exc:
            status, body, error = 0, b'', type(exc).__name__
        result = _save(url, body, status, run_dir, error=error, attempt=attempt + 1,
                       response_headers=response_headers)
        invalid = status == 200 and validator is not None and not validator(body)
        if (status not in (0, 429, 500, 502, 503, 504) and not invalid) or attempt + 1 == attempts:
            return result
        time.sleep(min(2, 0.25 * 2 ** attempt))


def _local(filename, config, run_dir):
    path = Path(filename)
    if not path.is_absolute():
        path = Path(config.get('_base_dir', '.')) / path
    path = path.resolve()
    url = path.as_uri()
    cached = _cached(url, config, run_dir)
    if cached:
        return cached
    return _save(url, path.read_bytes(), 200, run_dir)


def _doi(value):
    value = str(value or '').strip().lower()
    value = re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)', '', value)
    if value and not re.fullmatch(r'10\.\d{4,9}/\S+', value):
        raise ValueError('invalid_doi')
    return value


def _paper(item, source_ref):
    paper = dict(item)
    pmid = str(item.get('pmid') or '').strip()
    doi = _doi(item.get('doi'))
    pid = str(item.get('paper_id') or '')
    if pid.startswith('PMID:'):
        if pmid and pmid != pid[5:]:
            raise ValueError('identifier_conflict')
        pmid = pid[5:]
    elif pid.startswith('DOI:'):
        if doi and doi != _doi(pid[4:]):
            raise ValueError('identifier_conflict')
        doi = _doi(pid[4:])
    if pmid and not re.fullmatch(r'[1-9]\d*', pmid):
        raise ValueError('invalid_pmid')
    pmcid = str(item.get('pmcid') or '').upper().strip()
    if pmcid and not re.fullmatch(r'PMC[1-9]\d*', pmcid):
        raise ValueError('invalid_pmcid')
    paper.update(paper_id='PMID:' + pmid if pmid else 'DOI:' + doi if doi else '',
                 pmid=pmid, doi=doi, pmcid=pmcid,
                 title=item.get('title') or '', abstract=item.get('abstract', item.get('abstractText')) or '',
                 publication_date=item.get('publication_date', item.get('firstPublicationDate', '')),
                 license=item.get('license', ''), source_ref=source_ref,
                 allow_remote_llm=item.get('allow_remote_llm') is True)
    return paper


def _deduplicate(entries, qc):
    # Union shared identifiers first: a later DOI/PMID bridge can join two records.
    parents = list(range(len(entries)))

    def root(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    aliases = {}
    for i, (paper, record) in enumerate(entries):
        identities = {key: paper.get(key) for key in ('pmid', 'doi', 'pmcid')}
        identities['record_id'] = record['record_id']
        for key, value in identities.items():
            if value:
                alias = (key, value)
                if alias in aliases:
                    parents[root(i)] = root(aliases[alias])
                aliases[alias] = i
    groups = {}
    for i, entry in enumerate(entries):
        groups.setdefault(root(i), []).append(entry)
    papers = []
    for group in groups.values():
        ids = {key: {p[key] for p, _ in group if p.get(key)} for key in ('pmid', 'doi', 'pmcid')}
        if any(len(values) > 1 for values in ids.values()):
            qc.append(_qc('identifier_conflict', record_ids=[r['record_id'] for _, r in group]))
            continue
        merged = dict(group[0][0])
        for paper, _ in group[1:]:
            for key, value in paper.items():
                if key not in merged or merged[key] in ('', None):
                    merged[key] = value
        merged['paper_id'] = ('PMID:' + merged['pmid'] if merged['pmid'] else
                              'DOI:' + merged['doi'] if merged['doi'] else '')
        if not merged['paper_id']:
            qc.append(_qc('missing_identifier', record_ids=[r['record_id'] for _, r in group]))
            continue
        retained = group[0][1]['record_id']
        for _, record in group:
            record['paper_id'] = merged['paper_id']
            record['duplicate_of'] = retained if record['record_id'] != retained else ''
        papers.append(merged)
    return papers


def _valid_search_response(body):
    try:
        data = json.loads(body)
        hits = int(data['hitCount'])
        rows = data['resultList']['result']
        return hits >= 0 and isinstance(rows, list) and all(isinstance(row, dict) for row in rows)
    except (ValueError, KeyError, TypeError, OverflowError):
        return False


def search(config: dict, run_dir: Path) -> dict:
    """Acquire seeds and all bounded cursor pages; retain pre-dedup records."""
    settings = config.get('search', {})
    if settings.get('source', 'europepmc').lower() != 'europepmc':
        raise ValueError('unsupported_search_source')
    limit = int(settings.get('max_records', 1000))
    size = int(settings.get('page_size', 100))
    if limit < 0 or not 1 <= size <= 1000:
        raise ValueError('invalid_search_limits')
    queries = settings.get('queries', [])
    if not isinstance(queries, list) or not all(isinstance(q, str) and q.strip() for q in queries):
        raise ValueError('queries_must_be_nonempty_strings')
    start, end = settings.get('from_year'), settings.get('to_year')
    if any(y is not None and (isinstance(y, bool) or not str(y).isdigit() or not 1 <= int(y) <= 9999)
           for y in (start, end)) or (start is not None and end is not None and int(start) > int(end)):
        raise ValueError('invalid_year_range')
    entries, records, manifests, qc = [], [], [], []
    record_by_id = {}

    def add(item, manifest, source_id, ref):
        rid = 'record:' + _hash(_json([manifest['search_id'], source_id]))
        record = record_by_id.get(rid)
        if record is None:
            record = dict(record_id=rid, search_id=manifest['search_id'], source_identifier=source_id,
                          paper_id='', duplicate_of='', raw_ref=ref)
            record_by_id[rid] = record
            records.append(record)
        try:
            normalized = _paper(item, ref)
            entries.append((normalized, record))
        except (ValueError, TypeError, AttributeError) as exc:
            qc.append(_qc(str(exc), record_id=rid, source_ref=ref))

    def manifest(source, query, ordinal):
        return dict(search_id='search:' + _hash(_json([source, query, start, end, ordinal])),
                    source=source, platform='Europe PMC' if source == 'europepmc' else 'local',
                    source_kind='database' if source == 'europepmc' else 'other', full_query=query,
                    filters={'from_year': start, 'to_year': end} if source == 'europepmc' else {},
                    coverage_period=[start, end] if source == 'europepmc' else None,
                    searched_at=_utc(), sort_order='service_default' if query else 'input_order',
                    pagination=[], reported_hits=None, retrieved_records=0, completion_status='incomplete',
                    raw_response_refs=[], deduplication_version='v1: seeds then query/page order; first record',
                    mode=settings.get('mode', 'exploratory'), max_records=limit)

    seeds = config.get('seeds', [])
    if seeds:
        m = manifest('seeds', '', 0)
        for i, seed in enumerate(seeds):
            url = 'seed:' + _hash(_json(seed))
            _, ref, _ = _cached(url, config, run_dir) or _save(url, _json(seed), 200, run_dir)
            m['raw_response_refs'].append(ref)
            add(seed, m, 'seed:' + str(i), ref)
        m.update(completion_status='complete', reported_hits=len(seeds), retrieved_records=len(seeds))
        manifests.append(m)
    for ordinal, query in enumerate(queries):
        full_query = query
        if start is not None or end is not None:
            full_query = f'({query}) AND FIRST_PDATE:[{int(start or 1):04d}-01-01 TO {int(end or 9999):04d}-12-31]'
        m = manifest('europepmc', full_query, ordinal)
        manifests.append(m)
        cursor, seen, fetched = '*', set(), 0
        initial_records = len(records)
        while fetched < limit:
            if cursor in seen:
                qc.append(_qc('pagination_loop', search_id=m['search_id']))
                break
            seen.add(cursor)
            url = EPMC + 'search?' + urlencode(dict(query=full_query, format='json', resultType='core',
                                                    pageSize=min(size, limit - fetched), cursorMark=cursor))
            try:
                body, ref, meta = _fetch(url, config, run_dir, validator=_valid_search_response)
                m['raw_response_refs'].append(ref)
                if len(m['raw_response_refs']) == 1:
                    m['searched_at'] = meta['fetched_at_utc']
                if meta['http_status'] != 200:
                    raise ValueError('http_' + str(meta['http_status']))
                if not _valid_search_response(body):
                    raise ValueError('invalid_search_response')
                data = json.loads(body)
                hits = int(data['hitCount'])
                rows = data['resultList']['result']
                if (not isinstance(rows, list) or hits < 0 or not all(isinstance(row, dict) for row in rows)
                        or len(rows) > min(size, limit - fetched)):
                    raise ValueError('invalid_search_response')
                if m['reported_hits'] is not None and hits != m['reported_hits']:
                    raise ValueError('hit_count_changed')
                m['reported_hits'] = hits
                m['pagination'].append(dict(cursor=cursor, count=len(rows), source_ref=ref))
                for row in rows[:limit - fetched]:
                    source_id = str(row.get('source', '')) + ':' + str(row.get('id') or row.get('pmid') or row.get('doi') or _hash(_json(row)))
                    add(row, m, source_id, ref)
                fetched += len(rows)
                m['retrieved_records'] = len(records) - initial_records
                if m['retrieved_records'] == hits:
                    m['completion_status'] = 'complete'
                    break
                next_cursor = data.get('nextCursorMark')
                if not rows or not next_cursor or next_cursor == cursor:
                    raise ValueError('pagination_incomplete')
                cursor = next_cursor
            except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
                qc.append(_qc('search_failed', search_id=m['search_id'], detail=type(exc).__name__ + ':' + str(exc)))
                break
        if m['completion_status'] != 'complete':
            qc.append(_qc('search_incomplete', search_id=m['search_id'], retrieved_records=m['retrieved_records']))
    papers = _deduplicate(entries, qc)
    return dict(papers=papers, records=records, searches=manifests, qc=qc)


def _xml_text(body, paper):
    root = ET.fromstring(body)
    for node in root.iter():
        node.tag = node.tag.rsplit('}', 1)[-1]
    if root.tag != 'article':
        raise ValueError('not_full_article')
    article_meta = root.find('./front/article-meta')
    if article_meta is None:
        raise ValueError('missing_article_metadata')
    identifiers = {}
    for node in article_meta.findall('article-id'):
        key = {'pmid': 'pmid', 'doi': 'doi', 'pmc': 'pmcid', 'pmcid': 'pmcid'}.get(node.get('pub-id-type'))
        if key:
            value = ''.join(node.itertext()).strip()
            value = _doi(value) if key == 'doi' else value.upper() if key == 'pmcid' else value
            if key == 'pmcid' and not value.startswith('PMC'):
                value = 'PMC' + value
            if key in identifiers and identifiers[key] != value:
                raise ValueError('article_identifier_conflict')
            identifiers[key] = value
    matched = False
    for key, value in identifiers.items():
        expected = paper.get(key)
        if expected:
            if value != expected:
                raise ValueError('article_identity_mismatch')
            matched = True
    if not matched:
        raise ValueError('article_identity_unverified')
    article_body = root.find('body')
    if article_body is None or not ''.join(article_body.itertext()).strip():
        raise ValueError('missing_article_body')
    parts = []
    title = article_meta.find('./title-group/article-title')
    if title is not None:
        parts.append(''.join(title.itertext()).strip())

    def blocks(node):
        if node.tag in ('p', 'title'):
            text = ''.join(node.itertext()).strip()
            if text:
                parts.append(text)
        else:
            for child in node:
                blocks(child)

    blocks(article_body)
    if not any(n.tag == 'p' and ''.join(n.itertext()).strip() for n in article_body.iter()):
        raise ValueError('missing_article_paragraphs')
    license_node = article_meta.find('./permissions/license')
    license_text = ''.join(license_node.itertext()).strip() if license_node is not None else ''
    return '\n'.join(parts), license_text


def retrieve(paper, config, run_dir) -> dict:
    """Retrieve an explicitly supplied local fulltext or verified OA PMC XML."""
    ref = paper.get('source_ref', '')
    try:
        paper = _paper(paper, ref)
        if not paper['paper_id']:
            raise ValueError('missing_identifier')
        local = paper.get('fulltext_path')
        if local:
            body, ref, meta = _local(local, config, run_dir)
            is_xml = Path(local).suffix.lower() in ('.xml', '.nxml') or body.lstrip().startswith(b'<')
        else:
            if not paper['pmcid']:
                raise ValueError('missing_pmcid')
            if not (paper.get('is_open_access') is True or paper.get('isOpenAccess') == 'Y'):
                raise ValueError('oa_not_confirmed')
            body, ref, meta = _fetch(EPMC + paper['pmcid'] + '/fullTextXML', config, run_dir)
            is_xml = True
        if meta['http_status'] != 200:
            raise ValueError('http_' + str(meta['http_status']))
        text, license_text = _xml_text(body, paper) if is_xml else (body.decode('utf-8'), '')
        if not text.strip():
            raise ValueError('empty_fulltext')
        if text.strip() in (paper['abstract'].strip(), paper['title'].strip()):
            raise ValueError('abstract_or_title_only')
        digest = _hash(text.encode('utf-8'))
        document = dict(document_id='document:' + _hash(_json([paper['paper_id'], PARSER, _hash(body), digest])),
                        paper_id=paper['paper_id'], kind='fulltext', text=text, text_sha256=digest,
                        source_ref=ref, license=paper.get('license') or license_text,
                        allow_remote_llm=paper.get('allow_remote_llm') is True)
        return dict(document=document, reason='retrieved', source_ref=ref)
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as exc:
        return dict(document=None, reason=str(exc) if isinstance(exc, ValueError) else type(exc).__name__, source_ref=ref)


def _entity(entity):
    kind, identifier = entity['kind'], entity['entity_id']
    patterns = {'Gene': r'NCBIGene:[1-9]\d*', 'Species': r'NCBITaxon:[1-9]\d*',
                'CellLine': r'Cellosaurus:CVCL_[A-Z0-9]{4}',
                'Protein': r'UniProt:(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})(?:-[1-9]\d*)?'}
    if kind not in patterns or not re.fullmatch(patterns[kind], identifier):
        raise ValueError('unsupported_or_ambiguous_entity_id')
    if not isinstance(entity.get('name'), str) or not entity['name']:
        raise ValueError('missing_entity_name')
    taxon = entity.get('taxon_id')
    if taxon is not None:
        taxon = str(taxon)
        if taxon.isdigit():
            taxon = 'NCBITaxon:' + taxon
        if not re.fullmatch(r'NCBITaxon:[1-9]\d*', taxon):
            raise ValueError('invalid_taxon_id')
    return dict(entity_id=identifier, kind=kind, name=entity['name'], taxon_id=taxon)


def _validate_annotations(payload, document, paper):
    if payload.get('paper_id') != paper['paper_id']:
        raise ValueError('annotation_identity_mismatch')
    for key in ('document_id', 'text_sha256'):
        if key in payload and payload[key] != document[key]:
            raise ValueError('annotation_document_mismatch')
    entities, mentions, qc, blocked = {}, [], [], set()
    for item in payload['entities']:
        try:
            entity = _entity(item)
            eid = entity['entity_id']
            if eid in entities and entities[eid] != entity:
                blocked.add(eid)
                raise ValueError('conflicting_entity')
            entities[eid] = entity
        except (ValueError, KeyError, TypeError) as exc:
            qc.append(_qc('invalid_entity', detail=str(exc)))
    for item in payload['mentions']:
        try:
            eid, start, end = item['entity_id'], item['start'], item['end']
            quote = item.get('text', item.get('quote'))
            if eid not in entities or eid in blocked:
                raise ValueError('unresolved_entity')
            if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(document['text'])
                    or not isinstance(quote, str) or document['text'][start:end] != quote):
                raise ValueError('span_mismatch')
            mention = dict(entity_id=eid, start=start, end=end, text=quote, document_id=document['document_id'])
            if 'provenance' in item:
                mention['provenance'] = dict(item['provenance'])
            if mention not in mentions:
                mentions.append(mention)
        except (ValueError, KeyError, TypeError) as exc:
            qc.append(_qc('invalid_mention', detail=str(exc)))
    used = {m['entity_id'] for m in mentions}
    return dict(entities=[e for key, e in entities.items() if key in used], mentions=mentions, qc=qc)


def _bioc(payload, document, paper):
    if isinstance(payload, list):
        documents = payload
    elif 'PubTator3' in payload:
        documents = payload['PubTator3']
    elif 'documents' in payload:
        documents = payload['documents']
    else:
        documents = [payload]
    if len(documents) != 1:
        raise ValueError('annotation_identity_ambiguous')
    item = documents[0]
    allowed = {str(v) for v in (paper.get('pmid'), paper.get('pmcid')) if v}
    if paper.get('pmcid'):
        allowed.add(paper['pmcid'].removeprefix('PMC'))
    for passage in item.get('passages', []):
        info = passage.get('infons', {})
        if str(info.get('article-id_pmid')) == str(paper.get('pmid')) and paper.get('pmid'):
            pmc = str(info.get('article-id_pmc', '')).removeprefix('PMC')
            if re.fullmatch(r'[1-9]\d*', pmc):
                allowed.update((pmc, 'PMC' + pmc))
    if str(item.get('id')) not in allowed:
        raise ValueError('annotation_identity_mismatch')
    # Fulltext responses have a numeric PMC id plus explicit PMID/PMCID fields.
    identities = [item]
    for passage in item.get('passages', []):
        info = passage.get('infons', {})
        identities.append({'pmid': info.get('article-id_pmid'), 'pmcid': info.get('article-id_pmc'),
                           'doi': info.get('article-id_doi')})
    for identity in identities:
        for key in ('pmid', 'pmcid', 'doi'):
            value, expected = identity.get(key), paper.get(key)
            if value and expected:
                value = str(value)
                if key == 'pmcid':
                    value = 'PMC' + value.removeprefix('PMC')
                elif key == 'doi':
                    value = _doi(value)
                if value != str(expected):
                    raise ValueError('annotation_identity_mismatch')
    entities, mentions, qc = {}, [], []
    for passage_index, passage in enumerate(item.get('passages', [])):
        annotations = [a for a in passage.get('annotations', [])
                       if a.get('infons', {}).get('type') in ('Gene', 'Protein', 'Species', 'CellLine')]
        if not annotations:
            continue
        text, offset = passage.get('text', ''), passage.get('offset')
        if type(offset) is not int or offset < 0 or not isinstance(text, str) or not text:
            qc.append(_qc('annotation_invalid_passage', passage_index=passage_index))
            continue
        # Length-preserving whitespace normalization keeps Unicode offsets intact.
        normalized = re.sub(r'\s', ' ', document['text'])
        passage_text = re.sub(r'\s', ' ', text)
        anchor = normalized.find(passage_text)
        ambiguous = anchor >= 0 and normalized.find(passage_text, anchor + 1) >= 0
        if ambiguous:
            anchor = -1
        if anchor < 0:
            qc.append(_qc('annotation_passage_ambiguous' if ambiguous else 'annotation_passage_not_found', passage_index=passage_index,
                          source_passage_offset=offset, passage_text_sha256=_hash(text.encode()),
                          annotation_count=len(annotations)))
        for annotation in annotations:
            info = annotation.get('infons', {})
            kind = info.get('type')
            if kind not in ('Gene', 'Protein', 'Species', 'CellLine'):
                continue
            identifier = str(info.get('identifier', ''))
            namespace = {'Gene': 'NCBIGene:', 'Protein': 'UniProt:', 'Species': 'NCBITaxon:',
                         'CellLine': 'Cellosaurus:CVCL_'}[kind]
            if kind == 'CellLine' and re.fullmatch(r'CVCL:[A-Z0-9]{4}', identifier):
                identifier = identifier.replace('CVCL:', 'Cellosaurus:CVCL_')
            eid = identifier if ':' in identifier else namespace + identifier
            try:
                entity = _entity(dict(entity_id=eid, kind=kind, name=annotation.get('text', ''),
                                      taxon_id=info.get('taxon_id')))
                # Different surface forms may legitimately share one canonical ID.
                entities.setdefault(eid, entity)
                locations = annotation.get('locations', [])
                if len(locations) != 1:
                    raise ValueError('discontinuous_annotation')
                loc = locations[0]
                start, length = loc['offset'], loc['length']
                if type(start) is not int or type(length) is not int or not offset <= start < start + length <= offset + len(text):
                    raise ValueError('annotation_outside_passage')
                if text[start - offset:start - offset + length] != annotation['text']:
                    raise ValueError('source_span_mismatch')
                aligned_anchor = anchor
                alignment = 'exact_offset' if anchor == offset else 'exact_unique_passage'
                if anchor >= 0 and document['text'][anchor:anchor + len(text)] != text:
                    alignment = 'whitespace_unique_passage'
                if anchor < 0:
                    # ponytail: sentence fallback only; no fuzzy alignment or alias propagation.
                    span = next((s for s in re.finditer(r'[^.!?\n]+(?:[.!?]|(?=\n|$))', text)
                                 if s.start() <= start - offset < start - offset + length <= s.end()), None)
                    if span is None or len(span.group().split()) < 6:
                        raise ValueError('annotation_sentence_not_found')
                    sentence = re.sub(r'\s', ' ', span.group()).strip()
                    at = normalized.find(sentence)
                    if at < 0 or normalized.find(sentence, at + 1) >= 0:
                        raise ValueError('annotation_sentence_not_unique')
                    aligned_anchor = at - span.start() - len(span.group()) + len(span.group().lstrip())
                    alignment = 'whitespace_unique_sentence'
                aligned_start = aligned_anchor + start - offset
                if document['text'][aligned_start:aligned_start + length] != annotation['text']:
                    raise ValueError('aligned_mention_mismatch')
                provenance = dict(source_start=start, source_end=start + length,
                                  source_passage_offset=offset, aligned_passage_offset=aligned_anchor,
                                  passage_index=passage_index, passage_text_sha256=_hash(text.encode()),
                                  alignment=alignment)
                mentions.append(dict(entity_id=eid, start=aligned_start, end=aligned_start + length,
                                     text=annotation['text'], provenance=provenance))
            except (ValueError, KeyError, TypeError) as exc:
                qc.append(_qc('invalid_pubtator_annotation', detail=str(exc)))
    return dict(paper_id=paper['paper_id'], entities=list(entities.values()), mentions=mentions), qc


def _protein_url(gene_id):
    return UNIPROT + '?' + urlencode({'query': f'(xref:geneid-{gene_id}) AND (reviewed:true)',
                                     'format': 'json', 'size': 2})


def _protein_lookup(url, config, run_dir):
    cached = _cached(url, config, run_dir)
    if cached:
        return cached
    if config.get('offline', True) is not False:
        raise ValueError('offline_cache_miss')
    limit = config.get('max_protein_lookups', 20)
    if type(limit) is not int or limit < 0:
        raise ValueError('invalid_max_protein_lookups')
    ledger = Path(run_dir) / 'raw' / 'protein_lookups'
    ledger.mkdir(parents=True, exist_ok=True)
    # Exclusive slots enforce the run budget across annotate calls and processes.
    for index in range(limit):
        try:
            with (ledger / f'{index:06d}.json').open('xb') as handle:
                handle.write(_json(dict(url=url, started_at_utc=_utc())))
            break
        except FileExistsError:
            continue
    else:
        raise ValueError('protein_lookup_budget_exhausted')
    bounded = dict(config, network={**config.get('network', {}), 'max_attempts': 1})
    return _fetch(url, bounded, run_dir)


def _reviewed_protein(body, meta, gene):
    rows = json.loads(body)['results']
    total = meta.get('response_headers', {}).get('x-total-results')
    if not isinstance(rows, list) or total is None or int(total) != len(rows):
        raise ValueError('protein_results_incomplete')
    candidates = {}
    gene_id = gene['entity_id'].removeprefix('NCBIGene:')
    for row in rows:
        if row.get('entryType') != 'UniProtKB reviewed (Swiss-Prot)':
            raise ValueError('protein_not_reviewed')
        xrefs = {str(x['id']) for x in row.get('uniProtKBCrossReferences', [])
                 if x.get('database') == 'GeneID'}
        if gene_id not in xrefs:
            raise ValueError('protein_geneid_mismatch')
        taxon = row['organism']['taxonId']
        if type(taxon) is not int or taxon <= 0:
            raise ValueError('protein_taxon_missing')
        protein = _entity(dict(entity_id='UniProt:' + row['primaryAccession'], kind='Protein',
                               name=row['proteinDescription']['recommendedName']['fullName']['value'],
                               taxon_id=taxon))
        if gene.get('taxon_id') and gene['taxon_id'] != protein['taxon_id']:
            raise ValueError('protein_taxon_conflict')
        eid = protein['entity_id']
        if eid in candidates and candidates[eid] != protein:
            raise ValueError('protein_record_conflict')
        candidates[eid] = protein
    if len(candidates) != 1:
        raise ValueError('protein_mapping_ambiguous' if candidates else 'protein_mapping_missing')
    return next(iter(candidates.values()))


def _add_protein_candidates(result, paper, config, run_dir):
    entities = {e['entity_id']: e for e in result['entities']}
    original_mentions = list(result['mentions'])
    for gene in sorted(result['entities'], key=lambda e: e['entity_id']):
        if gene['kind'] != 'Gene':
            continue
        ref = ''
        try:
            url = _protein_url(gene['entity_id'].removeprefix('NCBIGene:'))
            body, ref, meta = _protein_lookup(url, config, run_dir)
            if meta['http_status'] != 200:
                raise ValueError('http_' + str(meta['http_status']))
            protein = _reviewed_protein(body, meta, gene)
            old = entities.get(protein['entity_id'])
            if old and (old['kind'] != protein['kind'] or old.get('taxon_id') != protein['taxon_id']):
                raise ValueError('protein_entity_conflict')
            if not old:
                entities[protein['entity_id']] = protein
                result['entities'].append(protein)
            for mention in original_mentions:
                if mention['entity_id'] != gene['entity_id']:
                    continue
                # The shared literal span is a candidate, not a protein assertion.
                provenance = dict(mention.get('provenance', {}), protein_normalization={
                    'gene_entity_id': gene['entity_id'], 'source_ref': ref,
                    'method': 'unique_reviewed_uniprot_geneid', 'candidate_only': True})
                candidate = dict(mention, entity_id=protein['entity_id'], provenance=provenance)
                if not any(m['entity_id'] == candidate['entity_id'] and m['start'] == candidate['start']
                           and m['end'] == candidate['end'] for m in result['mentions']):
                    result['mentions'].append(candidate)
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            result['qc'].append(_qc('protein_normalization_unavailable', paper_id=paper['paper_id'],
                                     entity_id=gene['entity_id'], source_ref=ref, detail=str(exc)))
    return result


def annotate(document, paper, config, run_dir) -> dict:
    """Validate local or optional public annotations against this exact text."""
    ref = ''
    try:
        if document['paper_id'] != paper['paper_id'] or _hash(document['text'].encode()) != document['text_sha256']:
            raise ValueError('document_identity_or_hash_mismatch')
        filename = config.get('annotations', {}).get(paper['paper_id'])
        extra_qc = []
        if filename:
            body, ref, _ = _local(filename, config, run_dir)
            payload = json.loads(body)
        elif config.get('pubtator') is True:
            identifier = str(paper.get('pmid') or '')
            if not re.fullmatch(r'[1-9]\d*', identifier):
                raise ValueError('missing_or_invalid_pubtator_pmid')
            params = {'pmids': identifier, 'full': 'true' if document.get('kind') == 'fulltext' else 'false'}
            body, ref, meta = _fetch(PUBTATOR + '?' + urlencode(params), config, run_dir)
            if meta['http_status'] != 200:
                raise ValueError('http_' + str(meta['http_status']))
            payload, extra_qc = _bioc(json.loads(body), document, paper)
        else:
            raise ValueError('annotations_not_configured')
        result = _validate_annotations(payload, document, paper)
        result['qc'].extend(extra_qc)
        if not result['mentions']:
            result['qc'].append(_qc('annotations_missing'))
        for qc in result['qc']:
            qc.update(paper_id=paper['paper_id'], source_ref=ref)
        for mention in result['mentions']:
            mention['source_ref'] = ref
        if config.get('protein_normalization') is True:
            _add_protein_candidates(result, paper, config, run_dir)
        return result
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        return dict(entities=[], mentions=[], qc=[_qc('annotations_unavailable', detail=str(exc),
                    paper_id=paper.get('paper_id', ''), source_ref=ref)])
