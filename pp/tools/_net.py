import json
d = json.load(open(r'src\pp\offsets\dump_index.json', encoding='utf-8'))

print('=== transport-ish classes ===')
kw = ('Transport', 'Socket', 'Enet', 'Channel', 'Datagram', 'Packet', 'Serializer', 'Replication')
seen = 0
for k in sorted(d):
    if any(s in k for s in kw):
        if 'UnityEngine' in k or 'System.' in k or 'Sentry' in k:
            continue
        print('  ', k)
        seen += 1
        if seen > 90:
            break
