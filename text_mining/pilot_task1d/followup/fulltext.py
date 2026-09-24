"""Public full-text requests, capped at 12; no redirects or retries."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'fulltext_raw'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch(name, url):
    RAW.mkdir(exist_ok=True)
    snapshot = RAW / 'previous_raw_hashes.json'
    if not snapshot.exists():
        snapshot.write_text(json.dumps({p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT / 'raw').iterdir()) if p.is_file()}, indent=2) + '\n')
    meta_path = RAW / (name + '.meta.json')
    if meta_path.exists():
        assert json.loads(meta_path.read_text())['url'] == url
        return
    assert len(list(RAW.glob('*.meta.json'))) < 12, 'Request budget exhausted'
    start = dt.datetime.now(dt.timezone.utc).isoformat()
    status, error, headers = None, '', {}
    try:
        opener = urllib.request.build_opener(NoRedirect)
        with opener.open(urllib.request.Request(url, headers={'User-Agent': 'task1d-public-fulltext-review/1.0'}), timeout=40) as response:
            status, body, headers = response.status, response.read(), dict(response.headers)
    except urllib.error.HTTPError as exc:
        status, body, error, headers = exc.code, exc.read(), str(exc), dict(exc.headers)
    except (urllib.error.URLError, TimeoutError) as exc:
        body, error = b'', str(exc)
    path = RAW / (name + '.response')
    path.write_bytes(body)
    meta = dict(name=name, url=url, started_utc=start, ended_utc=dt.datetime.now(dt.timezone.utc).isoformat(), http_status=status, error=error, headers=headers, raw_ref=str(path.relative_to(ROOT)), bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    meta_path.write_text(json.dumps(meta, indent=2) + '\n')
    print(name, status, len(body), error)


def text(name):
    data = ET.fromstring((RAW / (name + '.response')).read_bytes())
    lines = []
    # ponytail: linear text view; original XML remains authoritative for structure.
    if data.tag == 'article':
        for node in data.iter():
            if node.tag in ['article-id', 'article-title', 'title', 'p', 'caption', 'table-wrap-foot']:
                lines.append(' '.join(''.join(node.itertext()).split()))
    else:
        for passage in data.findall('.//passage'):
            kind = ';'.join((x.get('key', '') + '=' + (x.text or '')) for x in passage.findall('infon'))
            lines.append(kind + '\n' + (passage.findtext('text') or ''))
    assert lines, 'No article text found'
    (RAW / (name + '.txt')).write_text('\n\n'.join(f'[{i}] {line}' for i, line in enumerate(lines, 1)) + '\n')
    print(name, 'text blocks=', len(lines))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['fetch', 'text'])
    parser.add_argument('name')
    parser.add_argument('url', nargs='?')
    args = parser.parse_args()
    assert args.name.replace('_', '').isalnum()
    if args.action == 'fetch':
        assert args.url and args.url.startswith(('https://www.ebi.ac.uk/europepmc/', 'https://www.ncbi.nlm.nih.gov/pmc/', 'https://www.ncbi.nlm.nih.gov/research/', 'https://pmc.ncbi.nlm.nih.gov/tools/', 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'))
        fetch(args.name, args.url)
    else:
        text(args.name)
