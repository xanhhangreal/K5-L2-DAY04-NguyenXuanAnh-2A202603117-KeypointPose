"""Resumable, CPU-only auto-annotation and genuine CVAT dataset export."""
from datetime import datetime, timezone, timedelta
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import time
from urllib.parse import urlencode, quote

import docker

ROOT = Path('/workspace')
WORK = ROOT / '.lab4-auto'
def log(message):
    print(datetime.now().strftime('%H:%M:%S'), message, flush=True)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2))
    temp.replace(path)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


class CVAT:
    def __init__(self):
        self.docker = docker.from_env()
        self.server = self.docker.containers.get('cvat_server')
        self.put({'bridge.py': (ROOT / 'tools/lab4_auto/bridge.py').read_bytes()})

    def put(self, files):
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode='w') as tar:
            for name, data in files.items():
                info = tarfile.TarInfo('lab4-auto/' + name)
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))
        self.server.put_archive('/tmp', buf.getvalue())

    def call(self, path, method='GET', data=None, files=None, download=False):
        arg = {'path': path, 'method': method, 'data': data or {}, 'download': download}
        if files:
            self.put({'images/' + p.name: p.read_bytes() for p in files})
            arg['files'] = ['/tmp/lab4-auto/images/' + p.name for p in files]
        self.put({'request.json': json.dumps(arg).encode()})
        # Mutating calls are never retried blindly: the checkpoint/reconciliation handles them.
        attempts = 3 if method == 'GET' else 1
        for attempt in range(attempts):
            result = self.server.exec_run(['python', '/tmp/lab4-auto/bridge.py', '/tmp/lab4-auto/request.json'], workdir='/home/django')
            output = result.output.decode(errors='replace')
            if result.exit_code == 0 and 'LAB4_RESULT=' in output:
                body = json.loads(output.rsplit('LAB4_RESULT=', 1)[1].splitlines()[0])
                if body['status'] < 400:
                    return body['data']
                error = f"CVAT {method} {path}: {body}"
            else:
                error = output[-5000:]
            if attempt + 1 < attempts:
                time.sleep(2*(attempt+1))
        raise RuntimeError(error)

    def wait(self, rq_id):
        deadline = time.monotonic() + 900
        while time.monotonic() < deadline:
            result = self.call('/api/requests/' + quote(rq_id, safe=''))
            if result['status'] == 'finished':
                return result
            if result['status'] in ('failed', 'canceled'):
                raise RuntimeError(str(result))
            time.sleep(3)
        raise TimeoutError(f'CVAT request timed out: {rq_id}')

    def get_file(self, path):
        stream, _ = self.server.get_archive(path)
        with tarfile.open(fileobj=io.BytesIO(b''.join(stream))) as tar:
            return tar.extractfile(tar.getmembers()[0]).read()


