#!/usr/bin/env python3
"""Simulate two byte-fixed SBML models without modifying biological parameters."""
import argparse
from collections import Counter
import csv, hashlib, importlib.metadata, json, platform, sys
from pathlib import Path
import libsbml
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import roadrunner
from scipy.integrate import solve_ivp
from scipy.signal import find_peaks

ROOT=Path(__file__).resolve().parent
INPUTS=ROOT/'inputs'
EXPECTED={'BIOMD0000000170':'ec4a5b68041d448cf34b82af4fc26a3b2e5c68b57b04b29a2cd28ad557bd7898','BIOMD0000001006':'c412f691fb6dad00ebb96148ebdc52148b1f47949ad1dd139a0ea99c6ec6b389'}
CONFIG={'BIOMD0000000170':dict(end=720.0,points=14401,time_unit='h',concentration_unit='nmol/l'),'BIOMD0000001006':dict(end=1200.0,points=12001,time_unit='s (SBML)',concentration_unit='mol/l (SBML; abstract model values)')}
plt.rcParams.update({'font.size':10,'svg.hashsalt':'task3-fixed-sbml','figure.dpi':150})

def save_json(path,obj):path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def formula(math):return libsbml.formulaToL3String(math) if math is not None else None

def audit(mid):
 p=INPUTS/f'{mid}_current_0.xml';raw=p.read_bytes()
 assert hashlib.sha256(raw).hexdigest()==EXPECTED[mid]
 doc=libsbml.readSBMLFromString(raw.decode());nread=doc.getNumErrors();doc.checkConsistency();m=doc.getModel()
 issues=[dict(id=e.getErrorId(),severity=e.getSeverityAsString(),category=e.getCategoryAsString(),message=e.getMessage()) for e in (doc.getError(i) for i in range(doc.getNumErrors()))]
 assert m and not any(doc.getError(i).getSeverity()>=libsbml.LIBSBML_SEV_ERROR for i in range(doc.getNumErrors()))
 metadata=json.loads((INPUTS/f'{mid}_metadata.raw').read_text())
 semantics=dict(model=mid,sha256=EXPECTED[mid],revision=max(r['version'] for r in metadata['history']['revisions']),level=doc.getLevel(),version=doc.getVersion(),read_diagnostics=nread,issues=issues,units=[dict(id=u.getId(),definition=libsbml.UnitDefinition.printUnits(u)) for u in m.getListOfUnitDefinitions()],compartments=[dict(id=c.getId(),size=c.getSize(),constant=c.getConstant()) for c in m.getListOfCompartments()],species=[dict(id=s.getId(),name=s.getName(),initial_kind='concentration' if s.isSetInitialConcentration() else 'amount',initial_value=s.getInitialConcentration() if s.isSetInitialConcentration() else s.getInitialAmount(),boundary=s.getBoundaryCondition(),constant=s.getConstant(),has_only_substance_units=s.getHasOnlySubstanceUnits()) for s in m.getListOfSpecies()],parameters=[dict(id=p.getId(),value=p.getValue() if p.isSetValue() else None,units=p.getUnits(),constant=p.getConstant()) for p in m.getListOfParameters()],rules=[dict(variable=r.getVariable(),type='assignment' if r.isAssignment() else 'other',formula=formula(r.getMath())) for r in m.getListOfRules()],initial_assignments=[dict(symbol=a.getSymbol(),formula=formula(a.getMath())) for a in m.getListOfInitialAssignments()],events=[dict(id=e.getId(),trigger=formula(e.getTrigger().getMath()),delay=formula(e.getDelay().getMath()) if e.isSetDelay() else None,assignments=[dict(variable=a.getVariable(),formula=formula(a.getMath())) for a in e.getListOfEventAssignments()]) for e in m.getListOfEvents()],function_definitions=[dict(id=f.getId(),formula=formula(f.getMath())) for f in m.getListOfFunctionDefinitions()])
 return p,m,semantics,doc

def run_cvode(path,model,cfg,tight=False):
 rr=roadrunner.RoadRunner(str(path));rr.setIntegrator('cvode')
 rr.integrator.relative_tolerance=1e-11 if tight else 1e-9
 rr.integrator.absolute_tolerance=1e-14 if tight else 1e-12
 rr.integrator.stiff=True
 rr.integrator.maximum_num_steps=100000
 species=[s.getId() for s in model.getListOfSpecies()]
 extra=['y5_y6_y7','trans_per2_cry','trans_Bmal1'] if 'y1' in species else ['step','ModelValue_6','kd2_0']
 selections=['time']+['['+s+']' for s in species]+extra
 rr.timeCourseSelections=selections
 values=rr.simulate(0,cfg['end'],cfg['points'])
 return np.asarray(values).copy(),list(values.colnames),str(rr.integrator)

def save_csv(path,data,columns):np.savetxt(path,data,delimiter=',',header=','.join(columns),comments='',fmt='%.17g')
def series(data,columns,key):return data[:,columns.index(key)]
def peaks(data,columns,key,start=0):
 t=data[:,0];y=series(data,columns,key);idx,_=find_peaks(y,prominence=0.05);idx=idx[t[idx]>=start]
 # Parabolic interpolation refines the sampled maximum; no extra biological parameter.
 refined=[]
 for k in idx:
  offset=.5*(y[k-1]-y[k+1])/(y[k-1]-2*y[k]+y[k+1])
  refined.append(float(t[k]+offset*(t[k+1]-t[k])))
 return idx,np.array(refined)

def scaled_error(a,b):
 scale=np.maximum(np.max(np.abs(b[:,1:]),axis=0),1e-12)
 return dict(max_absolute=float(np.max(np.abs(a[:,1:]-b[:,1:]))),max_scaled_by_column_absmax=float(np.max(np.abs(a[:,1:]-b[:,1:])/scale)))

def clock_independent(path,model,baseline,columns):
 assert all(c.getSize()==1 and c.getConstant() for c in model.getListOfCompartments())
 assert model.getNumEvents()==0 and all(r.isAssignment() for r in model.getListOfRules())
 rr=roadrunner.RoadRunner(str(path));ids=list(rr.model.getFloatingSpeciesIds())
 y0=np.array(rr.model.getFloatingSpeciesConcentrations())
 def rhs(t,y):
  rr.model.setTime(t);rr.model.setFloatingSpeciesConcentrations(y)
  return np.array(rr.getRatesOfChange())
 sol=solve_ivp(rhs,(0,baseline[-1,0]),y0,t_eval=baseline[:,0],method='DOP853',rtol=1e-10,atol=1e-12)
 assert sol.success
 compare=np.column_stack([baseline[:,0]]+[series(baseline,columns,'['+s+']') for s in ids])
 result=np.column_stack([sol.t,sol.y.T])
 return result,['time']+['['+s+']' for s in ids],dict(method='SciPy DOP853; same RoadRunner-compiled SBML RHS',function_evaluations=sol.nfev,**scaled_error(result,compare))

def plot_clock(data,cols,out):
 fig,axes=plt.subplots(2,1,figsize=(9,6),layout='constrained')
 for key,label in [('[y1]','Per2/Cry-mRNA'),('[y3]','PER2/CRY nukleär'),('[y4]','Bmal1-mRNA'),('[y7]','BMAL1 aktiv'),('y5_y6_y7','BMAL1 gesamt')]:
  axes[0].plot(data[:,0],series(data,cols,key),label=label,lw=1.15)
  axes[1].plot(data[:,0],series(data,cols,key),label=label,lw=1.3)
 axes[0].set(xlim=(0,720),ylabel='Konzentration [nmol/l]',title='BIOMD0000000170: unverändertes SBML, CVODE')
 axes[1].set(xlim=(100,150),ylim=(0,3.6),xlabel='Zeit [h]',ylabel='Konzentration [nmol/l]',title='Fenster der BioModels-Kurationsabbildung (Fig. 3A)')
 axes[0].legend(ncol=3,fontsize=8,loc='upper right')
 for ax in axes:ax.grid(alpha=.2)
 fig.savefig(out/'clock.svg',metadata={'Date':None});fig.savefig(out/'clock.png');plt.close(fig)

def plot_p53(data,cols,out):
 fig,axes=plt.subplots(2,2,figsize=(10,6),layout='constrained')
 groups=[([('[p53_total]','p53 gesamt'),('[Mdm2_p_nuc]','MDM2 nukleär')],'p53 und nukleäres MDM2','Modellkonzentration [mol/l]'),([('[Mdm2_cyt]','MDM2 cyt'),('[Mdm2_p_cyt]','MDM2-P cyt')],'Cytoplasmatisches MDM2','Modellkonzentration [mol/l]'),([('[DNA_damage]','DNA-Schaden')],'DNA-Schadensvariable','Modellkonzentration [mol/l]'),([('kd2_0','kd2_0')],'Zugewiesener MDM2-Abbauparameter','Parameterwert (Einheit nicht deklariert)')]
 for ax,(signals,title,ylabel) in zip(axes.ravel(),groups):
  for key,label in signals:ax.plot(data[:,0],series(data,cols,key),label=label,lw=1.3)
  ax.set(xlim=(0,1200),xlabel='Zeit [s gemäß SBML]',ylabel=ylabel,title=title);ax.grid(alpha=.2);ax.legend(fontsize=8)
 fig.suptitle('BIOMD0000001006: Originalparameter und Originalereignisse',fontsize=12)
 fig.savefig(out/'p53_mdm2.svg',metadata={'Date':None});fig.savefig(out/'p53_mdm2.png');plt.close(fig)

def main(out):
 out.mkdir(parents=True,exist_ok=True)
 report=dict(environment=dict(python=platform.python_version(),platform=platform.platform(),machine=platform.machine(),packages={n:importlib.metadata.version(n) for n in ['libroadrunner','python-libsbml','numpy','scipy','matplotlib']}),date='2026-09-24',biological_parameters_modified=False,models={})
 for mid,cfg in CONFIG.items():
  path,m,semantics,doc=audit(mid)
  save_json(out/f'{mid}_semantics.json',semantics)
  a,cols,solver=run_cvode(path,m,cfg);b,_,_=run_cvode(path,m,cfg,tight=True);repeat,_,_=run_cvode(path,m,cfg)
  assert np.isfinite(a).all() and np.isfinite(b).all()
  species_cols=[cols.index('['+s.getId()+']') for s in m.getListOfSpecies()]
  assert np.min(a[:,species_cols])>=-1e-10
  assert np.array_equal(a,repeat),'Same-environment repeated run differs'
  convergence=scaled_error(a,b);assert convergence['max_scaled_by_column_absmax']<1e-5,convergence
  save_csv(out/f'{mid}_timeseries.csv',a,cols);save_csv(out/f'{mid}_tight.csv',b,cols)
  metrics=dict(**cfg,sha256=EXPECTED[mid],revision=semantics['revision'],solver=solver,repeated_run_bitwise_equal=True,convergence=convergence,min_species_concentration=float(np.min(a[:,species_cols])),columns=cols,libsbml_warning_counts=dict(Counter(str(x['id']) for x in semantics['issues'])))
  if mid.endswith('0170'):
   idx,pt=peaks(a,cols,'[y1]',start=240);periods=np.diff(pt)
   assert len(pt)>10 and np.all((periods>23)&(periods<25))
   assert np.max(np.abs(series(a,cols,'y5_y6_y7')-sum(series(a,cols,'['+s+']') for s in ('y5','y6','y7'))))<1e-12
   independent,icols,icheck=clock_independent(path,m,a,cols)
   assert icheck['max_scaled_by_column_absmax']<1e-5,icheck
   save_csv(out/f'{mid}_dop853.csv',independent,icols)
   metrics.update(peak_times_after_240h=pt.tolist(),period_mean_h=float(periods.mean()),period_sd_h=float(periods.std()),published_period_h=23.8,period_difference_h=float(periods.mean()-23.8),independent_integrator=icheck)
   plot_clock(a,cols,out)
  else:
   p53=series(a,cols,'[p53]');total=series(a,cols,'[p53_total]')
   p53_error=float(np.max(np.abs(p53-(total-series(a,cols,'[p53_ub]')-series(a,cols,'[p53_ub_ub]')))))
   mdm_error=float(np.max(np.abs(series(a,cols,'[MDM2_total]')-(series(a,cols,'[Mdm2_cyt]')+series(a,cols,'[Mdm2_p_cyt]')+series(a,cols,'[Mdm2_p_nuc]')/15))))
   assert p53_error<1e-12 and mdm_error<1e-12
   assert np.all(series(a,cols,'ModelValue_6')==15)
   samples=[]
   for t,expected in [(9.9,0),(10.1,0),(11.9,0),(12.1,1),(19.9,1),(20.1,0)]:
    k=int(round(t/(cfg['end']/(cfg['points']-1))))
    assert series(a,cols,'step')[k]==expected and series(a,cols,'[IR]')[k]==expected
    samples.append(dict(time=float(a[k,0]),step=float(series(a,cols,'step')[k]),IR=float(series(a,cols,'[IR]')[k])))
   idx,pt=peaks(a,cols,'[p53_total]')
   metrics.update(p53_peak_times=pt.tolist(),p53_sampled_peak_values=total[idx].tolist(),dna_damage_initial=float(series(a,cols,'[DNA_damage]')[0]),dna_damage_max=float(series(a,cols,'[DNA_damage]').max()),dna_damage_final=float(series(a,cols,'[DNA_damage]')[-1]),p53_final=float(total[-1]),assignment_rule_residual_p53=p53_error,assignment_rule_residual_mdm2=mdm_error,event_samples=samples,initial_assignment_value=15.0)
   assert len(pt)==2
   plot_p53(a,cols,out)
  report['models'][mid]=metrics
  print(mid,'PASS',convergence,flush=True)
 report['checks']='PASS'
 save_json(out/'validation.json',report)
 hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.iterdir()) if f.suffix in ('.csv','.svg','.png')}
 save_json(out/'output-sha256.json',hashes)
 return report

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=ROOT/'results-20260924')
 main(parser.parse_args().output)
