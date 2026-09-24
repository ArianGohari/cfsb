#!/usr/bin/env python3
"""Build the bounded human evidence graph and reproducible metadata audit."""
import csv, gzip, hashlib, json, subprocess
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
DATE = '2026-09-23'

def write_tsv(name, rows):
    with (DATA / name).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter='\t')
        w.writeheader(); w.writerows(rows)

sources = [
 {'id':'RAYNER2010','citation':'Rayner et al. (2010), Science 328:1570-1573','doi':'10.1126/science.1189862','url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC3114628/','use':'miR-33, ABCA1, Efflux; Mensch-Maus-Abgrenzung'},
 {'id':'DEPUYDT2020','citation':'Depuydt et al. (2020), Circulation Research 127:1437-1455','doi':'10.1161/CIRCRESAHA.120.316770','url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC7641189/','use':'Humane Karotis-Makrophagenzustände'},
 {'id':'WONG2011','citation':'Wong et al. (2011), Blood 118:e16-e31','doi':'10.1182/blood-2010-12-326355','url':'https://doi.org/10.1182/blood-2010-12-326355','use':'Humane Blutmonozyten-Phänotypen'},
 {'id':'QUILLARD2015','citation':'Quillard et al. (2015), European Heart Journal 36:1394-1404','doi':'10.1093/eurheartj/ehv044','url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC4458287/','use':'Neutrophile und Endothelverletzung'},
 {'id':'WARNATSCH2015','citation':'Warnatsch et al. (2015), Science 349:316-320','doi':'10.1126/science.aaa8064','url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC4854322/','use':'Humane NET- und Monozytenexperimente, Fig. 1A/B und 3E-G'},
 {'id':'BASHORE2024','citation':'Bashore et al. (2024), ATVB 44:930-945','doi':'10.1161/ATVBAHA.123.320524','url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC10978277/','use':'Öffentliches multimodales Datenbeispiel, keine abgeleiteten Kausalkanten'},
]
write_tsv('sources.tsv', sources)
registry=json.loads((DATA/'gene_registry.json').read_text())['result']
nodes=[]
for i in registry['uids']:
 r=registry[i]
 nodes.append(dict(id='NCBIGene:'+i,label=r['name'],entity_type='gene_product',taxon=9606,external_url='https://www.ncbi.nlm.nih.gov/gene/'+i,definition='Gen-zentrierter Anker; RNA oder Protein durch Kanten-Endpunkt spezifiziert.'))
nodes.append(dict(id='miRBase:MIMAT0000091',label='hsa-miR-33a-5p',entity_type='mature_miRNA',taxon=9606,external_url='https://www.mirbase.org/mature/MIMAT0000091',definition='Reife 5p-miRNA; ältere Quelle nennt miR-33.'))
local=[
 ('efflux','Cholesterinefflux zu ApoA1','process','Zellulärer Efflux-Endpunkt, kein vollständiger Reverse-Cholesterol-Transport.'),
 ('macro_il1b','IL1B+ Makrophagen','cell_state','Beobachteter Zustand humaner Karotisplaques, Depuydt 2020.'),
 ('macro_tnf','TNF+ Makrophagen','cell_state','Beobachteter Zustand humaner Karotisplaques, Depuydt 2020.'),
 ('macro_trem2','TREM2+ schaumzellähnlich','cell_state','Transkriptomisch beschriebener Zustand; Marker ist kein Herkunftsnachweis.'),
 ('mono_classical','Klassische Monozyten','cell_state','Humane Blutmonozyten CD14++ CD16-.'),
 ('mono_intermediate','Intermediäre Monozyten','cell_state','Humane Blutmonozyten CD14++ CD16+.'),
 ('mono_nonclassical','Nichtklassische Monozyten','cell_state','Humane Blutmonozyten CD14+ CD16++.'),
 ('neutrophils','Neutrophile','cell_type','Humane Blutneutrophile in Kokultur.'),
 ('ec_apoptosis','Endothel-Apoptose','phenotype','Gemessener Endothel-Endpunkt in vitro.'),
 ('crystals','Cholesterinkristalle','material','Kristalliner Cholesterinzustand, keine gelöste Metabolitkonzentration.'),
 ('nets','NETs','extracellular_material','Neutrophile extrazelluläre Chromatin-/Proteinstrukturen.'),
 ('il1b_release','Reife IL-1β freigesetzt','phenotype','Proteolytische Reifung und Freisetzung, von IL1B-RNA getrennt.'),
]
for key,label,typ,definition in local:
 nodes.append(dict(id='TASK5:'+key,label=label,entity_type=typ,taxon=9606,external_url='',definition=definition))
edges=[]
def edge(a,b,relation,sign,context,endpoint,evidence,source,location,limit,condition=''):
 edges.append(dict(id=f'H{len(edges)+1:02}',source=a,target=b,relation=relation,sign=sign,taxon=9606,cell_context=context,condition=condition,measured_endpoint=endpoint,evidence_class=evidence,source_id=source,source_location=location,limitation=limit))
G=lambda n:'NCBIGene:'+str(n)
L=lambda n:'TASK5:'+n
mi='miRBase:MIMAT0000091'
edge(mi,G(19),'posttranscriptional_repression','-', 'THP-1-derived human macrophages','ABCA1 protein','E1_target_and_perturbation','RAYNER2010','Fig. 2 and 3','Cell-line evidence; not an effect-size estimate in patient plaque.')
edge(mi,L('efflux'),'decreases_process','-', 'human macrophages in vitro','cholesterol efflux to ApoA1','E2_perturbation_phenotype','RAYNER2010','Fig. 3','Integrated phenotype; does not quantify ABCA1-only mediation.')
edge(G(19),L('efflux'),'participates_in','unknown','human macrophages','ABCA1-dependent efflux interpretation','E4_mechanistic_context','RAYNER2010','Fig. 3 and main text','Not a separately fitted reaction or rate law.')
for gene,state in [(3553,'macro_il1b'),(7124,'macro_tnf'),(54209,'macro_trem2')]:
 edge(G(gene),L(state),'marker_of','unknown','human carotid plaque macrophages','RNA expression','E3_observational','DEPUYDT2020','Abstract; myeloid-cell analysis','Cluster association does not establish causal state control.')
for gene,state,level in [(929,'mono_classical','CD14++'),(929,'mono_intermediate','CD14++'),(2214,'mono_intermediate','CD16+'),(929,'mono_nonclassical','CD14+'),(2214,'mono_nonclassical','CD16++')]:
 edge(G(gene),L(state),'phenotype_marker','unknown','human peripheral blood monocytes','surface protein; '+level,'E3_observational','WONG2011','Abstract and subset definitions','CD16 interpreted as monocytic FCGR3A; not neutrophil FCGR3B. Gating thresholds are study-specific.')
for gene,endpoint in [(3576,'CXCL8/IL8 RNA'),(3383,'ICAM1 RNA/protein')]:
 edge(G(7097),G(gene),'increases_expression','+','cultured human saphenous-vein endothelial cells',endpoint,'E2_perturbation_phenotype','QUILLARD2015','Fig. 1A/B','Multi-step response; not direct TF binding or a macrophage-intrinsic edge.','TLR2 stimulation in the study')
edge(G(7097),L('ec_apoptosis'),'increases_phenotype','+','cultured human saphenous-vein endothelial cells','caspase-3 cleavage / caspase-3/7 activity','E2_perturbation_phenotype','QUILLARD2015','Fig. 1E/F','In-vitro endpoint; does not establish coronary erosion causality.','TLR2 stimulation')
edge(L('neutrophils'),L('ec_apoptosis'),'potentiates_phenotype','+','human neutrophil/endothelial co-culture','endothelial apoptosis','E2_perturbation_phenotype','QUILLARD2015','Neutrophil co-culture results','Composite cell-cell effect, no unique molecular mediator assigned.','TLR2-activated endothelium')
edge(L('crystals'),L('nets'),'induces_formation','+','human blood neutrophils','extracellular chromatin / microscopy','E2_perturbation_phenotype','WARNATSCH2015','Fig. 1A/B','In vitro; crystalline material is distinct from plasma LDL.')
edge(L('nets'),G(3553),'increases_transcript','+','CD14-purified human blood monocytes','IL1B mRNA','E2_perturbation_phenotype','WARNATSCH2015','Fig. 3G','No direct promoter interaction established; blood monocytes, not isolated plaque macrophages.')
edge(L('nets'),L('il1b_release'),'primes_conditional_release','+','CD14-purified human blood monocytes','mature IL-1β in supernatant','E2_perturbation_phenotype','WARNATSCH2015','Fig. 3E/F','NETs alone do not justify substantial mature cytokine release.','NET priming AND subsequent cholesterol-crystal stimulation')
write_tsv('nodes.tsv',nodes);write_tsv('edges.tsv',edges)
network=dict(schema_version='1.0',curation_date=DATE,curation='LLM-assisted source-constrained curation; no independent human double review',model_type='static contextual evidence multigraph',nodes=nodes,edges=edges,sources=sources)
(DATA/'network.json').write_text(json.dumps(network,ensure_ascii=False,indent=2)+'\n')
# A feature-list audit is deliberately not an expression analysis.
features=list(csv.reader((DATA/'GSM8029950_features.tsv').open(),delimiter='\t'))
counts=Counter(r[2] for r in features)
mapping=[]
for n in nodes:
 if n['entity_type']=='gene_product':
  found=[r for r in features if r[1]==n['label'] and r[2]=='Gene Expression']
  mapping.append(dict(node_id=n['id'],symbol=n['label'],feature_id=';'.join(r[0] for r in found),matches=len(found),meaning='feature annotation only; expression not tested'))
write_tsv('feature_mapping.tsv',mapping)
# Graphviz draws relation IDs so long context text stays in the edge table.
q=lambda s:json.dumps(s,ensure_ascii=False)
dot=['digraph G {','graph [rankdir=LR, bgcolor="white", pad="0.2", nodesep="0.28", ranksep="0.7"];','node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=12, color="#334155", fillcolor="#e2e8f0"];','edge [fontname="Helvetica", fontsize=10];']
for n in nodes:
 color={'gene_product':'#dbeafe','mature_miRNA':'#fef3c7','cell_state':'#dcfce7'}.get(n['entity_type'],'#f1f5f9')
 dot.append(f'{q(n["id"])} [label={q(n["label"])}, fillcolor={q(color)}];')
for e in edges:
 color={'-':'#b91c1c','+':'#1d4ed8','unknown':'#64748b'}[e['sign']]
 style='dashed' if e['sign']=='unknown' else 'solid'
 arrow='tee' if e['sign']=='-' else ('none' if e['sign']=='unknown' else 'normal')
 label = e['id'] + ('\n+ Kristalle' if e['id']=='H18' else '')
 dot.append(f'{q(e["source"])} -> {q(e["target"])} [label={q(label)}, color={q(color)}, style={q(style)}, arrowhead={q(arrow)}];')
dot.append('}')
(ROOT/'figures/network.dot').write_text('\n'.join(dot))
subprocess.run(['dot','-Tsvg',str(ROOT/'figures/network.dot'),'-o',str(ROOT/'figures/network.svg')],check=True)
# Offline structural, accession and taxon checks.
ids={n['id'] for n in nodes};src={s['id'] for s in sources}
assert len(ids)==len(nodes)
assert all(e['source'] in ids and e['target'] in ids and e['source_id'] in src for e in edges)
assert all(e['taxon']==9606 and e['sign'] in ('+','-','unknown') for e in edges)
assert all(registry[i]['organism']['taxid']==9606 for i in registry['uids'])
assert 'hsa-miR-33a-5p' in (DATA/'MIMAT0000091.html').read_text()
assert all(m['matches']==1 for m in mapping)
assert all('NCBIGene:9619' not in (e['source'],e['target']) for e in edges) # no human ABCG1 target transfer
assert 'cholesterol-crystal' in edges[-1]['condition']
assert 'GSM8029950' in (DATA/'GSE253902.soft.txt').read_text()
assert 'carotid_5, ADT' in (DATA/'GSM8029951.soft.txt').read_text()
assert (DATA/'network.json').stat().st_size > 0
report=dict(date=DATE,nodes=len(nodes),edges=len(edges),evidence_classes=dict(Counter(e['evidence_class'] for e in edges)),feature_rows=len(features),feature_types=dict(counts),gene_nodes_mapped=sum(m['matches']==1 for m in mapping),checks='PASS',limitations=['No count-matrix analysis','No SFB1123 data','No kinetic parameters','No human double curation'])
(ROOT/'audits/validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
