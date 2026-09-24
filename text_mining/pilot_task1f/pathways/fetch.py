"""Ein öffentlicher GET pro URL; keine Redirects, Retries oder Credentials."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
log = HERE / 'requests.jsonl'
for url in sys.argv[1:]:
    parsed = urlsplit(url)
    assert parsed.scheme in ('http', 'https') and not parsed.username and not parsed.password
    rows = log.read_text().splitlines() if log.exists() else []
    amendment = json.loads((HERE / 'amendment.json').read_text())
    assert amendment['original_limit'] == 14 and amendment['additional_limit'] == 8
    assert amendment['total_limit'] == 22
    assert len(rows) < amendment['total_limit'], 'Request-Budget erschöpft'
    n = len(rows) + 1
    stem = f'request_{n:02}'
    body, headers, stderr = [HERE / (stem + ext) for ext in ('.body', '.headers', '.stderr')]
    body.touch(exist_ok=False)
    command = ['curl', '-q', '--silent', '--show-error', '--max-time', '45',
               '--proto', '=http,https', '--dump-header', str(headers),
               '--output', str(body), '--write-out', '%{json}', url]
    start = dt.datetime.now(dt.timezone.utc).isoformat()
    result = subprocess.run(command, capture_output=True)
    stderr.write_bytes(result.stderr)
    record = dict(number=n, utc_start=start, utc_end=dt.datetime.now(dt.timezone.utc).isoformat(),
                  url=url, exit_code=result.returncode, curl=json.loads(result.stdout),
                  body=body.name, headers=headers.name, stderr=stderr.name,
                  body_sha256=hashlib.sha256(body.read_bytes()).hexdigest(), command=command)
    with log.open('a') as out:
        out.write(json.dumps(record) + '\n')
    print(n, record['curl']['http_code'], result.returncode, url, len(body.read_bytes()))
