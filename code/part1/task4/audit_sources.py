"""Offline provenance audit; no molecular extraction or quantitative analysis."""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def relative(path):
    return str(path.resolve().relative_to(PROJECT))


def resolve(ref):
    path = Path(ref)
    if not path.is_absolute():
        path = PROJECT / path
    # Archived absolute paths remain usable in a copied workspace.
    if not path.exists() and '/part1/task4/' in str(path):
        path = ROOT / str(path).split('/part1/task4/', 1)[1]
    path.resolve().relative_to(ROOT)
    return path


def checked_body(ref):
    path = resolve(ref)
    metadata = read_json(path)
    body = path.parent / metadata['body']
    if digest(body) != metadata['sha256']:
        raise ValueError(f'Cached response hash mismatch: {path}')
    return metadata, body


def snapshot():
    paths = [ROOT / name for name in (
        'search.json', 'search_targeted.json', 'retrieval.json',
        'retrieval_targeted.json', 'pride_response.json',
        'mendeley_response.json', 'supplement_response.json', 'config.json')]
    for folder in ('raw', 'corpus', 'data'):
        paths.extend(p for p in (ROOT / folder).rglob('*') if p.is_file())
    return {relative(p): digest(p) for p in sorted(paths)}


def collect():
    before = snapshot()
    searches = [read_json(ROOT / n) for n in ('search.json', 'search_targeted.json')]
    retrievals = [r for n in ('retrieval.json', 'retrieval_targeted.json')
                  for r in read_json(ROOT / n)]
    records = [r for search in searches for r in search['records']]
    papers = {p['paper_id']: p for search in searches for p in search['papers']}
    by_id = defaultdict(list)
    for r in retrievals:
        by_id[r['paper_id']].append(r)
    if set(by_id) != set(papers):
        raise ValueError('Search/retrieval ID mismatch')
    register = []
    reasons = Counter()
    corpus_names = set()
    for paper_id, paper in sorted(papers.items()):
        attempts = by_id[paper_id]
        docs = [r['document'] for r in attempts if r['document']]
        local = None
        if docs:
            path = ROOT / 'corpus' / (paper_id.replace(':', '_').replace('/', '_') + '.txt')
            for document in docs:
                expected = hashlib.sha256(document['text'].encode()).hexdigest()
                if expected != document['text_sha256'] or digest(path) != expected:
                    raise ValueError(f'Corpus hash mismatch: {paper_id}')
            local = relative(path)
            corpus_names.add(path.name)
            status = 'retrieved'
        else:
            unique_reasons = sorted({r['reason'] for r in attempts})
            status = '; '.join(unique_reasons)
        reasons[status] += 1
        register.append({
            'paper_id': paper_id, 'pmcid': paper.get('pmcid', ''),
            'doi': paper.get('doi', ''), 'title': paper['title'],
            'search_occurrences': sum(r['paper_id'] == paper_id for r in records),
            'retrieval_status': status, 'retrieval_attempts': len(attempts),
            'local_fulltext': local, 'eligibility': 'not_assessed',
            'retrieval_source_refs': [relative(resolve(r['source_ref'])) for r in attempts],
        })
    if corpus_names != {p.name for p in (ROOT / 'corpus').glob('*.txt')}:
        raise ValueError('Corpus inventory mismatch')

    endpoints = {}
    bodies = {}
    for name in ('pride', 'mendeley', 'supplement'):
        receipt = read_json(ROOT / f'{name}_response.json')
        metadata, body = checked_body(receipt['source_ref'])
        if receipt['status'] != metadata['http_status'] or receipt['url'] != metadata['url']:
            raise ValueError(f'Response receipt mismatch: {name}')
        endpoints[name] = {k: metadata[k] for k in ('url', 'http_status', 'fetched_at_utc', 'sha256')}
        endpoints[name]['body_path'] = relative(body)
        bodies[name] = body
    pride = read_json(bodies['pride'])
    endpoints['pride']['project'] = {k: pride[k] for k in ('accession', 'title', 'doi', 'references')}

    selected = next(r for r in retrievals if r['paper_id'] == 'PMID:33898942' and r['document'])
    _, article_body = checked_body(selected['source_ref'])
    article = ET.fromstring(article_body.read_bytes())
    identifiers = {x.get('pub-id-type'): x.text for x in article.findall('./front/article-meta/article-id')}
    if identifiers.get('pmid') != '33898942' or identifiers.get('doi') != '10.1016/j.isci.2021.102420':
        raise ValueError('Selected article identifier mismatch')
    data_sections = [s for s in article.iter('sec')
                     if 'Data and code availability' in ''.join(s.findtext('title', ''))]
    accession_in_availability = any('PXD023760' in ''.join(s.itertext()) for s in data_sections)
    if not accession_in_availability or pride['accession'] != 'PXD023760':
        raise ValueError('Article/PRIDE accession mismatch')
    mapping = {}
    for item in article.iter('supplementary-material'):
        media = item.find('media')
        if media is None:
            continue
        name = media.get('{http://www.w3.org/1999/xlink}href')
        caption = ''.join(item.find('caption').itertext())
        label = re.match(r'(Table S\d+|Document S\d+)', caption).group(1)
        if name in mapping and mapping[name] != label:
            raise ValueError(f'Conflicting supplement labels: {name}')
        mapping[name] = label
    supplements = []
    ns = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(bodies['supplement']) as archive:
        for name, label in sorted(mapping.items()):
            local = ROOT / 'data' / name
            with archive.open(name) as stream:
                archived_sha = hashlib.file_digest(stream, 'sha256').hexdigest()
            if digest(local) != archived_sha:
                raise ValueError(f'Supplement bytes differ: {name}')
            entry = {'file': relative(local), 'label': label, 'sha256': archived_sha,
                     'archive_member': name, 'archive_match': True}
            if local.suffix == '.xlsx':
                with zipfile.ZipFile(local) as book:
                    error = book.testzip()
                    if error:
                        raise ValueError(f'XLSX CRC error: {name}/{error}')
                    workbook = ET.fromstring(book.read('xl/workbook.xml'))
                    entry['sheet_names'] = [s.get('name') for s in workbook.findall('x:sheets/x:sheet', ns)]
                    entry['zip_crc_ok'] = True
            supplements.append(entry)

    counts = Counter(r['paper_id'] for r in records if r['paper_id'])
    unidentified = [r for r in records if not r['paper_id']]
    summary = {
        'search_occurrences': len(records), 'missing_pipeline_paper_id': len(unidentified),
        'duplicate_id_occurrences': sum(c - 1 for c in counts.values()),
        'unique_pipeline_paper_ids': len(papers), 'retrieval_status_counts': dict(reasons),
        'local_fulltexts': len(corpus_names), 'supplements_byte_identical': len(supplements),
        'xlsx_crc_valid': sum('sheet_names' in s for s in supplements),
    }
    if before != snapshot():
        raise ValueError('Source files changed during audit')
    return {
        'scope': 'Offline bibliographic provenance and file integrity; no biological eligibility or quantitative validation',
        'summary': summary, 'searches': [s for obj in searches for s in obj['searches']],
        'records': records, 'unassigned_records': unidentified, 'candidate_register': register,
        'endpoints': endpoints, 'article_identifiers': identifiers,
        'article_raw_path': relative(article_body),
        'accession_present_in_article_data_availability': accession_in_availability,
        'supplements': supplements, 'source_hashes': before,
        'source_files_unchanged_during_audit': True,
        'script_sha256': digest(Path(__file__)),
    }


def report(result):
    s = result['summary']
    lines = ['# Quellen- und Dateiaudit zu Aufgabe 4', '',
             'Offline-Prüfung der gespeicherten Recherche und Dateiprovenienz. '
             'Die fachliche Eignung der Kandidaten und numerische Messergebnisse wurden nicht bewertet.', '',
             '## Recherchebestand', '',
             f"{s['search_occurrences']} Treffer-Vorkommen, {s['duplicate_id_occurrences']} ID-Dubletten "
             f"und {s['missing_pipeline_paper_id']} Datensatz ohne interne `paper_id` ergeben "
             f"{s['unique_pipeline_paper_ids']} intern identifizierte Datensätze. "
             f"{s['local_fulltexts']} lokale Volltexte stimmen mit den archivierten Retrievaltexten und deren Hashes überein.", '',
             'Der nicht übernommene Datensatz besitzt bereits die Quellkennung `PMC:PMC8108313`. '
             'Die historische Bezeichnung "ohne verwendbare Kennung" war daher zu weitgehend. '
             'Festgestellt ist eine fehlende interne Kennung. Eine Nachakquisition oder Zusammenführung '
             'mit anderen Publikationsversionen ist nicht erfolgt.', '',
             'Zugriffshindernisse sind keine fachlichen Ausschlüsse. Alle Einträge des Registers '
             'tragen deshalb `eligibility=not_assessed`.', '',
             '| Retrievalstatus | Eindeutige interne IDs |', '|---|---:|']
    lines += [f'| {key} | {value} |' for key, value in s['retrieval_status_counts'].items()]
    lines += ['', '## Datensatz und Supplemente', '',
              'Die Artikelkennung und DOI stimmen mit der ausgewählten Fallstudie überein. '
              '`PXD023760` steht in deren Datenverfügbarkeitsabschnitt und im archivierten '
              'PRIDE-Datensatz. PRIDE verwendet einen anderen Projekttitel; DOI und Referenzliste '
              'sind dort leer. Die Zuordnung stützt sich daher auf den expliziten Zugang im Artikel.', '',
              'Der archivierte PRIDE-Abruf und der Supplementabruf haben HTTP 200. '
              'Der archivierte Mendeley-API-Abruf hat HTTP 404. Dieser Fehlschlag sagt nichts '
              'über die heutige Verfügbarkeit einer Mendeley-Webseite aus.', '',
              'Alle neun lokalen Supplementdateien sind bytegleich mit den Mitgliedern des '
              'archivierten Europe-PMC-ZIPs. Die acht XLSX-Container bestehen die CRC-Prüfung. '
              'Tabellenlabels stammen aus den XML-Medienverweisen des Artikels; Blattnamen '
              'wurden ausschließlich aus `xl/workbook.xml` gelesen.', '',
              '| Lokale Datei | Label im Artikel | Blattname |', '|---|---|---|']
    lines += [f"| {Path(x['file']).name} | {x['label']} | {', '.join(x.get('sheet_names', [])) or 'PDF'} |" for x in result['supplements']]
    lines += ['', 'Numerische Zellwerte, Probenspalten, Formeln und biologische Kennungen '
              'wurden nicht geprüft. Bytegleichheit und lesbare Container belegen keine '
              'statistische Reproduzierbarkeit. Die Beschreibungsfehler "Calu2"/"Caco3" '
              'im Artikel bleiben bestehen; die Blattnamen lauten `Calu3_norm_file` und `Caco2_norm_file`.', '',
              '## Kandidaten- und Zugriffsregister', '',
              'Die maschinenlesbare Fassung in `audit.json` enthält Titel, DOI, Quellverweise '
              'und sämtliche 54 Suchvorkommen. Die folgende Tabelle fasst nach interner ID zusammen.', '',
              '| Interne ID | PMC-ID | Suchvorkommen | Retrievalstatus | Fachliche Eignung |',
              '|---|---|---:|---|---|']
    lines += [f"| {r['paper_id']} | {r['pmcid'] or ''} | {r['search_occurrences']} | {r['retrieval_status']} | ungeprüft |" for r in result['candidate_register']]
    lines += ['', '## Reproduktion', '',
              'Ab Projektverzeichnis:', '', '```sh',
              'python3 -B part1/task4/audit_sources.py --check part1/task4/audits/source-audit-20260923',
              '```', '',
              'Ein neuer Lauf benötigt mit `--out` ein noch nicht vorhandenes Verzeichnis. '
              'Das Skript nutzt nur die Python-Standardbibliothek, öffnet keine Netzwerkverbindung '
              'und liest keine Evaluationslabels. Hashes aller Quelldateien stehen in `audit.json`. '
              'Die Berichtserstellung ist LLM-unterstützt; sie ist kein menschlicher Goldstandard.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--out', type=Path)
    mode.add_argument('--check', type=Path)
    args = parser.parse_args()
    if args.out and args.out.exists():
        parser.error('Output directory already exists; choose a new one')
    result = collect()
    if args.check:
        if read_json(args.check / 'audit.json') != result:
            raise SystemExit('Audit differs from stored result')
        if (args.check / 'REPORT.md').read_text() != report(result):
            raise SystemExit('Report differs from regenerated report')
        print('Offline replay matches; source hashes and report verified.')
    else:
        args.out.mkdir(parents=True, exist_ok=False)
        (args.out / 'audit.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
        (args.out / 'REPORT.md').write_text(report(result))
        print(json.dumps(result['summary'], indent=2))


if __name__ == '__main__':
    main()
