"""Validated review exports. Requires pyarrow, real-ladybug (import real_ladybug), dot.

export() writes five complete Parquet tables, a primary-only graph.lbug, graph.dot,
graph.svg and graph_export.json. Rebuild by exporting the same immutable review.
Only files owned by an intact graph_export.json may be replaced; unrelated files
are untouched. Staging and rollback prevent failed builds from publishing output.
Replacement is atomic per file, not a concurrent-reader transaction across files.
manifest.config.graph.max_nodes limits rendering (default 500; null disables it).
It never truncates data. CLI/packaging are owned by the parent pipeline.
"""
from datetime import date
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from .engine import ATTRIBUTIONS, PREDICATES, argument_types
from .llm import IntegrityError, digest
from .sources import _entity

# name, fields: ? means nullable; offsets are Unicode codepoints, not bytes.
FIELDS = {
    'papers': ('Paper', 'paper_id pmid? doi? title publication_date? source_ref'),
    'documents': ('Document', 'document_id paper_id kind text text_sha256 source_ref'),
    'entities': ('Entity', 'entity_id kind name taxon_id?'),
    'relations': ('Relation', 'relation_id subject_id predicate object_id species_id? cell_line_id? condition? compartment?'),
    'evidence': ('Evidence', 'evidence_id relation_id document_id start end quote subject_start subject_end object_start object_end section? source_locator? stance attribution experimental_method? validation_status extractor_id score?'),
}
OFFSETS = {'start', 'end', 'subject_start', 'subject_end', 'object_start', 'object_end'}
EDGES = (
    ('HAS_DOCUMENT', 'papers', 'documents', 'paper_id', True),
    ('HAS_EVIDENCE', 'documents', 'evidence', 'document_id', True),
    ('ASSESSES', 'evidence', 'relations', 'relation_id', False),
    ('SUBJECT_OF', 'entities', 'relations', 'subject_id', True),
    ('OBJECT', 'relations', 'entities', 'object_id', False),
)
COLORS = dict(zip(FIELDS, ('#b3cde3', '#ccebc5', '#fed9a6', '#decbe4', '#ffffcc')))
NOTICE = 'Automatically extracted evidence; auto_pass is not biological truth. Scientific quality: not evaluated.'
RECEIPT = 'graph_export.json'
OUTPUTS = tuple(t + '.parquet' for t in FIELDS) + ('graph.lbug', 'graph.dot', 'graph.svg')


def schemas():
    """Explicit Arrow types also apply to empty tables and all-null columns."""
    import pyarrow as pa
    return {table: pa.schema([
        pa.field(field.rstrip('?'), pa.int64() if field.rstrip('?') in OFFSETS else
                 pa.float64() if field == 'score?' else pa.date32() if field == 'publication_date?' else pa.string(),
                 nullable=field.endswith('?'))
        for field in fields.split()]) for table, (_, fields) in FIELDS.items()}


def _require(condition, reason):
    if not condition:
        raise IntegrityError(reason)


def _hashes(root, hashes):
    _require(isinstance(hashes, dict), 'invalid_hash_manifest')
    for name, expected in hashes.items():
        path = root / name
        _require(not Path(name).is_absolute() and path.resolve().is_relative_to(root.resolve()), 'unsafe_manifest_path')
        _require(path.is_file() and digest(path.read_bytes()) == expected, 'input_hash_mismatch:' + name)


def _load(review_path):
    review = json.loads(review_path.read_bytes())
    manifest = review['manifest']
    _require(manifest['schema_version'] == 1, 'unsupported_schema_version')
    _hashes(review_path.parent, manifest['input_hashes'])
    _hashes(review_path.parent, manifest.get('output_hashes', {}))
    authoritative = review_path.parent / 'manifest.json'
    if authoritative.exists():
        outer = json.loads(authoritative.read_bytes())
        _require(outer.get('run_id') == manifest.get('run_id'), 'manifest_run_mismatch')
        _require(outer['output_hashes'].get(review_path.name) == digest(review_path.read_bytes()), 'review_hash_mismatch')
        _require(outer['input_hashes'] == manifest['input_hashes'], 'manifest_input_mismatch')
        _hashes(review_path.parent, outer['input_hashes'])
    return review


def _validated(review):
    tables, maps = {}, {}
    for table, schema in schemas().items():
        rows = []
        _require(isinstance(review[table], list), 'invalid_table:' + table)
        for original in review[table]:
            row = {}
            for field in schema:
                value = original.get(field.name)
                if field.name == 'publication_date' and value == '':
                    value = None  # sources uses an empty string for unknown dates.
                if value is None:
                    _require(field.nullable, 'missing_field:' + field.name)
                elif field.name in OFFSETS:
                    _require(type(value) is int and 0 <= value < 2**63, 'invalid_offset')
                elif field.name == 'score':
                    _require(type(value) in (float, int) and math.isfinite(value), 'invalid_score')
                else:
                    _require(isinstance(value, str), 'invalid_string:' + field.name)
                    if field.name == 'publication_date':
                        _require(bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}', value)), 'invalid_publication_date')
                        value = date.fromisoformat(value)
                row[field.name] = value
            _require(bool(row[schema.names[0]]), 'empty_primary_key')
            rows.append(row)
        key = schema.names[0]
        maps[table] = {r[key]: r for r in rows}
        _require(len(maps[table]) == len(rows), 'duplicate_primary_key:' + table)
        tables[table] = sorted(rows, key=lambda r: r[key])

    for doc in tables['documents']:
        _require(doc['paper_id'] in maps['papers'], 'document_foreign_key')
        _require(doc['kind'] in ('abstract', 'fulltext'), 'document_kind')
        _require(digest(doc['text'].encode()) == doc['text_sha256'], 'document_hash_mismatch')
    for entity in tables['entities']:
        if entity['kind'] == 'CellLine':
            _require(bool(re.fullmatch(r'Cellosaurus:CVCL_[A-Z0-9]{4}', entity['entity_id'])), 'invalid_cell_line_id')
        else:
            _entity(entity)
        _require(entity['name'].strip(), 'empty_entity_name')
        _require(entity['taxon_id'] is None or bool(re.fullmatch(r'NCBITaxon:[1-9]\d*', entity['taxon_id'])), 'invalid_taxon_id')
    for rel in tables['relations']:
        _require(rel['subject_id'] in maps['entities'] and rel['object_id'] in maps['entities'], 'relation_foreign_key')
        sk, ok = (maps['entities'][rel[k]]['kind'] for k in ('subject_id', 'object_id'))
        _require(rel['predicate'] in PREDICATES, 'invalid_predicate')
        valid = argument_types(rel['predicate'], sk, ok)
        _require(valid, 'invalid_argument_types')
        _require(rel['predicate'] != 'BINDS' or rel['subject_id'] <= rel['object_id'], 'noncanonical_binds')
        for key, kind in (('species_id', 'Species'), ('cell_line_id', 'CellLine')):
            _require(rel[key] is None or maps['entities'].get(rel[key], {}).get('kind') == kind, 'context_foreign_key:' + key)
        _require(rel['relation_id'] == 'relation:' + digest({k: v for k, v in rel.items() if k != 'relation_id'}), 'relation_id_mismatch')
    for ev in tables['evidence']:
        _require(ev['document_id'] in maps['documents'] and ev['relation_id'] in maps['relations'], 'evidence_foreign_key')
        doc, rel = maps['documents'][ev['document_id']], maps['relations'][ev['relation_id']]
        _require(0 <= ev['start'] < ev['end'] <= len(doc['text']) and doc['text'][ev['start']:ev['end']] == ev['quote'], 'evidence_span')
        for role in ('subject', 'object'):
            _require(ev['start'] <= ev[role + '_start'] < ev[role + '_end'] <= ev['end'], 'argument_span')
        _require(ev['validation_status'] in ('auto_pass', 'assertion_pass', 'uncertain', 'rejected'), 'invalid_validation_status')
        if ev['validation_status'] == 'assertion_pass':
            _require(ev['attribution'] == 'unknown', 'assertion_pass_requires_unknown_attribution')
        _require(ev['stance'] in ('supports', 'inconclusive') and ev['attribution'] in ATTRIBUTIONS, 'invalid_evidence_enums')
        _require(bool(ev['extractor_id']), 'missing_extractor')
        for value in (ev['experimental_method'], rel['condition'], rel['compartment']):
            _require(value is None or bool(value) and value in ev['quote'], 'unproven_context')
        if ev['validation_status'] in ('auto_pass', 'assertion_pass'):
            taxons = {maps['entities'][rel[k]]['taxon_id'] for k in ('subject_id', 'object_id')} - {None}
            _require(len(taxons) <= 1 and (not rel['species_id'] or not taxons or rel['species_id'] in taxons), 'inconsistent_species')
            _require(ev['stance'] == 'supports', 'inconclusive_auto_pass')
        _require(ev['evidence_id'] == 'evidence:' + digest({k: v for k, v in ev.items() if k != 'evidence_id'}), 'evidence_id_mismatch')

    events = review['screening']
    by_id = {e['event_id']: e for e in events}
    active = review['manifest']['active_event_ids']
    _require(len(by_id) == len(events) and len(set(active)) == len(active) and set(active) <= by_id.keys(), 'invalid_active_events')
    seen, included_docs = set(), set()
    for eid in active:
        event = by_id[eid]
        pid, stage = event['paper_id'], event['stage']
        _require(pid in maps['papers'] and (pid, stage) not in seen, 'screening_foreign_key_or_duplicate')
        seen.add((pid, stage))
        _require(stage in ('title_abstract', 'retrieval', 'fulltext_eligibility'), 'invalid_screening_stage')
        if event.get('document_id') is not None:
            doc = maps['documents'].get(event['document_id'])
            _require(doc is not None and doc['paper_id'] == pid and event['input_hash'] == doc['text_sha256'], 'screening_input_hash')
        else:
            original = next(p for p in review['papers'] if p['paper_id'] == pid)
            # Retrieval happens after engine attaches the abstract-stage decision.
            source = {k: v for k, v in original.items() if k != 'final_decision'}
            if stage == 'retrieval':
                source['final_decision'] = 'unclear'
            _require(event['input_hash'] == digest(source), 'screening_input_hash')
        if stage == 'fulltext_eligibility':
            _require(event['decision'] in ('include', 'exclude', 'unclear', 'not_processed'), 'invalid_fulltext_decision')
            if event['decision'] == 'include':
                doc = maps['documents'].get(event.get('document_id'))
                _require(doc is not None and doc['kind'] == 'fulltext', 'inclusion_requires_fulltext')
                quote = event.get('evidence_quote')
                _require(isinstance(quote, str) and quote and quote in doc['text'], 'screening_quote')
                included_docs.add(doc['document_id'])

    primary = {}
    primary['documents'] = [d for d in tables['documents'] if d['document_id'] in included_docs]
    pids = {d['paper_id'] for d in primary['documents']}
    primary['papers'] = [p for p in tables['papers'] if p['paper_id'] in pids]
    scope = review['manifest'].get('config', {}).get('graph', {}).get('scope', 'attributed')
    _require(scope in ('attributed', 'reported_assertions', 'own_experiment'), 'invalid_graph_scope')
    statuses = ('auto_pass', 'assertion_pass') if scope == 'reported_assertions' else ('auto_pass',)
    primary['evidence'] = [e for e in tables['evidence'] if e['validation_status'] in statuses
                           and e['document_id'] in included_docs
                           and (scope != 'own_experiment' or e['attribution'] == 'own_experiment')]
    rids = {e['relation_id'] for e in primary['evidence']}
    primary['relations'] = [r for r in tables['relations'] if r['relation_id'] in rids]
    entity_ids = {r[k] for r in primary['relations'] for k in ('subject_id', 'object_id', 'species_id', 'cell_line_id')} - {None}
    primary['entities'] = [e for e in tables['entities'] if e['entity_id'] in entity_ids]
    return tables, primary


def _edges(primary):
    for name, source, target, foreign_key, reverse in EDGES:
        rows = primary[target if reverse else source]
        key = FIELDS[target if reverse else source][1].split()[0]
        for row in rows:
            yield name, source, target, row[foreign_key] if reverse else row[key], row[key] if reverse else row[foreign_key]


def _database(path, primary):
    import real_ladybug as lbug
    db = lbug.Database(path, buffer_pool_size=64 * 1024 * 1024, max_num_threads=2)
    try:
        connection = lbug.Connection(db)
        try:
            def execute(query, params=None):
                result = connection.execute(query, params or {})
                try:
                    return result.get_next() if result.has_next() else None
                finally:
                    result.close()
            for table, (label, _) in FIELDS.items():
                schema = schemas()[table]
                key = schema.names[0]
                columns = ', '.join('`' + f.name + '` ' + ('INT64' if f.name in OFFSETS else 'DOUBLE' if f.name == 'score' else 'DATE' if f.name == 'publication_date' else 'STRING') for f in schema)
                execute(f'CREATE NODE TABLE {label}({columns}, PRIMARY KEY (`{key}`))')
                for row in primary[table]:
                    props = ', '.join(f'`{k}`: $v{i}' for i, k in enumerate(row))
                    execute(f'CREATE (n:{label} {{{props}}})', {f'v{i}': v for i, v in enumerate(row.values())})
            for name, source, target, _, _ in EDGES:
                execute(f'CREATE REL TABLE {name}(FROM {FIELDS[source][0]} TO {FIELDS[target][0]})')
            edges = list(_edges(primary))
            for name, source, target, sid, tid in edges:
                slabel, skey = FIELDS[source][0], FIELDS[source][1].split()[0]
                tlabel, tkey = FIELDS[target][0], FIELDS[target][1].split()[0]
                execute(f'MATCH (s:{slabel}), (t:{tlabel}) WHERE s.`{skey}` = $s AND t.`{tkey}` = $t CREATE (s)-[:{name}]->(t)', {'s': sid, 't': tid})
            counts = {}
            for table, (label, _) in FIELDS.items():
                counts[label] = execute(f'MATCH (n:{label}) RETURN count(n)')[0]
                _require(counts[label] == len(primary[table]), 'database_node_count')
            for name, *_ in EDGES:
                counts[name] = execute(f'MATCH ()-[e:{name}]->() RETURN count(e)')[0]
                _require(counts[name] == sum(e[0] == name for e in edges), 'database_edge_count')
            execute('CHECKPOINT')
            return counts
        finally:
            connection.close()
    finally:
        db.close()


def _quoted(value):
    # Only quoted DOT strings, never HTML labels; neutralize Graphviz escapes too.
    value = ''.join(c if ord(c) >= 32 and ord(c) != 127 else ' ' for c in str(value))
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'


def _dot(primary, notice):
    lines = ['digraph KnowledgeGraph {', 'graph [rankdir=LR, label=' + _quoted(notice) + ', labelloc=t, fontname="Helvetica-Bold", fontsize=18];',
             'node [shape=box, style=filled, fontname="Helvetica"];']
    ids = {}
    documents = {d['document_id']: d for d in primary['documents']}
    papers = {p['paper_id']: p for p in primary['papers']}
    for table, (label, fields) in FIELDS.items():
        for row in primary[table]:
            key = row[fields.split()[0]]
            node = 'n' + str(len(ids))
            ids[table, key] = node
            text = row.get('title', row.get('name', row.get('predicate', row.get('quote', row.get('kind', key)))))
            citation = {}
            if table == 'evidence':
                text = row['validation_status'] + ' / ' + row['attribution'] + ': ' + text
                doc = documents[row['document_id']]
                citation = dict(paper=papers[doc['paper_id']], source_ref=doc['source_ref'])
            tooltip = json.dumps(dict(row, **citation), ensure_ascii=False, sort_keys=True, default=str)
            lines.append(f'{node} [label={_quoted(label + ": " + text[:100])}, fillcolor="{COLORS[table]}", tooltip={_quoted(tooltip)}];')
    for name, source, target, sid, tid in _edges(primary):
        lines.append(f'{ids[source, sid]} -> {ids[target, tid]} [label="{name}"];')
    lines.append('subgraph cluster_legend { label="Node types";')
    for table, (label, _) in FIELDS.items():
        lines.append(f'legend_{table} [label="{label}", fillcolor="{COLORS[table]}"];')
    lines.extend(['}', '}'])
    return '\n'.join(lines) + '\n'


def _svg(path):
    root = ET.parse(path).getroot()
    _require(root.tag == '{http://www.w3.org/2000/svg}svg', 'invalid_svg')
    for node in root.iter():
        _require(node.tag.rsplit('}', 1)[-1] not in ('script', 'foreignObject', 'image', 'use'), 'active_svg_content')
        _require(not any(k.rsplit('}', 1)[-1].lower().startswith('on') or k.rsplit('}', 1)[-1] in ('href', 'src') for k in node.attrib), 'external_svg_content')


def _ownership(output_dir):
    receipt = output_dir / RECEIPT
    names = OUTPUTS + (RECEIPT,)
    _require(not output_dir.is_symlink(), 'symlink_output_directory')
    for name in names:
        path = output_dir / name
        _require(not path.is_symlink() and (not path.exists() or path.is_file()), 'unsafe_output:' + name)
    if receipt.exists():
        previous = json.loads(receipt.read_bytes())
        _require(previous.get('format') == 'litmine-graph-v1' and set(previous.get('output_hashes', {})) == set(OUTPUTS), 'unowned_output_directory')
        _hashes(output_dir, previous['output_hashes'])
    else:
        _require(not any((output_dir / name).exists() for name in OUTPUTS), 'unowned_output_files')


def export(review_path: Path, output_dir: Path) -> dict:
    """Validate, stage, verify, then replace only owned files; return export receipt."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    review_path, output_dir = Path(review_path), Path(output_dir)
    review = _load(review_path)
    tables, primary = _validated(review)
    settings = review['manifest'].get('config', {}).get('graph', {})
    limit = settings.get('max_nodes', 500)
    _require(limit is None or type(limit) is int and limit > 0, 'invalid_graph_max_nodes')
    nodes = sum(map(len, primary.values()))
    synthetic = bool(review.get('qc', {}).get('synthetic_demo') or review['manifest'].get('mode') == 'synthetic_demo')
    notice = ('SYNTHETIC DEMO: fixture data, not biological evidence. ' if synthetic else '') + NOTICE
    scope = settings.get('scope', 'attributed')
    notice += ' Scope: ' + scope + '. Unknown context/attribution is not confirmed.'
    if nodes == 0:
        notice += ' No primary graph nodes; no biological proof.'
    _require(limit is None or nodes <= limit, f'graph_max_nodes_exceeded:{nodes}>{limit}; set manifest.config.graph.max_nodes explicitly (null disables limit)')
    _ownership(output_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.litmine-graph-', dir=output_dir.parent) as temporary:
        stage = Path(temporary)
        for table, schema in schemas().items():
            pq.write_table(pa.Table.from_pylist(tables[table], schema=schema), stage / (table + '.parquet'))
        counts = _database(stage / 'graph.lbug', primary)
        (stage / 'graph.dot').write_text(_dot(primary, notice), encoding='utf-8')
        # Rendering is the last artifact-producing step. No shell or remote assets.
        subprocess.run(['dot', '-Tsvg', str(stage / 'graph.dot'), '-o', str(stage / 'graph.svg')], check=True, capture_output=True)
        _svg(stage / 'graph.svg')
        result = dict(format='litmine-graph-v1', review_sha256=digest(review_path.read_bytes()),
                      tables={t: len(rows) for t, rows in tables.items()}, primary_counts=counts,
                      rendering=dict(nodes=nodes, max_nodes=limit, complete=True), synthetic_demo=synthetic,
                      scope=scope, scientific_disclaimer=notice,
                      dependencies={name: importlib.metadata.version(name) for name in ('pyarrow', 'real-ladybug')},
                      output_hashes={name: digest((stage / name).read_bytes()) for name in OUTPUTS})
        (stage / RECEIPT).write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        _ownership(output_dir)  # Refuse a changed output while the build was running.
        output_dir.mkdir(exist_ok=True)
        backup = stage / 'backup'
        backup.mkdir()
        saved, published = [], []
        try:
            for name in OUTPUTS + (RECEIPT,):
                target = output_dir / name
                if target.exists():
                    os.replace(target, backup / name)
                    saved.append(name)
                os.replace(stage / name, target)
                published.append(name)
        except BaseException:
            for name in reversed(published):
                (output_dir / name).unlink()
            for name in saved:
                os.replace(backup / name, output_dir / name)
            raise
    return result
