---
status: partial
phase: 28-polimento-ux-da-home
source: [28-VERIFICATION.md]
started: 2026-11-22T22:40:00Z
updated: 2026-11-22T22:40:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Hover nos chips de cidade (ativo e inativo)
expected: Chip inativo mostra borda/texto accent e leve fundo accent/10 ao hover; chip ativo (selecionado) clareia com bg-accent-strong-hover; sem mudança de layout.
result: [pending]

### 2. Hover no dropdown de ordenação e nas opções
expected: Trigger mostra feedback accent ao hover/aberto; opções Recentes/Antigas mostram fundo accent/10 + texto accent-soft ao hover e ao navegar por teclado; sem layout shift.
result: [pending]

### 3. Teclado no SortDropdown
expected: ArrowUp/Down move opção ativa, Enter/Space seleciona, Escape fecha e devolve foco ao trigger; clique fora fecha; Tab não fica preso.
result: [pending]

### 4. Hover nos cards de vaga
expected: Card ganha borda accent e leve fundo rgba(139,92,246,0.04) ao hover; focus-within mantém borda accent; sem mudança de padding/borda/transform.
result: [pending]

### 5. Filtro de cidades dinâmico com busca ativa
expected: Ao digitar q que reduz resultados, o conjunto de chips de cidade permanece o mesmo (baseado em available_cities do board geral). Selecionar cidade obsoleta/URL antiga redireciona para estado amplo sem cidade.
result: [pending]

## Summary

total: 5
passed: 0
issues: 0
pending: 5
skipped: 0

## Gaps

[none yet]
