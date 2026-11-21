from pathlib import Path

root = Path('api/static/modules')
out = Path('api/static/ts')
skip = {'jquery.min.js', 'jquery.dataTables.min.js'}
out.mkdir(parents=True, exist_ok=True)
converted = []
skipped = []

for p in sorted(root.glob('*.js')):
    if p.name in skip:
        skipped.append(p.name)
        continue
    q = out / (p.stem + '.ts')
    if q.exists():
        skipped.append(p.name)
        continue
    text = p.read_text(encoding='utf-8')
    if text.startswith('// @ts-check'):
        text = text.replace('// @ts-check\n\n', '', 1).replace('// @ts-check\r\n\r\n', '', 1)
    q.write_text(text, encoding='utf-8')
    converted.append(str(q))

print('converted', len(converted))
for item in converted:
    print(item)
print('skipped', len(skipped), ', '.join(skipped))
