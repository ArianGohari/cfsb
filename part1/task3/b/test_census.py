import csv
import json
import unittest
from collections import Counter
from census import ROOT, extract, normalize
from verify_api import model_annotations


class CensusTests(unittest.TestCase):
    def test_normalization(self):
        for uri in ('http://identifiers.org/kegg.pathway/hsa04110',
                    'https://identifiers.org/kegg.pathway:hsa04110',
                    'urn:miriam:kegg.pathway:hsa04110'):
            self.assertEqual(normalize({'uri': uri}), ('kegg.pathway', 'hsa04110'))
        self.assertEqual(normalize({'uri': 'urn:miriam:pw:PW%3A0000001'}), ('pw', 'PW:0000001'))
        self.assertEqual(normalize({'uri': 'urn:miriam:pw:+PW%3A0001362'}), ('pw', 'PW:0001362'))
        self.assertEqual(normalize({'uri': 'https://identifiers.org/reactome/REACT_152'}), ('reactome', 'REACT_152'))
        self.assertEqual(normalize({'uri': 'https://identifiers.org/reactome/R-HSA-164017'}), ('reactome', 'R-HSA-164017'))
        for uri in ('http://identifiers.org/go/GO:0007166', 'http://identifiers.org/kegg.reaction/R00001', 'https://example.org/reactome/REACT_152'):
            self.assertIsNone(normalize({'uri': uri}))
        with self.assertRaises(ValueError):
            normalize({'uri': 'https://identifiers.org/pw/not-an-id'})

    def test_snapshot_integrity(self):
        if not (ROOT / 'inventory.csv').exists():
            self.skipTest('Run the census first')
        def rows(name):
            with (ROOT / name).open() as handle:
                return list(csv.DictReader(handle))
        inventory = rows('inventory.csv')
        pairs = rows('model_pathway_pairs.csv')
        manifest = json.loads((ROOT / 'snapshot.json').read_text())
        ids = {row['model_id'] for row in inventory}
        self.assertEqual(len(ids), manifest['model_count'])
        self.assertEqual(len(ids), len(inventory))
        self.assertTrue(manifest['enumeration_stable'])
        self.assertFalse(any(row['status'] in ('error', 'annotations_unavailable') for row in inventory))
        self.assertEqual(len(pairs), len({(r['model_id'], r['namespace'], r['pathway_id']) for r in pairs}))
        self.assertLessEqual({r['model_id'] for r in pairs}, ids)
        counts = Counter(row['model_id'] for row in pairs)
        for row in inventory:
            self.assertEqual(int(row['pathway_count']), counts[row['model_id']])
        for namespace in manifest['pair_counts']:
            selected = [r for r in pairs if r['namespace'] == namespace]
            model_counts = Counter(r['model_id'] for r in selected)
            pathway_counts = Counter(r['pathway_id'] for r in selected)
            for row in rows('model_ranking.csv'):
                if row['namespace'] == namespace:
                    self.assertEqual(int(row['pathway_count']), model_counts[row['model_id']])
            for row in rows('pathway_ranking.csv'):
                if row['namespace'] == namespace:
                    self.assertEqual(int(row['model_count']), pathway_counts[row['pathway_id']])

    def test_sbml_model_scope(self):
        raw = b'''<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core"
          xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
          xmlns:bqbiol="http://biomodels.net/biology-qualifiers/">
          <model metaid="m"><annotation><rdf:RDF><rdf:Description rdf:about="#m">
          <bqbiol:is><rdf:Bag><rdf:li rdf:resource="http://identifiers.org/kegg.pathway/hsa04110"/></rdf:Bag></bqbiol:is>
          </rdf:Description></rdf:RDF></annotation><listOfSpecies><species metaid="s">
          <annotation><rdf:RDF><rdf:Description rdf:about="#s"><bqbiol:is><rdf:Bag>
          <rdf:li rdf:resource="http://identifiers.org/reactome/REACT_152"/>
          </rdf:Bag></bqbiol:is></rdf:Description></rdf:RDF></annotation>
          </species></listOfSpecies></model></sbml>'''
        self.assertEqual(model_annotations(raw), {('bqbiol:is', 'http://identifiers.org/kegg.pathway/hsa04110')})

    def test_scope_duplicates_and_missing(self):
        annotation = dict(uri='http://identifiers.org/kegg.pathway/hsa04110', qualifier='bqbiol:isVersionOf')
        data = dict(publicationId='BIOMD0000000003', modelLevelAnnotations=[annotation, annotation], species=[dict(annotation=annotation)])
        result = extract(data, 'BIOMD0000000003')
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[('kegg.pathway', 'hsa04110')]), 2)
        data['modelLevelAnnotations'] = []
        self.assertEqual(extract(data, 'BIOMD0000000003'), {})
        del data['modelLevelAnnotations']
        self.assertIsNone(extract(data, 'BIOMD0000000003'))
        with self.assertRaises(AssertionError):
            extract(data, 'BIOMD0000000004')


if __name__ == '__main__':
    unittest.main()
