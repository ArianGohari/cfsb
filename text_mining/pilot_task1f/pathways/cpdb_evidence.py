"""Extrahiert die beobachteten CPDB-HTML-Tabellen offline nach stdout."""
import html
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent

def extract():
    result = {}
    for n in (15, 16, 17, 20, 21, 22):
        text = (HERE / f'request_{n:02}.body').read_text()
        records = []
        # ponytail: zugeschnitten auf diese gespeicherten Tabellen, kein allgemeiner HTML-Scraper.
        for row in re.split(r'<tr bgcolor="[^"]+">', text)[1:]:
            key = re.search(r'name="([^"]+:list)" value="(\d+)"', row)
            if not key:
                continue
            if n in (20, 21):
                title = re.search(r'"> ([^<]+)<div id="div_', row)
                if not title:
                    continue
                names = [html.unescape(title[1]).strip()]
                kind = 'interaction'
            else:
                cells = re.findall(r'<td align="left" valign="top">(.*?)</td>', row, re.S)
                names = [html.unescape(re.sub('<[^>]+>', '', x)).strip() for x in cells[0].split('<br>')]
                kind = 'pathway' if n in (15, 16) else cells[1]
            links = sorted(set((html.unescape(url), html.unescape(source)) for url, source in
                               re.findall(r'<a href="([^"]+)"[^>]*title="([^"]+)"', row)))
            records.append(dict(id=key[2], names=names, kind=kind, sources=links))
        result[str(n)] = records
    return result

if __name__ == '__main__':
    print(json.dumps(extract(), ensure_ascii=False, indent=2))
