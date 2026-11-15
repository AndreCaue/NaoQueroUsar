from pathlib import Path
text = Path('docs/DEPLOY.md').read_text(encoding='utf-8')
marker = '## Registro de verificação'
idx = text.index(marker)
tail = text[idx:]
Path('.gsd-temp/registro-tail.txt').write_text(tail, encoding='utf-8')
print(len(tail))
