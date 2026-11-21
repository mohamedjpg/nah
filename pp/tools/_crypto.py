import json
d = json.load(open(r'src\pp\offsets\dump_index.json', encoding='utf-8'))

print('=== crypto / cipher / encrypt classes ===')
kw = ('crypt', 'cipher', 'aes', 'chacha', 'salsa', 'hmac', 'nonce', 'xor')
for k in sorted(d):
    low = k.lower()
    if any(s in low for s in kw):
        c = d[k]
        nm = len(c['fields'])
        print('  %-72s fields=%d' % (k, nm))

print()
print('=== Kefir network classes ===')
for k in sorted(d):
    if 'Kefir' in k and ('Network' in k or 'Transport' in k or 'Serial' in k):
        print('  ', k)
