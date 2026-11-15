from pathlib import Path
t = Path('docs/DEPLOY.md').read_text(encoding='utf-8')
for line in t.splitlines():
    if 'Render' in line and '/api/v1/health' in line and line.startswith('| 2026-11-12'):
        print(repr(line))
        # check em dash U+2014
        print('has_em_dash', '\u2014' in line)
        print('has_en_dash', '\u2013' in line)
        print('has_minus', ' - ' in line)
        break
for line in t.splitlines():
    if 'Rollback por revers' in line:
        print('ROLL_REPR', repr(line))
        print('has_exact_phrase', 'rollback por reversão de env/config/domínio' in line)
        break
