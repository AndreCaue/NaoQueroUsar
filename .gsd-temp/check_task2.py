import json
from pathlib import Path

v = Path('scripts/verify-deploy.ps1').read_text(encoding='utf-8')
print('v1', 'https://empreganoix.vercel.app' in v)
print('v2', 'https://empreganoix.onrender.com' in v)
print('params', all(x in v for x in ['param(', '[Parameter(Mandatory = $true)][string]$FrontendUrl', '[Parameter(Mandatory = $true)][string]$BackendUrl', 'function Invoke-Http']))
fe = Path('frontend/.env.example').read_text(encoding='utf-8')
print('fe', 'NEXT_PUBLIC_API_URL=http://localhost:8000' in fe and 'BACKEND_API_URL=http://localhost:8000' in fe and 'https://empreganoix.onrender.com' in fe and 'https://empreganoix.vercel.app' in fe)
fl = Path('frontend/.env.local.example').read_text(encoding='utf-8')
print('fl', 'NEXT_PUBLIC_API_URL=http://localhost:8000' in fl)
r = Path('render.yaml').read_text(encoding='utf-8')
print('ry', 'name: nqu-backend' in r and 'autoDeploy: false' in r and 'healthCheckPath: /api/v1/health' in r and 'sync: false' in r)
vj = json.loads(Path('frontend/vercel.json').read_text(encoding='utf-8'))
print('vj', vj.get('framework') == 'nextjs')
w = Path('.github/workflows/expire-cron.yml').read_text(encoding='utf-8')
print('wf', all(x in w for x in ['vars.API_BASE_URL', 'secrets.CRON_SECRET', 'X-Cron-Secret', 'POST "${API_BASE_URL%/}/api/v1/admin/expire"']))
