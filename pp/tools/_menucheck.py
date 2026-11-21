import io, re, sys

p = r"D:\tools2\dumpss\robrun\src\pp\2_src_port\menu.html"
s = io.open(p, encoding="utf-8").read()

i = s.index("<script>")
j = s.index("</script>")
js = s[i + 8:j]

print("js braces  ", js.count("{") - js.count("}"))
print("js parens  ", js.count("(") - js.count(")"))
print("js brackets", js.count("[") - js.count("]"))
print("sections   ", s.count("<section"), s.count("</section>"))
print("articles   ", s.count("<article"), s.count("</article>"))
print("divs       ", s.count("<div"), s.count("</div>"))

# Every id referenced by $("x") in JS must exist in the HTML.
ids = set(re.findall(r'\bid="([^"]+)"', s))
refs = set(re.findall(r'\$\("([^"]+)"\)', js))
missing = sorted(r for r in refs if r not in ids)
print("missing ids", missing)

# data-tab values must match section ids (that is how activate() pairs them).
tabs = re.findall(r'data-tab="([^"]+)"', s)
print("tabs       ", tabs)
print("orphan tabs", [t for t in tabs if 'id="%s"' % t not in s])

# CSS custom properties used vs declared.
declared = set(re.findall(r'^\s*(--[a-z0-9-]+)\s*:', s, re.M))
used = set(re.findall(r'var\((--[a-z0-9-]+)\)', s))
print("undeclared vars", sorted(used - declared))
