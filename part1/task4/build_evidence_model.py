"""Build the bounded Task 4 literature register and observation graph offline."""

import csv
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
AUDIT = ROOT / 'audits' / 'source-audit-20260923' / 'audit.json'
OUT = ROOT / 'model'


def write_tsv(path, rows, fields):
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def main():
    audit = json.loads(AUDIT.read_text())
    register = audit['candidate_register']
    decisions = {
        'PMID:33898942': ('included_case_study', 'Vergleichende quantitative Wirtsproteomik mit Caco-2 und weiterer humaner Zelllinie; Volltext und Supplemente lokal vorhanden.'),
        'DOI:10.1101/2020.08.28.271684': ('related_preprint_not_independent', 'Gleiche Autorengruppe und sehr ähnlicher Abstract wie Saccon 2021; als Vorversion der Fallstudie behandelt, nicht als unabhängige Replikation.'),
        'PMID:32591346': ('background_only', 'Caco-2 wird als Referenzproteom erwähnt; der Artikel liefert keinen getrennt nachgerechneten Caco-2-Kontrast für diese Arbeit.'),
    }
    rows = []
    for item in register:
        paper_id = item['paper_id']
        if paper_id in decisions:
            decision, reason = decisions[paper_id]
        else:
            decision = 'not_selected_on_title_abstract'
            reason = ('Titel und Abstract belegen keinen für diese Auswahl geeigneten '
                      'vergleichenden Caco-2-Gesamtproteomkontrast; keine fachliche '
                      'Volltextbewertung oder Qualitätsaussage.')
        rows.append({
            'paper_id': paper_id, 'source_identifier': '', 'title': item['title'], 'doi': item['doi'],
            'search_occurrences': item['search_occurrences'],
            'retrieval_status': item['retrieval_status'],
            'screening_level': 'title_abstract_and_local_fulltext' if paper_id == 'PMID:33898942' else 'title_abstract',
            'decision': decision, 'reason': reason,
        })
    for item in audit['unassigned_records']:
        rows.append({
            'paper_id': '', 'source_identifier': item['source_identifier'],
            'title': '', 'doi': '', 'search_occurrences': 1,
            'retrieval_status': 'not_attempted_by_pipeline',
            'screening_level': 'none', 'decision': 'not_processed_missing_pipeline_id',
            'reason': 'Quellkennung vorhanden, interne paper_id fehlt; keine fachliche Entscheidung.',
        })
    if len(rows) != 52 or sum(x['search_occurrences'] for x in rows) != 54:
        raise ValueError('Candidate register count mismatch')
    if sum(x['decision'] == 'included_case_study' for x in rows) != 1:
        raise ValueError('Case study count mismatch')

    nodes = [
        {'id': 'R-HSA-913531', 'label': 'Humanes Interferon-Signalmodul', 'kind': 'curated_pathway', 'taxon': 9606},
        {'id': 'T4:CACO2_PROTEOME', 'label': 'Caco-2-Proteomikkontrast', 'kind': 'published_observation', 'taxon': 9606},
        {'id': 'T4:CALU3_PROTEOME', 'label': 'Calu-3-Proteomikkontrast', 'kind': 'published_observation', 'taxon': 9606},
        {'id': 'T4:CACO2_TRANSCRIPT', 'label': 'Caco-2-Transkriptmessung', 'kind': 'published_observation', 'taxon': 9606},
        {'id': 'T4:IFN_FUNCTIONAL_GROUP', 'label': 'IFN-bezogene Funktionsgruppe', 'kind': 'functional_group', 'taxon': 9606},
    ]
    source_article = 'https://doi.org/10.1016/j.isci.2021.102420'
    edges = [
        {'id': 'T4E01', 'source': 'R-HSA-913531', 'target': 'T4:IFN_FUNCTIONAL_GROUP',
         'relation': 'interpretation_framework', 'evidence': 'curated_human_pathway',
         'reference': 'https://reactome.org/content/detail/R-HSA-913531',
         'context': 'human_general', 'sign': 'not_applicable',
         'limit': 'Keine Caco-2-spezifische Reaktion oder Aktivität belegt.'},
        {'id': 'T4E02', 'source': 'T4:CACO2_PROTEOME', 'target': 'T4:IFN_FUNCTIONAL_GROUP',
         'relation': 'observed_altered_members', 'evidence': 'published_proteomics',
         'reference': source_article, 'context': 'Caco-2; within-cell-line comparison',
         'sign': 'mixed', 'limit': '27/131 detektierte Mitglieder verändert; 25 erhöht, 2 erniedrigt. Keine Kausalkante.'},
        {'id': 'T4E03', 'source': 'T4:CALU3_PROTEOME', 'target': 'T4:IFN_FUNCTIONAL_GROUP',
         'relation': 'observed_altered_members', 'evidence': 'published_proteomics',
         'reference': source_article, 'context': 'Calu-3; within-cell-line comparison',
         'sign': 'mixed', 'limit': '105/129 detektierte Mitglieder verändert. Separater Zelllinienkontext.'},
        {'id': 'T4E04', 'source': 'T4:CACO2_TRANSCRIPT', 'target': 'T4:IFN_FUNCTIONAL_GROUP',
         'relation': 'supports_functional_interpretation', 'evidence': 'published_targeted_transcript_measurement',
         'reference': source_article, 'context': 'Caco-2; selected transcripts',
         'sign': 'not_applicable', 'limit': 'Transkriptmessung ist keine Proteinmessung und validiert keine einzelne Signalkante.'},
    ]
    by_id = {node['id'] for node in nodes}
    if len(by_id) != len(nodes) or len({e['id'] for e in edges}) != len(edges):
        raise ValueError('Duplicate graph ID')
    if any(e['source'] not in by_id or e['target'] not in by_id for e in edges):
        raise ValueError('Dangling graph edge')
    if any(e['relation'] in ('activates', 'inhibits', 'binds') for e in edges):
        raise ValueError('Unsupported causal/molecular relation')

    OUT.mkdir(exist_ok=True)
    write_tsv(OUT / 'screening.tsv', rows, list(rows[0]))
    write_tsv(OUT / 'nodes.tsv', nodes, list(nodes[0]))
    write_tsv(OUT / 'edges.tsv', edges, list(edges[0]))
    payload = {'scope': 'published observations plus general interpretation framework',
               'review_method': 'LLM-assisted bounded curation',
               'nodes': nodes, 'edges': edges}
    (OUT / 'network.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n')
    lines = ['digraph Evidence {', '  rankdir=LR;', '  graph [bgcolor="white", pad="0.25"];',
             '  node [shape=box, style="rounded,filled", fillcolor="#eff4f8", color="#526477", fontname="Helvetica"];',
             '  edge [color="#687889", fontname="Helvetica", fontsize=10];']
    for node in nodes:
        label = node['label'].replace('"', '\\"')
        lines.append(f'  "{node["id"]}" [label="{label}"];')
    for edge in edges:
        label = edge['relation'].replace('_', ' ')
        lines.append(f'  "{edge["source"]}" -> "{edge["target"]}" [label="{edge["id"]}: {label}", style=dashed];')
    lines.append('}')
    (OUT / 'network.dot').write_text('\n'.join(lines) + '\n')
    subprocess.run(['dot', '-Tsvg', str(OUT / 'network.dot'), '-o', str(OUT / 'network.svg')], check=True)

    manifest = {path.name: sha(path) for path in OUT.iterdir() if path.is_file() and path.name != 'validation.json'}
    validation = {'search_occurrences': audit['summary']['search_occurrences'],
                  'internal_candidates': len(register), 'unassigned_source_records': len(audit['unassigned_records']),
                  'case_studies': 1, 'background_sources': 1,
                  'related_preprints_not_independent': 1,
                  'not_selected_on_title_abstract': 48,
                  'node_count': len(nodes), 'edge_count': len(edges),
                  'all_edges_have_context_reference_and_limit': all(e['context'] and e['reference'] and e['limit'] for e in edges),
                  'manifest_sha256': manifest}
    (OUT / 'validation.json').write_text(json.dumps(validation, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k: v for k, v in validation.items() if k != 'manifest_sha256'}, indent=2))


if __name__ == '__main__':
    main()
