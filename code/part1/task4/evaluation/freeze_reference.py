"""Build the fixed corpus-only selection. Refuse replacement of frozen artifacts."""
import hashlib
import json
from pathlib import Path
import re
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_new(path, value):
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')

# Selection was made from complete local paragraphs, before opening run artifacts.
# Tuple: PMID, paragraph line, sentence index, stratum, rationale, relations.
# Relation: subject surface, predicate, object surface, subject identity, object identity.
ROWS = [
('33143316',4,4,'positive','Cited inhibition; drug to enzyme, not reverse.', [('Camostat','INHIBITS','TMPRSS2','camostat','TMPRSS2 protein')]),
('33143316',5,0,'positive','Established inhibition survives the separate speculative treatment clause.', [('Aprotinin','INHIBITS','TMPRSS2','aprotinin','TMPRSS2 protein')]),
('33143316',5,1,'context','Investigation objective, not a molecular result.', []),
('33143316',40,0,'positive','Two inhibitors target trypsin activity. Trypsin is a family-level identity; no single accession asserted.', [('aprotinin','INHIBITS','trypsin','aprotinin','trypsin family'),('SERPINA1/alpha-1 antitrypsin','INHIBITS','trypsin','SERPINA1 protein','trypsin family')]),
('33143316',44,0,'uncertain','Suggested class-level mechanism, not a specific confirmed molecular pair.', []),
('33143316',44,1,'negated','No significant post-adsorption antiviral effect under the stated assay; do not generalize to all conditions.', []),
('33143316',47,0,'positive','TMPRSS2 activates viral S by cleavage; unnamed inhibitor class is not a specific entity. Cleavage itself is outside the target predicate set.', [('TMPRSS2','ACTIVATES','S protein','TMPRSS2 protein','SARS-CoV-2 spike protein')]),
('33143316',49,1,'positive','Measured suppression of N and M abundance, not direct inhibition of their activity.', [('aprotinin','DOWNREGULATES','N (nucleocapsid protein)','aprotinin','SARS-CoV-2 nucleocapsid protein'),('aprotinin','DOWNREGULATES','M (membrane protein)','aprotinin','SARS-CoV-2 membrane protein')]),
('33143316',49,4,'positive','Suppression of spike expression in the stated infected cell line.', [('Aprotinin','DOWNREGULATES','SARS-CoV-2 S','aprotinin','SARS-CoV-2 spike protein')]),
('33143316',51,0,'uncertain','Observed antiviral phenotype, but the specific TMPRSS2/spike mechanism is only probable.', []),
('33143316',51,3,'positive','Enzymatic inhibition is asserted; clinical treatment remains a suggestion.', [('SERPINA1/alpha-1 antitrypsin','INHIBITS','TMPRSS2','SERPINA1 protein','TMPRSS2 protein')]),
('33143316',52,3,'positive','Cited furin activation of spike, distinct from unspecified furin inhibitors and antiviral phenotype.', [('furin','ACTIVATES','SARS-CoV-2 S','furin protein','SARS-CoV-2 spike protein')]),
('33282147',7,0,'context','Sequence similarity does not establish a molecular interaction.', []),
('33282147',7,4,'context','Domain inventory, not interaction between distinct molecular entities.', []),
('33282147',7,5,'positive','Solved complex supports physical association of SARS-CoV (not SARS-CoV-2) spike with ACE2.', [('SARS-CoV S','BINDS','ACE2','SARS-CoV spike protein','ACE2 protein')]),
('33282147',8,4,'negated','Negated SARS-CoV-2 receptor usage; positive receptor usage of other viruses is not a named molecular pair.', []),
('33282147',8,6,'context','Engineered cell susceptibility with explicit exclusions; no specific spike/receptor binding result is asserted.', []),
('33282147',8,7,'positive','Camostat mesylate is explicitly identified as TMPRSS2 inhibitor; no direct protein edge to viral entry.', [('camostat mesylate','INHIBITS','TMPRSS2','camostat mesylate','TMPRSS2 protein')]),
('33282147',8,9,'context','Cross-analyte abundance comparison, not CD147/GRP78 regulation of ACE2.', []),
('33282147',8,10,'positive','In-vitro association is asserted; the paragraph cautions against inferring functional receptor identity.', [('CD147','BINDS','SARS-CoV-2 S','CD147 protein','SARS-CoV-2 spike protein')]),
('33282147',8,11,'uncertain','Proposed GRP78 binding is not confirmed, unlike the preceding association.', []),
('33282147',8,12,'uncertain','Explicit lack of strong receptor evidence; do not inherit confirmation from adjacent claims.', []),
('33685917',4,1,'context','Subunit composition does not assert binding between separate proteins.', []),
('33685917',4,2,'positive','SARS-CoV RBD binds human ACE2. Do not replace SARS-CoV by SARS-CoV-2 or RBD by a different viral protein.', [('receptor-binding domain (RBD)','BINDS','human angiotensin-converting enzyme 2 (ACE2)','SARS-CoV spike RBD','human ACE2 protein')]),
('33685917',4,4,'uncertain','Historical proposal of conformation, not a molecular pair assertion.', []),
('33685917',4,8,'uncertain','Speculative analogy between viruses, not a confirmed molecular interaction.', []),
('33685917',5,1,'uncertain','Hypothesized insert effect on host range; no confirmed molecular pair.', []),
('33685917',12,6,'negated','Absence of a cleavage pattern in a specific construct/cell context; not global absence of cleavage.', []),
('33685917',14,4,'context','Fusion persists without hACE2; phenotype is not evidence that spike activates ACE2.', []),
('33685917',14,8,'context','Marginal change of a fusion phenotype does not assert TMPRSS2 activation or inhibition of spike.', []),
('34094637',2,2,'positive','Spike attachment to ACE2, not binding of the whole viral species node.', [('spike proteins','BINDS','angiotensin-converting enzyme 2 (ACE2)','SARS-CoV-2 spike protein','ACE2 protein')]),
('34094637',2,3,'out_of_vocabulary','Explicit TMPRSS2 cleavage of spike; CLEAVES is not a target predicate and must not silently become INHIBITS.', []),
('34094637',2,5,'context','Joint expression as tropism indicator does not imply ACE2/TMPRSS2 interaction or mutual regulation.', []),
('34094637',3,4,'context','Study objective about expression; ACE2+ TMPRSS2+ are marker-positive cells.', []),
('34094637',4,2,'context','Relationships of cell groups and tissues, not interactions of marker proteins.', []),
('34094637',4,4,'uncertain','Hypothesis-generation objective, not validated target tissue or molecular mechanism.', []),
('32402155',4,0,'context','Analysis method, not a molecular interaction.', []),
('32402155',4,3,'uncertain','Speculative kidney injury implication, not an identified molecular pair.', []),
('32402155',6,0,'uncertain','Potential organ-level explanation; no molecular interaction.', []),
('32402155',6,1,'uncertain','Observed organotropism plus speculative clinical implications, no molecular pair.', []),
]


def main():
    assert len(ROWS) == 40
    sentences = []
    for pid, line, index, stratum, rationale, triples in ROWS:
        path = ROOT / f'part1/task4/corpus/PMID_{pid}.txt'
        text = path.read_text(encoding='utf-8')
        lines = text.splitlines(keepends=True)
        paragraph = lines[line-1].rstrip('\r\n')
        sentence = re.split(r'(?<=[.!?])\s+(?=[A-Z])', paragraph)[index]
        start = sum(map(len, lines[:line-1])) + paragraph.index(sentence)
        assert text[start:start+len(sentence)] == sentence
        relations = []
        for subject, predicate, obj, subject_identity, object_identity in triples:
            endpoints = []
            for surface, identity in ((subject, subject_identity), (obj, object_identity)):
                matches = list(re.finditer(r'(?<!\w)' + re.escape(surface) + r'(?!\w)', sentence))
                assert len(matches) == 1 or (pid == '33143316' and line == 52 and surface == 'furin' and len(matches) == 2), (pid, surface)
                a = start + matches[0].start()
                endpoints.append(dict(text=surface, start=a, end=a+len(surface), identity=identity, normalized_id=None))
            context = dict(species_id=None, cell_line_id=None, condition=None, compartment=None)
            attribution = 'cited_result'
            if pid == '33282147':
                attribution = 'review_summary'
            if pid == '33143316' and line == 49:
                attribution = 'own_experiment'
                context['condition'] = 'SARS-CoV-2 infection; aprotinin treatment'
                context['cell_line_id'] = 'Calu-3 (normalization unknown)' if index == 4 else None
                if index == 1:
                    context['condition'] += '; 20 µM; primary bronchial epithelial ALI cultures'
            relations.append(dict(subject=endpoints[0], predicate=predicate, object=endpoints[1], direction='undirected' if predicate == 'BINDS' else 'subject_to_object', negated=False, certainty='asserted', attribution=attribution, context=context))
        sentences.append(dict(sentence_id=f'PMID{pid}:L{line}:S{index}', paper_id=f'PMID:{pid}', split='test', source_path=str(path.relative_to(ROOT)), source_sha256=sha(path), line=line, paragraph=paragraph, paragraph_start=sum(map(len, lines[:line-1])), text=sentence, start=start, end=start+len(sentence), stratum=stratum, rationale=rationale, relations=relations))
    assert len({s['paper_id'] for s in sentences}) == 5
    assert not any('33898942' in s['paper_id'] for s in sentences)
    ref = dict(version='bounded-sentence-v1', annotation_source='independent task agent; machine-generated source-anchored reference; NOT human gold', human_independence=False, clinical_validity=False, prediction_scope='reported_assertions', development_excluded=['PMID:33898942'], complete_paper_annotations=False, sentence_denominator=40, target_predicates=['BINDS','INHIBITS','ACTIVATES','UPREGULATES','DOWNREGULATES'], scope='Explicit asserted molecular pairs for target predicates, including reported/cited results and abundance regulation. No inference from viral phenotype, coexpression, clinical outcome or speculative mechanism. Binding is undirected; regulatory direction is strict. Unspecified classes do not add endpoints except explicitly family-level trypsin, retained without accession.', context_policy='Full paragraph read. Null IDs mean unknown/not normalized, not verified absence. Context prose records supported own-experiment conditions; no strict normalized-context score is claimed.', sampling='Purposive, stratified by source reading; 5 papers, 40 distinct real sentences. No random-population inference. All eligible molecular pairs in these sentences for the target predicates are labeled; paragraphs are context only, not scoring units.', prefreeze_exposure='Required docs/task4.md disclosed aggregate zero held-out predictions and two development assertions before labeling. evaluate.py schema and a predicate-symbol search were read. No run prediction/annotation artifacts were opened before this freeze. Thus output-artifact separation, not fully blinded or human-independent assessment.', sentences=sentences)
    write_new(HERE/'reference.json', ref)
    freeze = dict(frozen_at_utc=datetime.now(timezone.utc).isoformat(), reference_sha256=sha(HERE/'reference.json'), builder_sha256=sha(Path(__file__)), corpus_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'part1/task4/corpus').glob('*.txt'))}, tool_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'text_mining/litmine').glob('*.py'))}, prediction_artifacts_opened=False, disclosure=ref['prefreeze_exposure'], integrity_note='Local hash receipt, not an externally timestamped or tamper-proof commitment. Do not change labels after first evaluation; use a new version for corrections.')
    write_new(HERE/'freeze.json', freeze)
    print(json.dumps({'reference_sha256':freeze['reference_sha256'],'sentences':len(sentences),'positive_sentences':sum(bool(s['relations']) for s in sentences),'relations':sum(len(s['relations']) for s in sentences)}))

if __name__ == '__main__':
    main()
