import json
d = json.load(open(r'src\pp\offsets\robrun_offsets.json', encoding='utf-8'))
sf = d.get('static_field_globals') or {}
for cls, rec in sf.items():
    print('%-24s rva=0x%X votes=%d scanned=%d cands=%s' % (
        cls, rec['rva'], rec['votes'], rec['methods_scanned'],
        [(hex(c['rva']), c['votes']) for c in rec['candidates']]))
