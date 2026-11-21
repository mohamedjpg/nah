import re
p = r'D:\tools2\dumpss\robrun\newasmbly\script.json'
pat = re.compile(rb'"([A-Za-z_][\w]*StaticFields[\w]*)"')
with open(p, 'rb') as f:
    prev = b''
    n = 0
    while n < 5:
        chunk = f.read(1 << 22)
        if not chunk:
            break
        data = prev + chunk
        for m in pat.finditer(data):
            print(m.group(1).decode())
            n += 1
            if n >= 5:
                break
        prev = data[-128:]
print('done', n)
