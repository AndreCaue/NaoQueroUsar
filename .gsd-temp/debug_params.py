from pathlib import Path
v = Path('scripts/verify-deploy.ps1').read_text(encoding='utf-8')
for s in ['param(', '[Parameter(Mandatory = $true)][string]$FrontendUrl', '[Parameter(Mandatory = $true)][string]$BackendUrl', 'function Invoke-Http']:
    print(s, '=>', s in v)
print('---')
for i, l in enumerate(v.splitlines()[:45], 1):
    if 'param' in l or 'Parameter' in l or 'FrontendUrl' in l or 'BackendUrl' in l:
        print(i, repr(l))
