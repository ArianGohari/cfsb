"""Read back real Task4 artifacts; write a new verification receipt, never labels.

Run from text_mining: uv run python tests/verify_task4_run.py RUN_DIR
"""
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import pyarrow.parquet as pq
import real_ladybug as lbug


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root):
    review = json.loads((root / 'review.json').read_text())
    receipt = json.loads((root / 'graph_export.json').read_text())
    freeze = json.loads((root / 'freeze.json').read_text())
    assert review['qc']['llm_calls'] == 0
    assert review['qc']['processing_mode'] == 'rules'
    assert not (root / 'llm').exists()
    assert receipt['scope'] == 'reported_assertions'
    assert all(sha(Path(p)) == expected for p, expected in freeze['corpus_sha256'].items())
    assert all(sha(Path(p)) == expected for p, expected in freeze['code_sha256'].items())
    assert all(sha(root / p) == expected for p, expected in receipt['output_hashes'].items())
    assert sha(root / 'review.json') == receipt['review_sha256']
    for table, count in receipt['tables'].items():
        assert pq.read_table(root / (table + '.parquet')).num_rows == count
    docs = {d['document_id']: d for d in review['documents']}
    relations = {r['relation_id']: r for r in review['relations']}
    for ev in review['evidence']:
        doc = docs[ev['document_id']]
        assert doc['text'][ev['start']:ev['end']] == ev['quote']
        for role in ('subject', 'object'):
            assert ev['start'] <= ev[role + '_start'] < ev[role + '_end'] <= ev['end']
        if ev['validation_status'] == 'assertion_pass':
            assert ev['attribution'] == 'unknown'
    selected = [ev for ev in review['evidence'] if docs[ev['document_id']]['paper_id'] == 'PMID:33898942']
    assert selected
    assert any(relations[e['relation_id']]['object_id'] == 'Cellosaurus:CVCL_0025' for e in selected)
    assert all(e['attribution'] == 'unknown' for e in selected)
    assert all(relations[e['relation_id']][k] is None for e in selected
               for k in ('species_id', 'cell_line_id', 'condition', 'compartment'))
    db = lbug.Database(str(root / 'graph.lbug'), read_only=True, buffer_pool_size=64 * 1024 * 1024)
    counts = {}
    try:
        conn = lbug.Connection(db)
        try:
            for name in ('Paper', 'Document', 'Entity', 'Relation', 'Evidence'):
                result = conn.execute(f'MATCH (n:{name}) RETURN count(n)')
                counts[name] = result.get_next()[0]
                result.close()
                assert counts[name] == receipt['primary_counts'][name]
            result = conn.execute('MATCH (e:Entity)-[:SUBJECT_OF]->(r:Relation)-[:OBJECT]->(o:Entity) RETURN count(r)')
            linked = result.get_next()[0]
            result.close()
            assert linked == counts['Relation'] > 0
        finally:
            conn.close()
    finally:
        db.close()
    svg = ET.parse(root / 'graph.svg')
    svg_counts = {kind: sum(node.get('class') == kind for node in svg.getroot().iter()) for kind in ('node', 'edge')}
    assert svg_counts['node'] > 0 and svg_counts['edge'] > 0
    heldout = set(freeze['heldout_paper_ids'])
    evidence_papers = {docs[e['document_id']]['paper_id'] for e in review['evidence']
                       if e['validation_status'] in ('auto_pass', 'assertion_pass')}
    coverage = review['qc']['annotation_coverage']
    result = dict(status='passed', graph_database_counts=counts, svg_counts=svg_counts,
        corpus_unchanged=True, frozen_code_unchanged=True, llm_calls=0,
        fulltext_coverage=review['prisma_counts']['retrieval'],
        screening=review['prisma_counts']['fulltext_eligibility'],
        annotation_documents=len(coverage), annotation_mentions=sum(a['mentions'] for a in coverage),
        sentences=sum(a['sentences'] for a in coverage),
        sentences_with_two_mentions=sum(a['sentences_with_two_mentions'] for a in coverage),
        assertion_sentences=len({(e['document_id'], e['start'], e['end']) for e in review['evidence']}),
        evidence_status_counts=review['qc']['evidence_status_counts'],
        papers_with_assertions=len(evidence_papers), heldout_papers=len(heldout),
        heldout_papers_with_assertions=len(heldout & evidence_papers),
        heldout_precision=None, heldout_recall=None,
        precision_note='No reference labels used. Zero heldout predictions means precision is undefined; coverage is not recall.',
        review_sha256=sha(root / 'review.json'), verifier_sha256=sha(Path(__file__)))
    with (root / 'verification.json').open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    verify(Path(sys.argv[1]))
