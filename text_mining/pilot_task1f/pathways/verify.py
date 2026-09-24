"""Offline-Prüfung der gespeicherten Antworten; kein Netzwerk, keine Schreibzugriffe."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
rows = [json.loads(line) for line in (HERE / 'requests.jsonl').read_text().splitlines()]
amendment = json.loads((HERE / 'amendment.json').read_text())
assert (amendment['original_limit'], amendment['additional_limit'], amendment['total_limit']) == (14, 8, 22)
assert len(rows) == 22 and len(rows[14:]) <= amendment['additional_limit']
initial_log = b''.join((HERE / 'requests.jsonl').read_bytes().splitlines(keepends=True)[:14])
assert hashlib.sha256(initial_log).hexdigest() == amendment['initial_log_sha256']
assert dt.datetime.fromisoformat(rows[13]['utc_end']) < dt.datetime.fromisoformat(amendment['utc'])
assert dt.datetime.fromisoformat(amendment['utc']) < dt.datetime.fromisoformat(rows[14]['utc_start'])
for n, row in enumerate(rows, 1):
    assert row['number'] == n
    assert row['curl']['num_redirects'] == 0
    assert row['curl']['http_code'] == (0 if n in (5, 6) else 200)
    assert row['exit_code'] == (7 if n in (5, 6) else 0)
    assert hashlib.sha256((HERE / row['body']).read_bytes()).hexdigest() == row['body_sha256']
    assert (HERE / row['headers']).exists() and (HERE / row['stderr']).exists()
    assert dt.datetime.fromisoformat(row['utc_start']).utcoffset() == dt.timedelta(0)
    assert dt.datetime.fromisoformat(row['utc_end']) >= dt.datetime.fromisoformat(row['utc_start'])
    assert '-q' in row['command'] and '-L' not in row['command'] and '--location' not in row['command']
    print(f"REQUEST {n:02}: {row['utc_start']} .. {row['utc_end']} HTTP={row['curl']['http_code']} curl={row['exit_code']} {row['url']} raw={row['body']}")

targets = {'PER2': '8864', 'TP53': '7157', 'MDM2': '4193', 'ARNTL/BMAL1': '406', 'CLOCK': '9575'}
genesets = []
for text_n, xml_n, pid, expected in [(1, 3, 'hsa04710', {'8864','406','9575'}), (2, 4, 'hsa04115', {'7157','4193'})]:
    text = (HERE / f'request_{text_n:02}.body').read_text()
    section = text.split('GENE        ', 1)[1].split('\nREFERENCE', 1)[0].split('\nCOMPOUND', 1)[0]
    genes = dict(re.findall(r'^\s*(\d+)\s+(\S+);', section, re.M))
    root = ET.parse(HERE / f'request_{xml_n:02}.body').getroot()
    assert root.get('name') == 'path:' + pid and root.get('org') == 'hsa'
    entries = {e.get('id'): e for e in root.findall('entry')}
    xmlgenes = {g.split(':')[1] for e in entries.values() if e.get('type') == 'gene' for g in e.get('name').split()}
    assert set(genes) == xmlgenes
    assert set(genes) & set(targets.values()) == expected
    genesets.append(set(genes))
    print(pid, 'unique genes=', len(genes), 'entries=',len(entries), 'relations=',len(root.findall('relation')))
    print('presence:', {name: gid in genes for name, gid in targets.items()})
    if xml_n == 3:
        assert [c.get('id') for c in entries['86'].findall('component')] == ['7','8']
        assert entries['7'].get('name') == 'hsa:406'
        assert entries['8'].get('name') == 'hsa:4862 hsa:9575'
        rel = root.find("relation[@entry1='86'][@entry2='16']")
        assert rel is not None and rel.get('type') == 'PPrel' and not rel.findall('subtype')
        assert entries['16'].get('name') == 'hsa:5187 hsa:8863 hsa:8864'
        print('Uhr: Gruppe 86 -> PER1/2/3-Knoten 16, PPrel ohne subtype; keine eindeutige Einzelgenkante.')
    else:
        selected = []
        for r in root.findall('relation'):
            a,b = [entries[r.get(k)].get('name') for k in ('entry1','entry2')]
            if a in ('hsa:7157','hsa:4193') and b in ('hsa:7157','hsa:4193'):
                selected.append((r.get('entry1'), r.get('entry2'), a, b, r.get('type'), [s.get('name') for s in r.findall('subtype')]))
        assert selected == [('50','49','hsa:7157','hsa:4193','PPrel',['activation']), ('50','51','hsa:7157','hsa:4193','GErel',['expression'])]
        print('Eindeutige Zielgen-Relationen:', selected)
    refs = re.findall(r'REFERENCE\s+PMID:(\d+)(.*?)(?=\nREFERENCE|\nREL_PATHWAY)', text, re.S)
    for pmid, block in refs:
        print('PATHWAY REFERENCE', pid, pmid, re.search(r'DOI:(\S+)', block).group(1))
assert not (genesets[0] & genesets[1])
assert 'SYMBOL      BMAL1, ARNTL,' in (HERE/'request_07.body').read_text()
print('PASS: Geneintrag bestätigt ARNTL/BMAL1; Schnittmenge beider Genlisten leer.')
for n in (5,6):
    assert 'Failed to connect' in (HERE/f'request_{n:02}.stderr').read_text()
assert 'sp_human' in (HERE/'request_12.body').read_text()
assert 'name="keywords"' in (HERE/'request_14.body').read_text()
assert 'action="search" method="post"' in (HERE/'request_14.body').read_text()
articles = ET.parse(HERE/'request_13.body').findall('.//PubmedArticle')
assert len(articles) == 2
for a in articles:
    print('CPDB PUBLICATION:', a.findtext('.//PMID'), a.findtext('.//ArticleTitle'), [(e.get('IdType'),e.text) for e in a.findall('./PubmedData/ArticleIdList/ArticleId')])
    print('ABSTRACT:', ' '.join(''.join(e.itertext()) for e in a.findall('.//AbstractText')))
from cpdb_evidence import extract
from urllib.parse import parse_qs, urlsplit
cpdb = extract()
assert json.loads(json.dumps(cpdb)) == json.loads((HERE / 'cpdb_evidence.json').read_text())
assert {n: len(v) for n, v in cpdb.items()} == {'15': 7, '16': 35, '17': 9, '20': 120, '21': 32, '22': 273}
for n, keyword, space in [(15,'circadian','Pathway'), (16,'p53','Pathway'), (17,'PER2','PhysicalEntity'), (22,'TP53\nMDM2\nARNTL\nBMAL1\nCLOCK','PhysicalEntity')]:
    query = parse_qs(urlsplit(rows[n-1]['url']).query)
    assert query == {'nameacc':['name'], 'keywords':[keyword], 'searchspace':[space]}
for n, cpdbid, sourceid in [('15','186064','hsa04710'), ('16','186056','hsa04115'), ('15','147321','R-HSA-400253')]:
    record = next(r for r in cpdb[n] if r['id'] == cpdbid)
    assert any(sourceid in url for url, source in record['sources'])
for n, cpdbid, names in [('17','147176',{'PER2'}), ('22','8712',{'TP53'}), ('22','14013',{'MDM2'}), ('22','10181',{'ARNTL','BMAL1'}), ('22','10197',{'CLOCK'})]:
    record = next(r for r in cpdb[n] if r['id'] == cpdbid)
    assert names <= set(record['names']) and record['kind'] == 'protein'
    print('CPDB TARGET:', cpdbid, sorted(names))
for title, ids in [
    ('Physical interaction of PER2 gene; TP53', {'2649126','2649135','2649141','3025362','2649138','3025365'}),
    ('Physical interaction of MDM2 Gene; PER2 gene', {'3523918','2649147','3523915','3523921','4069781'})]:
    records = [r for r in cpdb['20'] if r['names'] == [title]]
    assert {r['id'] for r in records} == ids
    assert all(r['sources'] and all(source == 'Biogrid' for url, source in r['sources']) for r in records)
    print('CPDB PHYSICAL INTERACTION:', title, sorted(ids), 'source=Biogrid; no direction inferred')
for n, pid in [(18,'hsa04710'), (19,'hsa04115')]:
    body = (HERE / f'request_{n:02}.body').read_text()
    assert 'The selected objects have no interactions in ConsensusPathDB.' in body and pid in body
assert '120 interactions (38 distinct ones)' in (HERE/'request_20.body').read_text()
assert '32 interactions (32 distinct ones)' in (HERE/'request_21.body').read_text()
print('PASS: 22 Abrufversuche = ursprüngliche 14 + genehmigte 8; Amendment vor Request 15, ursprüngliches Log unverändert.')
print('PASS: alle Body-Hashes, UTC, Status; CPDB-Suchtreffer, Quellen-IDs und physische PER2–TP53/PER2–MDM2-Annotationen geprüft.')
print('Offline: keine Remote-Requests, keine Simulation, kein SBML-Modell abgerufen.')
