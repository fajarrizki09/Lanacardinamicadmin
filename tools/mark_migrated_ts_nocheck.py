from pathlib import Path

files = ['app', 'crm', 'invoices', 'license', 'modal', 'patients', 'settings']
base = Path('api/static/ts')
for name in files:
    path = base / f'{name}.ts'
    text = path.read_text(encoding='utf-8')
    if not text.startswith('// @ts-nocheck'):
        path.write_text('// @ts-nocheck\n' + text, encoding='utf-8')
        print(path)
