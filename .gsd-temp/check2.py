from pathlib import Path

t = Path('docs/DEPLOY.md').read_text(encoding='utf-8')
print('has_2012_row_em', '| 2026-11-12 | Render — `/api/v1/health` |' in t)
print('has_2012_row_hyphen', '| 2026-11-12 | Render - `/api/v1/health` |' in t)
print('rollback exact', 'rollback por reversão de env/config/domínio' in t)
for line in t.splitlines():
    if line.startswith('| 2026-11-12 | Render'):
        print('LINE2012:', line[:140])
for line in t.splitlines():
    if 'rollback por revers' in line.lower():
        print('ROLL:', line)
