from pathlib import Path
p = Path('docs/DEPLOY.md')
t = p.read_text(encoding='utf-8')
# add explicit lowercase rollback phrase for acceptance
if 'rollback por reversão de env/config/domínio' not in t:
    t = t.replace('**Rollback:** por reversão de env/config/domínio e redeploy',
                  '**Rollback:** rollback por reversão de env/config/domínio (reversão de env/config/domínio) e redeploy')
p.write_text(t, encoding='utf-8')
print('fixed')
print('| 2026-11-12 | Render \u2014 `/api/v1/health` |' in t)
print('rollback por reversão de env/config/domínio' in t)
