#!/usr/bin/env python3
import sys, os, hashlib
from pathlib import Path

def sha256_path(p: Path) -> str:
    h = hashlib.sha256()
    if p.is_file():
        with p.open('rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()
    # directory: walk sorted by path for determinism
    for fp in sorted([x for x in p.rglob('*') if x.is_file()]):
        h.update(fp.relative_to(p).as_posix().encode())
        with fp.open('rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
    return h.hexdigest()

def main():
    if len(sys.argv) < 2:
        print('usage: hash_directory.py <path>')
        sys.exit(1)
    p = Path(sys.argv[1])
    if not p.exists():
        print('path not found', file=sys.stderr)
        sys.exit(2)
    print(sha256_path(p))

if __name__ == '__main__':
    main()
