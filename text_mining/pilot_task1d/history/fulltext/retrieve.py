"""Ein öffentlicher GET pro Aufruf, ohne Redirects oder Retries."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

BASE = Path(__file__).resolve().parent


def utc():
    return datetime.now(timezone.utc).isoformat()


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch(identifier, url, purpose):
    assert re.fullmatch(r'[a-z0-9_]+', identifier)
    assert url.startswith('https://')
    log = BASE / 'requests.jsonl'
    previous = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
    assert len(previous) < 12, 'Netzbudget ausgeschöpft'
    assert identifier not in {entry['id'] for entry in previous}, 'Keine Wiederholung'
    entry = dict(id=identifier, url=url, purpose=purpose, method='GET',
                 requested_at_utc=utc(), ordinal=len(previous) + 1,
                 plan_sha256=hashlib.sha256((BASE / 'plan.md').read_bytes()).hexdigest())
    with log.open('a') as stream:
        stream.write(json.dumps(entry, ensure_ascii=False) + '\n')
    body = None
    try:
        with build_opener(NoRedirect).open(Request(url, headers={
            'User-Agent': 'task1d-history-fulltext/1.0 (academic pilot)'}), timeout=25) as response:
            body = response.read()
            entry.update(http_status=response.status, headers=dict(response.headers), status='received')
    except HTTPError as error:
        body = error.read()
        entry.update(http_status=error.code, headers=dict(error.headers),
                     status='http_error', error=str(error))
    except (URLError, OSError) as error:
        entry.update(http_status=None, status='network_error', error=repr(error))
    entry['finished_at_utc'] = utc()
    if body is not None:
        entry['raw_ref'] = 'raw/' + identifier + '.body'
        (BASE / entry['raw_ref']).write_bytes(body)
        entry['sha256'] = hashlib.sha256(body).hexdigest()
        entry['bytes'] = len(body)
        entry['pdf_magic'] = body.startswith(b'%PDF-')
        try:
            data = json.loads(body)
        except (ValueError, UnicodeDecodeError):
            pass
        else:
            if 'hitCount' in data:
                entry['hitCount'] = data['hitCount']
                entry['retrieved_records'] = len(data.get('resultList', {}).get('result', []))
    (BASE / (identifier + '.meta.json')).write_text(json.dumps(entry, ensure_ascii=False, indent=2) + '\n')
    print(identifier, entry['status'], entry.get('http_status'), entry.get('bytes'),
          'PDF=', entry.get('pdf_magic'), entry.get('error', ''))


if __name__ == '__main__':
    if len(sys.argv) != 4:
        raise SystemExit('Usage: python3 retrieve.py ID HTTPS_URL PURPOSE')
    fetch(*sys.argv[1:])
