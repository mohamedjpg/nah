import re

p = r'D:\tools2\dumpss\robrun\newasmbly\script.json'
pat = re.compile(rb'\n  "([A-Za-z_]+)"\s*:')
with open(p, 'rb') as f:
    prev = b''
    hits = []
    while True:
        chunk = f.read(1 << 22)
        if not chunk:
            break
        data = prev + chunk
        for m in pat.finditer(data):
            hits.append((m.start(), m.group(1).decode()))
        prev = data[-64:]
print(len(hits))
for off, name in hits:
    print(off, name)
