"""Index every class/field/method in an Il2CppDumper dump.cs into JSON.

Usage:
  python index_dumpcs.py --dump <dump.cs> --out <cache.json>

Output shape:
{
  "classes": {
     "<Namespace.Type>": {
        "namespace": ..., "name": ..., "decl": ..., "line": N,
        "size": "0x123",
        "fields":  {"<name>": {"offset": 16, "decl": "...", "static": bool}},
        "methods": {"<name>": {"rva": 123, "decl": "..."}}
     }
  }
}
"""

import argparse
import json
import re
from pathlib import Path

NS_RE = re.compile(r'^// Namespace: (.*)$')
CLASS_RE = re.compile(r'^(?:\[[^\]]*\]\s*)*(?:public|private|internal|protected)?\s*'
                      r'(?:sealed\s+|abstract\s+|static\s+|readonly\s+|partial\s+)*'
                      r'(class|struct|interface|enum)\s+([^\s:{(]+)')
SIZE_RE = re.compile(r'\}\s*//\s*Size:\s*(0x[0-9A-Fa-f]+)')
RVA_RE = re.compile(r'//\s*RVA:\s*(0x[0-9A-Fa-f]+|-1)\s+Offset:\s*(0x[0-9A-Fa-f]+|-1)')
FIELD_RE = re.compile(r'^\s*(.*?)\s*;\s*//\s*(0x[0-9A-Fa-f]+)\s*$')
NAME_RE = re.compile(r'([A-Za-z_<>][\w<>\[\],\.`]*)\s*$')


def parse(path):
    classes = {}
    ns = ''
    stack = []          # [(full_name, dict)]
    pending_method = None
    lines = Path(path).read_text(encoding='utf-8', errors='ignore').split('\n')
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        m = NS_RE.match(line)
        if m:
            ns = m.group(1).strip()
            continue
        if stripped.startswith('//'):
            m = RVA_RE.search(line)
            if m and stack:
                pending_method = m.group(1)
            continue
        # class declaration
        if '// TypeDefIndex:' in line and not stack:
            m = CLASS_RE.match(line)
            if m:
                name = m.group(2)
                full = f'{ns}.{name}' if ns else name
                entry = dict(namespace=ns, name=name, kind=m.group(1),
                             decl=line.strip(), line=idx + 1,
                             size=None, fields={}, methods={})
                classes.setdefault(full, entry)
                stack.append((full, entry))
                continue
        if stack:
            if stripped.startswith('}'):
                m = SIZE_RE.search(line)
                if m:
                    stack[-1][1]['size'] = int(m.group(1), 16)
                stack.pop()
                pending_method = None
                continue
            if stripped.startswith('{'):
                continue
            m = FIELD_RE.match(line)
            if m and '// ' in line:
                decl, off = m.group(1), int(m.group(2), 16)
                nm = NAME_RE.search(decl)
                if nm:
                    fname = nm.group(1)
                    entry = stack[-1][1]
                    is_static = ' static ' in f' {decl} '
                    entry['fields'][fname] = dict(offset=off, decl=decl,
                                                  static=is_static, line=idx + 1)
                pending_method = None
                continue
            if pending_method is not None and '(' in line and not line.strip().startswith('//'):
                nm = re.search(r'([A-Za-z_<>][\w<>`\.]*)\s*\(', line)
                if nm:
                    entry = stack[-1][1]
                    entry['methods'][nm.group(1)] = dict(
                        rva=None if pending_method == '-1' else int(pending_method, 16),
                        decl=line.strip(), line=idx + 1)
                pending_method = None
    return classes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dump', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    classes = parse(a.dump)
    Path(a.out).write_text(json.dumps(classes, indent=1), encoding='utf-8')
    nf = sum(len(c['fields']) for c in classes.values())
    nm = sum(len(c['methods']) for c in classes.values())
    print(f'classes={len(classes)} fields={nf} methods={nm} -> {a.out}')


if __name__ == '__main__':
    main()
