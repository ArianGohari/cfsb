"""Offline-Inventar der beiden lokalen SBML-Dateien; keine Simulation."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]


def inspect(path):
    data = path.read_bytes()
    root = ET.fromstring(data)
    ns = {'s': root.tag.split('}')[0][1:], 'm': 'http://www.w3.org/1998/Math/MathML'}
    model = root.find('s:model', ns)
    def elements(query):
        return model.findall(query, ns)
    def resources(element):
        return sorted({value for node in element.iter() for key, value in node.attrib.items()
                       if key == '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource'})
    species = [dict(node.attrib, resources=resources(node))
               for node in elements('s:listOfSpecies/s:species')]
    reactions = []
    for node in elements('s:listOfReactions/s:reaction'):
        reaction = dict(node.attrib)
        for kind, tag in [('reactants', 'speciesReference'), ('products', 'speciesReference'),
                          ('modifiers', 'modifierSpeciesReference')]:
            reaction[kind] = [x.attrib for x in node.findall(
                f's:listOf{kind.capitalize()}/s:{tag}', ns)]
        kinetic = node.find('s:kineticLaw', ns)
        reaction['kinetic_law_xml'] = ET.tostring(kinetic, encoding='unicode') if kinetic is not None else None
        reaction['math_identifiers'] = [x.text.strip() for x in node.findall('.//m:ci', ns)]
        reactions.append(reaction)
    rules = [ET.tostring(x, encoding='unicode') for x in elements('s:listOfRules/*')]
    events = [ET.tostring(x, encoding='unicode') for x in elements('s:listOfEvents/*')]
    ids = {s['id'] for s in species}
    assert len(ids) == len(species)
    for reaction in reactions:
        assert all(ref['species'] in ids for kind in ('reactants', 'products', 'modifiers')
                   for ref in reaction[kind])
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest(),
            'sbml': root.attrib, 'model': model.attrib,
            'model_resources': resources(model.find('s:annotation', ns)),
            'compartments': [x.attrib for x in elements('s:listOfCompartments/s:compartment')],
            'species': species, 'reactions': reactions, 'rules_xml': rules, 'events_xml': events,
            'parameters': [x.attrib for x in elements('s:listOfParameters/s:parameter')],
            'initial_assignments_xml': [ET.tostring(x, encoding='unicode') for x in elements('s:listOfInitialAssignments/*')],
            'function_definitions_xml': [ET.tostring(x, encoding='unicode') for x in elements('s:listOfFunctionDefinitions/*')]}


if __name__ == '__main__':
    models = [inspect(path) for path in sorted((ROOT / 'part1/task1/sbml').glob('*.xml'))]
    assert len(models) == 2
    print(json.dumps(models, indent=2, ensure_ascii=False))
