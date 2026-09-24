"""Generate and check both Ciliberto2005 diagrams and single-page A4 PDFs."""
import json
from pathlib import Path
import subprocess
import textwrap
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
root = ET.parse(BASE / 'Ciliberto2005.xml').getroot()
for element in root.iter():
    element.tag = element.tag.split('}')[-1]
model = root.find('model')
species = {s.get('id'): s for s in model.find('listOfSpecies')}
reactions = list(model.find('listOfReactions'))
rules = {r.get('variable'): r for r in model.find('listOfRules')}
assert len(species) == 10 and len(reactions) == 21
assert set(rules) == {'IR', 'p53', 'MDM2_total', 'kd2_0'}


def refs(reaction, group, tag='speciesReference'):
    elements = reaction.findall(f'listOf{group}/{tag}')
    assert all(float(e.get('stoichiometry', '1')) == 1 for e in elements)
    return [e.get('species') for e in elements]


def quote(value):
    return json.dumps(value, ensure_ascii=False)


for kind in ('petrinetz', 'reaktionsgraph'):
    stem = BASE / f'Ciliberto2005_{kind}'
    title = 'Petrinetz' if kind == 'petrinetz' else 'Reaktionsgraph'
    legend = (
        f'Ciliberto2005 · p53/Mdm2 · {title}\n'
        'Durchgezogen: SBML-Reaktionen (Gewicht 1); gestrichelt: Einfluss auf Reaktionsrate (+/−).\n'
        'Doppelrand: durch Regel bestimmt, keine unabhängige Stoffmenge; Startwerte laut SBML (mol/L).\n'
        'p53 = p53_total − p53_ub − p53_ub_ub; MDM2_total = Mdm2_cyt + Mdm2_p_cyt + Mdm2_p_nuc/15.\n'
        'IR = ampl × step; step: 1 nach Trigger t > 10 plus 2 s Verzögerung, 0 bei t > 20.\n'
        'DNA_damage erhöht kd2_0 und damit R18. Transporte bleiben getrennte Ein-/Ausflüsse wie im SBML.'
    )
    if kind == 'reaktionsgraph':
        legend += '\n∅ = Quelle/Senke der SBML-Bilanz, nicht zwingend physischer Abbau (z. B. Transport).'
    lines = ['digraph Ciliberto2005 {',
             f'graph [rankdir=LR, bgcolor="white", fontname="Helvetica", fontsize=12, labelloc=b, label={quote(legend)}, nodesep=0.22, ranksep=0.55];',
             'node [fontname="Helvetica", fontsize=12, style=filled];',
             'edge [fontname="Helvetica", fontsize=10, color="#475569", arrowsize=0.65];']
    shape = 'circle' if kind == 'petrinetz' else 'ellipse'
    for compartment, name, color in [('Cyt', 'Cytoplasma', '#dbeafe'), ('Nuc', 'Zellkern', '#ede9fe')]:
        lines += [f'subgraph cluster_{compartment} {{', f'label="{name}"; color="#94a3b8"; style=rounded;']
        for sid, s in species.items():
            if s.get('compartment') != compartment:
                continue
            label = sid.replace('_', '\n') + '\n' + format(float(s.get('initialConcentration')), '.5g')
            lines.append(f'{quote(sid)} [shape={shape}, fillcolor="{color}", peripheries={2 if sid in rules else 1}, label={quote(label)}];')
        if kind == 'reaktionsgraph':
            for role in ('source', 'sink'):
                lines.append(f'{role}_{compartment} [shape=circle, fillcolor="#f1f5f9", label="∅"];')
        lines.append('}')
    expected_edges = []
    for number, r in enumerate(reactions, 1):
        rid = r.get('id')
        assert r.get('reversible') == 'false'
        inputs, outputs = refs(r, 'Reactants'), refs(r, 'Products')
        assert len(inputs) <= 1 and len(outputs) <= 1
        name = '\n'.join(textwrap.wrap(r.get('name').replace('_', ' '), width=21))
        label = f'R{number}\n{name}'
        compartment = species[(inputs or outputs)[0]].get('compartment')
        if kind == 'petrinetz':
            lines.append(f'{quote(rid)} [shape=box, fillcolor="#f1f5f9", label={quote(label)}];')
            pairs = [(s, rid) for s in inputs] + [(rid, s) for s in outputs]
        else:
            pairs = [(inputs[0] if inputs else f'source_{compartment}', outputs[0] if outputs else f'sink_{compartment}')]
        for index, (a, b) in enumerate(pairs):
            eid = f'{rid}_{index}'
            attrs = f'id={quote(eid)}, tooltip={quote(rid)}'
            if kind == 'reaktionsgraph':
                attrs += f', label={quote(label)}'
            lines.append(f'{quote(a)} -> {quote(b)} [{attrs}];')
            expected_edges.append((a, b, eid))
        modifiers = refs(r, 'Modifiers', 'modifierSpeciesReference')
        # This dependency is indirect through an assignment rule, not an SBML modifier.
        if rid == 'Mdm2_p_nuc_degradation':
            modifiers.append('DNA_damage')
        for modifier in modifiers:
            negative = rid == 'Mdm2_cyt_phosphorylation'
            sign, color = ('−', '#b91c1c') if negative else ('+', '#15803d')
            target = rid if kind == 'petrinetz' else (outputs or inputs)[0]
            eid = f'influence_{rid}_{modifier}'
            lines.append(f'{quote(modifier)} -> {quote(target)} [id={quote(eid)}, style=dashed, constraint=false, color="{color}", fontcolor="{color}", label="{sign} R{number}", tooltip={quote("Einfluss auf Rate: " + rid)}];')
            expected_edges.append((modifier, target, eid))
    lines.append('}')
    stem.with_suffix('.dot').write_text('\n'.join(lines) + '\n')
    subprocess.run(['dot', '-Tsvg', str(stem.with_suffix('.dot')), '-o', str(stem.with_suffix('.svg'))], check=True)
    graph = json.loads(subprocess.check_output(['dot', '-Tjson', str(stem.with_suffix('.dot'))]))
    nodes = {n['_gvid']: n for n in graph['objects']}
    actual = [(nodes[e['tail']]['name'], nodes[e['head']]['name'], e['id']) for e in graph['edges']]
    assert sorted(actual) == sorted(expected_edges)
    assert set(species) <= {n['name'] for n in nodes.values()}
    boxes = [n for n in nodes.values() if n.get('shape') == 'box']
    assert len(boxes) == (21 if kind == 'petrinetz' else 0)
    svg = ET.parse(stem.with_suffix('.svg')).getroot()
    assert svg.tag == '{http://www.w3.org/2000/svg}svg'
    subprocess.run(['rsvg-convert', '-f', 'pdf', '-a', '-w', '277mm', '-h', '190mm', '--page-width', '297mm', '--page-height', '210mm', '--left', '10mm', '--top', '10mm', '-o', str(BASE / f'Ciliberto2005_{kind}_A4.pdf'), str(stem.with_suffix('.svg'))], check=True)
    info = subprocess.check_output(['pdfinfo', str(BASE / f'Ciliberto2005_{kind}_A4.pdf')], text=True)
    fields = dict(line.split(':', 1) for line in info.splitlines() if ':' in line)
    assert fields['Pages'].strip() == '1'
    dimensions = fields['Page size'].split()
    assert abs(float(dimensions[0]) - 841.89) < 1 and abs(float(dimensions[2]) - 595.28) < 1
    print(f'PASS {kind}: 10 Spezies, 21 Reaktionen, {len(actual)} Kanten geprüft; SVG gültig; PDF 1 Seite DIN A4 quer.')
