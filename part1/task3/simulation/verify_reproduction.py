#!/usr/bin/env python3
"""Verify archived source bytes and regenerate simulation artifacts in isolation."""
from pathlib import Path
import hashlib,json,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results-20260924';TASK=ROOT.parent
for item in json.loads((OUT/'snapshot-files.json').read_text()):
 assert hashlib.sha256((TASK/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
reference=json.loads((OUT/'output-sha256.json').read_text())
with tempfile.TemporaryDirectory(prefix='.replay-',dir=ROOT) as tmp:
 subprocess.run([sys.executable,str(ROOT/'simulate.py'),'--output',tmp],check=True)
 regenerated=json.loads((Path(tmp)/'output-sha256.json').read_text())
 assert reference==regenerated,'Reproduced CSV/SVG/PNG artifact bytes changed'
 assert (Path(tmp)/'validation.json').read_bytes()==(OUT/'validation.json').read_bytes()
report=dict(status='PASS',archived_files_verified=len(json.loads((OUT/'snapshot-files.json').read_text())),reproduced_artifact_count=len(reference),all_artifacts_byte_equal=True,validation_report_byte_equal=True)
(OUT/'reproduction.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
