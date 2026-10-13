#!/usr/bin/env python3
"""Refresh small public metadata inputs; never downloads count matrices or reads."""
import gzip, hashlib, json, urllib.request
from datetime import datetime, timezone
from pathlib import Path
DATA=Path(__file__).resolve().parents[1]/'data'
urls={}
for acc in ('GSE253904','GSE253902','GSE253903','GSM8029950','GSM8029951'):
 urls[acc+'.soft.txt']=f'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={acc}&targ=self&form=text&view=full'
urls['gene_registry.json']='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=gene&id=19,3553,7124,54209,929,2214,7097,3576,3383&retmode=json'
urls['MIMAT0000091.html']='https://www.mirbase.org/mature/MIMAT0000091'
urls['GSM8029950_RPE008_features.tsv.dup_marked.tsv.gz']='https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM8029nnn/GSM8029950/suppl/GSM8029950_RPE008_features.tsv.dup_marked.tsv.gz'
if __name__=='__main__':
 manifest=[]
 for name,url in urls.items():
  data=urllib.request.urlopen(url,timeout=45).read()
  if name.endswith('.soft.txt'): assert data.startswith((b'^SERIES',b'^SAMPLE'))
  if name.endswith('.json'): json.loads(data)
  if name.endswith('.html'): assert b'hsa-miR-33a-5p' in data
  if name.endswith('.gz'): gzip.decompress(data)
  (DATA/name).write_bytes(data)
  manifest.append(dict(file=name,url=url,retrieved_utc=datetime.now(timezone.utc).isoformat(),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
 (DATA/'GSM8029950_features.tsv').write_bytes(gzip.decompress((DATA/'GSM8029950_RPE008_features.tsv.dup_marked.tsv.gz').read_bytes()))
 (DATA/'provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(f'{len(manifest)} small source inputs refreshed')
