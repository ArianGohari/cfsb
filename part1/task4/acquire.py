"""Task4 bounded public acquisition; no screening or LLM extraction."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'text_mining'))
from litmine import sources

ROOT = Path(__file__).resolve().parent
CONFIG = {'offline': False, 'network': {'timeout': 40, 'max_attempts': 2},
          'search': {'source': 'europepmc', 'queries': [
              '(TITLE_ABS:"Caco-2" OR TITLE_ABS:Caco2) AND (TITLE_ABS:"SARS-CoV-2" OR TITLE_ABS:COVID-19) AND (TITLE_ABS:proteomics OR TITLE_ABS:proteomic OR TITLE_ABS:proteome)'
          ], 'max_records': 100, 'page_size': 100, 'mode': 'task4_pilot'}}

def save(name, obj):
    (ROOT / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')

if __name__ == '__main__':
    save('config.json', CONFIG)
    result = sources.search(CONFIG, ROOT)
    save('search.json', result)
    print([(s['reported_hits'], s['retrieved_records'], s['completion_status']) for s in result['searches']], flush=True)
    out = []
    for p in result['papers']:
        r = sources.retrieve(p, CONFIG, ROOT)
        out.append({'paper_id': p['paper_id'], **r})
        if r['document']:
            folder = ROOT / 'corpus'
            folder.mkdir(exist_ok=True)
            (folder / (p['paper_id'].replace(':', '_').replace('/', '_') + '.txt')).write_text(r['document']['text'])
        print(p['paper_id'], p['title'], r['reason'], flush=True)
    save('retrieval.json', out)
