"""Audit RR_* macros: which are defined, which are actually referenced.

A reference is any occurrence outside a `#define <NAME>` line.
"""

import re, os, glob

root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '2_src_port'))
files = [p for p in glob.glob(os.path.join(root, '**', '*'), recursive=True)
         if os.path.isfile(p) and p.lower().endswith(('.c', '.h', '.cpp', '.hpp', '.cc'))]

TOK = re.compile(r'\bRR_(?:OFF|RVA|SF)_[A-Z0-9_]+\b')
DEF = re.compile(r'^\s*#\s*define\s+(RR_(?:OFF|RVA|SF)_[A-Z0-9_]+)')

used, defined = {}, {}
for p in files:
    rel = os.path.relpath(p, root)
    for line in open(p, encoding='utf-8', errors='ignore'):
        m = DEF.match(line)
        if m:
            defined.setdefault(m.group(1), set()).add(rel)
            line = line[m.end():]
        for t in TOK.findall(line):
            used.setdefault(t, set()).add(rel)

print('files scanned: %d | defined: %d | referenced: %d' % (len(files), len(defined), len(used)))
print()
print('=== REFERENCED BUT NOT DEFINED (%d) ===' % len(set(used) - set(defined)))
for x in sorted(set(used) - set(defined)):
    print('  %-34s %s' % (x, ','.join(sorted(used[x]))))
print()
print('=== DEFINED BUT NEVER REFERENCED (%d) ===' % len(set(defined) - set(used)))
for x in sorted(set(defined) - set(used)):
    print('  %-34s %s' % (x, ','.join(sorted(defined[x]))))
print()
print('=== DEFINED IN MULTIPLE HEADERS ===')
for x in sorted(defined):
    if len(defined[x]) > 1:
        print('  %-34s %s' % (x, ','.join(sorted(defined[x]))))
