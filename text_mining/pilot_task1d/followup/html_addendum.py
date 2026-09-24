"""Fetch one known public HTML page or derive a readable offline copy."""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import fulltext

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'html_raw'
URL = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC3466558/'


class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ['script', 'style']:
            self.skip += 1
        if tag in ['p', 'h1', 'h2', 'h3', 'h4', 'section', 'li', 'tr']:
            self.parts.append('\n\n')

    def handle_endtag(self, tag):
        if tag in ['script', 'style']:
            self.skip -= 1
        if tag in ['p', 'h1', 'h2', 'h3', 'h4', 'section', 'li', 'tr']:
            self.parts.append('\n\n')

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def normalized_blocks(body):
    parser = Text()
    parser.feed(body)
    return [' '.join(x.split()) for x in ''.join(parser.parts).split('\n\n') if x.strip()]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['fetch', 'text'])
    args = parser.parse_args()
    if args.action == 'fetch':
        RAW.mkdir(exist_ok=True)
        snapshot = RAW / 'prior_artifacts.json'
        if not snapshot.exists():
            paths = list((ROOT / 'raw').iterdir()) + list((ROOT / 'fulltext_raw').iterdir())
            snapshot.write_text(json.dumps({str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}, indent=2) + '\n')
        assert len(list(RAW.glob('*.meta.json'))) < 3
        fulltext.RAW = RAW
        fulltext.fetch('gaddameedhi_html', URL)
    else:
        meta = json.loads((RAW / 'gaddameedhi_html.meta.json').read_text())
        assert meta['http_status'] == 200
        body = (RAW / 'gaddameedhi_html.response').read_text()
        assert 'Effect of circadian clock mutations' in body
        blocks = normalized_blocks(body)
        (RAW / 'gaddameedhi_html.txt').write_text('\n\n'.join(f'[{i}] {x}' for i, x in enumerate(blocks, 1)) + '\n')
        print('blocks=', len(blocks))
