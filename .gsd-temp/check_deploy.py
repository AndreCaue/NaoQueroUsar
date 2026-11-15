from pathlib import Path

t = Path('docs/DEPLOY.md').read_text(encoding='utf-8')
checks = [
    '## Alvo canônico (state-alvo)',
    'https://empreganoix.vercel.app',
    'https://empreganoix.onrender.com',
    'CORS_ORIGINS=https://empreganoix.vercel.app',
    'NEXT_PUBLIC_API_URL=https://empreganoix.onrender.com',
    'BACKEND_API_URL=https://empreganoix.onrender.com',
    'vars.API_BASE_URL=https://empreganoix.onrender.com',
    '/api/v1/admin/expire',
    'X-Cron-Secret',
    'T-06-01',
    'verificado em host legado',
    'alinhado contratualmente ao canônico',
    'pendente de execução operacional',
    'empreganoix-six.vercel.app',
    'nqu-backend-x60n.onrender.com',
    'nao-quero-usar.vercel.app',
    'naoquerousar.onrender.com',
    '| 2026-11-12 | Render — `/api/v1/health` |',
    '| 2026-11-14 | Deploy produção (10-04 Task 2, checkpoint aprovado) |',
    '| 2026-11-15 | Smoke gate produção (09-04 Task 3, critério 6) |',
    '/privacidade',
    '/termos-de-uso',
    'Access-Control-Allow-Origin',
    'Preflight CORS',
    'rollback por reversão de env/config/domínio',
    'NEXT_PUBLIC_*',
    '/admin',
]
miss = []
for c in checks:
    if c in t:
        print('OK', c)
    else:
        print('MISS', c)
        miss.append(c)
print('MISS_COUNT', len(miss))
