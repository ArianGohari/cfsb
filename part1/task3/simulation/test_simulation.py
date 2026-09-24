import hashlib,json,unittest
from pathlib import Path
import numpy as np
import roadrunner
import simulate as sim

class SemanticsTests(unittest.TestCase):
 def test_archived_sources_and_revision(self):
  for item in json.loads((sim.INPUTS/'manifest.json').read_text()):
   self.assertEqual(hashlib.sha256((sim.INPUTS/item['file']).read_bytes()).hexdigest(),item['sha256'])
  for mid in sim.CONFIG:
   path,m,a,doc=sim.audit(mid)
   self.assertEqual(a['revision'],3)
   self.assertEqual(a['read_diagnostics'],0)
   self.assertTrue(all(i['severity']=='Warning' for i in a['issues']))

 def test_sbml_initial_values_and_constants(self):
  for mid in sim.CONFIG:
   path,m,a,doc=sim.audit(mid);rr=roadrunner.RoadRunner(str(path))
   assigned={r['variable'] for r in a['rules']}|{r['symbol'] for r in a['initial_assignments']}
   for p in m.getListOfParameters():
    if p.getId() not in assigned and p.isSetValue():
     self.assertEqual(rr[p.getId()],p.getValue())
   for s in m.getListOfSpecies():
    if s.getId() not in assigned and s.isSetInitialConcentration():
     self.assertAlmostEqual(rr['['+s.getId()+']'],s.getInitialConcentration(),places=14)

 def test_delayed_switch_and_initial_assignment(self):
  path,m,a,doc=sim.audit('BIOMD0000001006')
  self.assertEqual(a['events'][0]['trigger'],'time > 10')
  self.assertEqual(a['events'][0]['delay'],'2')
  self.assertEqual(a['events'][1]['trigger'],'time > 20')
  self.assertIsNone(a['events'][1]['delay'])
  rr=roadrunner.RoadRunner(str(path));rr.integrator.relative_tolerance=1e-9
  self.assertEqual(rr['ModelValue_6'],rr['vratio'])
  self.assertEqual(rr['ModelValue_6'],15)
  data=rr.simulate(0,21,211,selections=['time','step','[IR]'])
  for time,expected in [(9.9,0),(10.1,0),(11.9,0),(12.1,1),(19.9,1),(20.1,0)]:
   row=data[round(time*10)];self.assertEqual(row[1],expected);self.assertEqual(row[2],expected)

 def test_saved_numeric_outputs_match_report(self):
  out=sim.ROOT/'results-20260924';r=json.loads((out/'validation.json').read_text())
  self.assertEqual(r['checks'],'PASS');self.assertFalse(r['biological_parameters_modified'])
  for mid,report in r['models'].items():
   data=np.genfromtxt(out/f'{mid}_timeseries.csv',delimiter=',',skip_header=1)
   self.assertEqual(len(data),report['points']);self.assertTrue(np.isfinite(data).all())
   self.assertTrue(report['repeated_run_bitwise_equal'])
   self.assertLess(report['convergence']['max_scaled_by_column_absmax'],1e-5)
  for name,sha in json.loads((out/'output-sha256.json').read_text()).items():
   self.assertEqual(hashlib.sha256((out/name).read_bytes()).hexdigest(),sha)

if __name__=='__main__':unittest.main()
