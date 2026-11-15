from pathlib import Path
t = Path('docs/DEPLOY.md').read_text(encoding='utf-8')
target = '| 2026-11-12 | Render \u2014 `/api/v1/health` |'
print('exact_contains', target in t)
print('startswith_any', any(line.startswith(target) for line in t.splitlines()))
print('line_has_substr', any(target.rstrip() in line for line in t.splitlines()))
# relaxed
print('has key parts', ('| 2026-11-12 | Render' in t and '`/api/v1/health`' in t and '\u2014' in t))
