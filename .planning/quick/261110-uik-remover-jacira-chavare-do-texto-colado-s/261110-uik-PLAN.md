---
phase: 261110-uik
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/app/services/extraction/blocklist.py
  - backend/tests/test_blocklist.py
  - backend/app/api/v1/extract.py
  - backend/tests/test_extract_api.py
  - frontend/lib/blocklist.ts
  - frontend/app/admin/paste/ExtractForm.tsx
autonomous: true
requirements: []   # quick task — sem IDs de ROADMAP; escopo vem da tarefa 261110-uik
user_setup: []

must_haves:
  truths:
    - "Colar um texto com 'JACIRA CHAVARE' insere o texto SEM o termo no cursor e mostra um aviso informativo (role=status), sem descartar o paste"
    - "O botão 'Extrair vagas' nunca é desabilitado por causa do termo — só por loading, falta de token ou texto efetivamente vazio"
    - "handleSubmit envia o texto já limpo para a API (defesa final) e sincroniza o textarea quando algo foi removido"
    - "POST /api/v1/admin/extract com o termo responde 200, chama extract_jobs com o texto limpo (texto ao redor intacto) e devolve o alerta de remoção em alerts"
    - "POST cujo texto é apenas o termo responde 422 com mensagem pt-BR de texto vazio e NÃO chama o Groq"
    - "POST com texto acima do limite de bytes continua respondendo 413 mesmo contendo o termo (precedência do tamanho preservada)"
  artifacts:
    - path: "backend/app/services/extraction/blocklist.py"
      provides: "REMOVED_TERM + TERM_REMOVED_ALERT + strip_blocked_terms(text) -> str"
      contains: "def strip_blocked_terms"
    - path: "backend/tests/test_blocklist.py"
      provides: "Testes de remoção: caixa, acento, espaços/quebras, múltiplas ocorrências, blob preservado, negativos, só-o-termo"
      contains: "strip_blocked_terms"
    - path: "backend/app/api/v1/extract.py"
      provides: "Strip antes do Groq + 422 para texto vazio + alerta de remoção"
      contains: "strip_blocked_terms(payload.text)"
    - path: "frontend/lib/blocklist.ts"
      provides: "Espelho da regra: REMOVED_TERM, TERM_REMOVED_NOTICE, stripBlockedTerms"
      exports: ["REMOVED_TERM", "TERM_REMOVED_NOTICE", "stripBlockedTerms"]
    - path: "frontend/app/admin/paste/ExtractForm.tsx"
      provides: "Paste inserindo texto limpo no cursor + aviso informativo + submit sem gate de bloqueio"
      contains: "stripBlockedTerms"
  key_links:
    - from: "backend/app/api/v1/extract.py"
      to: "app.services.extraction.blocklist.strip_blocked_terms"
      via: "chamada entre o gate 413 e extract_jobs"
      pattern: "strip_blocked_terms\\(payload\\.text\\)"
    - from: "frontend/app/admin/paste/ExtractForm.tsx"
      to: "frontend/lib/blocklist.ts"
      via: "import estático"
      pattern: "stripBlockedTerms"
---

<objective>
Inverter a regra do termo "JACIRA CHAVARE": em vez de bloquear o paste (422 / botão desabilitado / paste descartado), o termo é REMOVIDO de todas as ocorrências e a extração segue normalmente — a vaga é criada.

Purpose: o nome citado não deve virar conteúdo da vaga, mas também não pode impedir o admin de extrair o resto do texto. A remoção é a menor intervenção possível: casa o termo em qualquer caixa/acento/espaçamento entre as palavras, substitui cada ocorrência por um único espaço e preserva o restante do texto sem normalização global.

Output: `strip_blocked_terms`/`stripBlockedTerms` + testes backend reescritos, alerta informativo no summary, endpoint que extrai do texto limpo e formulário que insere o paste já limpo no cursor.

Substitui integralmente a decisão da quick task 261110-u28 (rejeição 422).
</objective>

<execution_context>
@$HOME/.config/opencode/get-shit-done/workflows/execute-plan.md
@$HOME/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@AGENTS.md
@backend/app/services/extraction/blocklist.py
@backend/app/api/v1/extract.py
@frontend/app/admin/paste/ExtractForm.tsx

Decisões já fechadas (não reabra):
1. Remover TODAS as ocorrências, qualquer caixa, ignorando acentos, aceitando qualquer quantidade de espaços/quebras entre as duas palavras. Cada ocorrência vira UM espaço; o resto do texto fica intacto.
2. Backend mantém os caminhos `blocklist.py`/`test_blocklist.py` mas troca os símbolos: `REMOVED_TERM`, `TERM_REMOVED_ALERT`, `strip_blocked_terms`. Regex montado a partir da constante (classes de caracteres com variantes acentuadas + `\s+` entre palavras), sem regex dinâmica a partir de input e sem normalização global do texto (offsets preservados).
3. Ordem no endpoint: auth → `GROQ_API_KEY` (503) → tamanho em bytes do texto ORIGINAL (413) → strip → vazio/só espaços (422) → `extract_jobs(texto_limpo, settings)`.
4. Feedback: constante `TERM_REMOVED_ALERT` em `blocklist.py` (junto do termo, fonte única do texto), anexada em `alerts` quando o texto mudou. Sem campos novos no schema de resposta e sem tocar `schemas/extract.py`.
5. Frontend: `stripBlockedTerms` + `TERM_REMOVED_NOTICE`; sem `isBlockedText`, sem `BLOCKED_TERM_ERROR`, sem estado `blocked`, sem `aria-invalid`, aviso em `role="status"`.
6. Sem dependências novas. Não tocar no board público, no review/edit de vagas salvas nem na regra de extração/LLM.

Comandos canônicos (Windows PowerShell 5.1 — sem `&&`/`||`):
- Backend, sempre a partir de `backend/` (senão `pytest` não lê `backend/pyproject.toml` e perde `asyncio_mode=auto`):
  `cd backend; .venv\Scripts\python.exe -m pytest -q tests/test_blocklist.py tests/test_extract_api.py`
- Frontend (não existe runner de teste): a partir de `frontend/`: `npx tsc --noEmit`, `npm run lint`, `npm run build`.

<interfaces>
Contratos atuais que as tarefas consomem (não invente outros):

`backend/app/api/v1/extract.py` (assinatura atual, inalterada):
```python
@router.post("/extract", response_model=ExtractSummaryResponse)
async def extract_admin(
    payload: ExtractRequest,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_admin),
) -> ExtractSummaryResponse
```

`backend/app/schemas/extract.py`:
```python
class ExtractRequest(BaseModel):
    text: str = Field(min_length=1)

class ExtractSummaryResponse(BaseModel):
    saved_pending: int
    saved_needs_review: int
    discarded: list[DiscardedJob]
    divergent: bool
    detected_count: int | None
    extracted_count: int
    truncated: bool
    model_used: str
    chunks: int
    alerts: list[str]
```

`backend/app/services/extraction/extractor.py` (chamada, inalterada):
```python
async def extract_jobs(text: str, settings: Settings) -> ExtractionResult
```

`backend/tests/test_extract_api.py` (helpers existentes, reutilize):
```python
def _make_result(**overrides: Any) -> ExtractionResult   # kept=2, discarded=1, divergent=True, truncated=True
async def _get_admin_token(client, admin_password: str) -> str
from app.api.v1 import extract as extract_module         # monkeypatch em extract_module.extract_jobs
```

`frontend/lib/api.ts` (inalterado):
```ts
export async function extractJobs(token: string, text: string): Promise<ExtractSummary>
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>task 1: strip_blocked_terms no backend + unit tests de remoção</name>
  <files>backend/app/services/extraction/blocklist.py, backend/tests/test_blocklist.py</files>
  <action>
Reescreva `backend/app/services/extraction/blocklist.py` inteiro. Conteúdo obrigatório (sem `unicodedata` — a remoção é por regex sobre o texto original, sem fold global):

```python
"""Remoção do termo residual na extração (admin paste) — regra única do backend.

Regra (espelhada em frontend/lib/blocklist.ts): todas as ocorrências do termo
são removidas, em qualquer caixa, ignorando acentos e aceitando qualquer
quantidade de espaços/quebras de linha entre as palavras. Cada ocorrência é
substituída por UM espaço e o restante do texto é preservado byte a byte —
nenhuma normalização global é aplicada.

O padrão é construído a partir da constante ``REMOVED_TERM`` (nunca de input
do usuário), então não há risco de injeção de padrão nem de ReDoS.

Nunca logue nem ecoe o texto colado: a mensagem cita apenas o termo.
"""

import re

REMOVED_TERM = "JACIRA CHAVARE"

TERM_REMOVED_ALERT = (
    'ℹ️ O termo "JACIRA CHAVARE" foi removido do texto antes da extração.'
)

# Variantes acentuadas aceitas por letra (minúsculas; a maiúscula é derivada).
_LETTER_VARIANTS = {
    "a": "aáàâãä",
    "c": "cç",
    "e": "eéèêë",
    "h": "h",
    "i": "iíìîï",
    "j": "j",
    "r": "r",
    "v": "v",
}


def _char_class(char: str) -> str:
    """Classe de caracteres que aceita a letra em caixa baixa, alta e acentuada."""
    variants = _LETTER_VARIANTS.get(char.lower(), char.lower())
    return f"[{variants}{variants.upper()}]"


_TERM_PATTERN = re.compile(
    "".join(r"\s+" if char == " " else _char_class(char) for char in REMOVED_TERM)
)


def strip_blocked_terms(text: str) -> str:
    """Remove todas as ocorrências do termo; cada uma vira um único espaço.

    Devolve ``""`` quando o texto é só o termo (ou ficou só com espaços),
    preservando o restante exatamente como veio do admin.
    """
    if not text:
        return ""
    cleaned = _TERM_PATTERN.sub(" ", text)
    return "" if not cleaned.strip() else cleaned
```

Não use `str.replace(texto_do_usuario)`, não mexa em `BLOCKED_TERM`/`BLOCKED_TERM_ERROR` (eles deixam de existir) e não altere nenhum outro módulo.

Reescreva `backend/tests/test_blocklist.py` inteiro (pytest puro, sem async/fixtures), importando `REMOVED_TERM, TERM_REMOVED_ALERT, strip_blocked_terms`:

1. `test_remove_variacoes` (parametrize: entrada, esperado) — todos os casos abaixo devem devolver exatamente `""`:
   `"JACIRA CHAVARE"`, `"jacira chavare"`, `"Jacira Chavare"`, `"JACIRA   CHAVARE"`, `"JACIRA\nCHAVARE"`, `"JACIRA\tCHAVARE"`, `"JACIRA CHAVÁRE"`, `"  jacira chavare  "`.
2. `test_remove_multiplas_ocorrencias` — `"Vaga 1: jacira chavare / Vaga 2: JACIRA CHAVARE"` → resultado não contém `"jacira"` nem `"chavare"` (casefold) e ainda contém `"Vaga 1:"` e `"Vaga 2:"`; e `strip_blocked_terms("jacira chavare jacira chavare") == ""`.
3. `test_preserva_texto_ao_redor` — com o blob realista
   `"Vaga: Auxiliar de limpeza — contato rh@empresa.com\n\nBairro: Centro\nNome citado: jacira chavare\nSalário: R$ 1.800"`:
   - `out.startswith("Vaga: Auxiliar de limpeza — contato rh@empresa.com")`
   - `out.endswith("Salário: R$ 1.800")`
   - `"rh@empresa.com" in out` e `"Bairro: Centro" in out`
   - `"jacira" not in out.casefold()` e `"chavare" not in out.casefold()`
   - `out.strip() != ""`
4. `test_texto_sem_termo_fica_intacto` (parametrize, `assert strip_blocked_terms(text) == text`):
   `""`, `"Vaga para desenvolvedor backend em São Paulo — rh@acme.com.br"`, `"JACIRA"`, `"CHAVARE"` (parciais NÃO podem ser removidas), `"Acentuação e\tquebras\npreservadas — ação, coração"`.
5. `test_so_o_termo_vira_string_vazia` — `strip_blocked_terms("JACIRA CHAVARE") == ""` e `strip_blocked_terms("  Jacira\nChavare  ") == ""`.
6. `test_alerta_pt_br_cita_o_termo` — `REMOVED_TERM in TERM_REMOVED_ALERT` e `"removido" in TERM_REMOVED_ALERT`.

Nada de testes que dependam do endpoint neste arquivo; nenhum I/O.
  </action>
  <verify>
    <automated>cd backend; .venv\Scripts\python.exe -m pytest -q tests/test_blocklist.py</automated>
  </verify>
  <done>`strip_blocked_terms` remove todas as ocorrências (caixa, acentos, múltiplos espaços/tab/newline), preserva integralmente o texto ao redor, devolve texto normal inalterado (incluindo "JACIRA"/"CHAVARE" isolados) e `""` quando só havia o termo; todos os casos do arquivo passam.</done>
</task>

<task type="auto">
  <name>task 2: endpoint extrai do texto limpo + alerta TERM_REMOVED_ALERT + testes de API</name>
  <files>backend/app/api/v1/extract.py, backend/tests/test_extract_api.py</files>
  <action>
**(a)** Em `backend/app/api/v1/extract.py`:

1. Troque o import do blocklist por:
   `from app.services.extraction.blocklist import TERM_REMOVED_ALERT, strip_blocked_terms`
   (o alerta vive em `blocklist.py` junto do termo — uma única fonte do texto, sem duplicar a mensagem em `schemas/extract.py`).
2. Substitua o bloco `if is_blocked_text(payload.text): raise HTTPException(status_code=422, detail=BLOCKED_TERM_ERROR)` pelo strip. O gate 413 continua ANTES, medindo `payload.text` original:

```python
    cleaned_text = strip_blocked_terms(payload.text)
    if not cleaned_text.strip():
        # O texto era só o termo removido — nada para extrair. Mensagem
        # própria (não confundir com corpo vazio do Pydantic) e sem Groq.
        raise HTTPException(
            status_code=422,
            detail=(
                "O texto continha apenas o termo removido — "
                "cole o conteúdo da vaga."
            ),
        )

    term_removed = cleaned_text != payload.text
```

4. Troque a chamada por `result = await extract_jobs(cleaned_text, settings)` — nenhum outro ponto do `try/except` muda.
5. Em `alerts`, antes do bloco de divergência, adicione:

```python
    if term_removed:
        alerts.append(TERM_REMOVED_ALERT)
```

Não ecoe `payload.text` em nenhuma resposta/log. Não mexa em `app/services/extraction/extractor.py` nem em `app/schemas/extract.py`.

**(b)** Em `backend/tests/test_extract_api.py`:

1. Troque o import `from app.services.extraction.blocklist import BLOCKED_TERM_ERROR` por `from app.services.extraction.blocklist import TERM_REMOVED_ALERT, strip_blocked_terms`.
2. DELETE `test_extract_422_blocked_term_skips_groq` e o substitua por:

```python
async def test_extract_200_strips_term_and_calls_groq_cleaned(
    client, admin_password, db_session, monkeypatch
):
    """O termo é removido e a extração segue: 200, Groq com texto limpo, alerta."""
    token = await _get_admin_token(client, admin_password)
    settings = get_settings()
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")

    calls: list[str] = []

    async def capture(text, s):
        calls.append(text)
        return _make_result()

    monkeypatch.setattr(extract_module, "extract_jobs", capture)

    pasted = "Vaga: jacira\n  chavare — contato segredo-xyz@example.com"
    resp = await client.post(
        "/api/v1/admin/extract",
        json={"text": pasted},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    assert len(calls) == 1
    sent = calls[0]
    assert sent != pasted
    assert sent == strip_blocked_terms(pasted)
    assert "jacira" not in sent.casefold()
    assert "chavare" not in sent.casefold()
    assert "segredo-xyz@example.com" in sent  # texto ao redor intacto
    assert sent.startswith("Vaga:")            # nada foi normalizado/reescrito
    assert TERM_REMOVED_ALERT in resp.json()["alerts"]
    assert "segredo-xyz" not in resp.text  # o texto colado nunca é ecoado
```

3. Adicione o caso "só o termo":

```python
async def test_extract_422_term_only_text_skips_groq(client, admin_password, monkeypatch):
    token = await _get_admin_token(client, admin_password)
    settings = get_settings()
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")

    calls: list[str] = []

    async def should_not_run(text, s):
        calls.append(text)
        raise AssertionError("extract_jobs não deveria ser chamado sem conteúdo")

    monkeypatch.setattr(extract_module, "extract_jobs", should_not_run)

    resp = await client.post(
        "/api/v1/admin/extract",
        json={"text": "  JACIRA\n chavare  "},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert isinstance(detail, str)
    assert "apenas o termo removido" in detail
    assert "JACIRA CHAVARE" in detail
    assert calls == []
```

4. MANTENHA `test_extract_413_wins_over_blocklist` (com `EXTRACT_MAX_TEXT_BYTES = 10` e `text="jacira chavare"` → 413); renomeie para `test_extract_413_wins_over_term_removal` e ajuste só a docstring/comentário ("o limite de bytes roda antes da remoção; o texto original é medido").

Não altere os outros testes existentes e não mude as fixtures.
  </action>
  <verify>
    <automated>cd backend; .venv\Scripts\python.exe -m pytest -q tests/test_extract_api.py</automated>
  </verify>
  <done>POST com o termo retorna 200, `extract_jobs` recebe exatamente `strip_blocked_terms(pasted)` (texto ao redor intacto) e `alerts` traz `TERM_REMOVED_ALERT`; texto só com o termo retorna 422 com "apenas o termo removido" e não chama o Groq; 413 continua vencendo a remoção; demais testes do arquivo seguem verdes.</done>
</task>

<task type="auto">
  <name>task 3: frontend — paste limpo no cursor, aviso informativo e submit sem gate</name>
  <files>frontend/lib/blocklist.ts, frontend/app/admin/paste/ExtractForm.tsx</files>
  <action>
**(a)** Reescreva `frontend/lib/blocklist.ts` para espelhar exatamente a regra do backend (sem `fold`/NFKD global):

```ts
/**
 * Remoção do termo residual na extração (admin paste) — regra única do frontend.
 * Espelha backend/app/services/extraction/blocklist.py: todas as ocorrências
 * são removidas, em qualquer caixa, ignorando acentos e aceitando qualquer
 * quantidade de espaços/quebras de linha entre as palavras. Cada ocorrência
 * vira UM espaço e o resto do texto é preservado — sem normalização global.
 * O padrão é montado a partir da constante, nunca do texto do usuário.
 */

export const REMOVED_TERM = "JACIRA CHAVARE";

export const TERM_REMOVED_NOTICE = `ℹ️ O termo "${REMOVED_TERM}" foi removido do texto antes da extração.`;

// Variantes acentuadas por letra (minúsculas; a maiúscula é derivada).
const LETTER_VARIANTS: Record<string, string> = {
  a: "aáàâãä",
  c: "cç",
  e: "eéèêë",
  h: "h",
  i: "iíìîï",
  j: "j",
  r: "r",
  v: "v",
};

function charClass(char: string): string {
  const variants = LETTER_VARIANTS[char.toLowerCase()] ?? char.toLowerCase();
  return `[${variants}${variants.toUpperCase()}]`;
}

const TERM_SOURCE = REMOVED_TERM.split("")
  .map((char) => (char === " " ? "\\s+" : charClass(char)))
  .join("");

export function stripBlockedTerms(text: string): string {
  if (!text) return "";
  // RegExp novo a cada chamada: evita o estado de lastIndex de uma /g compartilhada.
  const cleaned = text.replace(new RegExp(TERM_SOURCE, "g"), " ");
  return cleaned.trim() === "" ? "" : cleaned;
}
```

Não use `\p{M}` nem `replaceAll` (target ES2017 do tsconfig). Não exporte `isBlockedText`/`BLOCKED_TERM_ERROR`.

**(b)** Em `frontend/app/admin/paste/ExtractForm.tsx`:

1. Import de react: `import { useEffect, useState, type ClipboardEvent } from "react";`
2. Import do blocklist: `import { TERM_REMOVED_NOTICE, stripBlockedTerms } from "@/lib/blocklist";`
3. Remova o estado `blockedNotice` e a linha derivada `const blocked = ...`. No lugar, adicione `const [notice, setNotice] = useState<string | null>(null);`
4. Em `clearSession` e `handleReset`, troque `setBlockedNotice(false)` por `setNotice(null)`.
5. `handleSubmit`:

```tsx
  const handleSubmit = async () => {
    const cleaned = stripBlockedTerms(text); // defesa final: nada de termo vai à API
    if (!token || !cleaned.trim()) return;
    if (cleaned !== text) {
      setText(cleaned);
      setNotice(TERM_REMOVED_NOTICE);
    }
    setError(null);
    setSummary(null);
    setLoading(true);
    try {
      const res = await extractJobs(token, cleaned);
      setSummary(res);
    } catch (err) {
      // IN-08: JWT expirado/inválido derruba a sessão (clearSession antes do erro).
      if (err instanceof ApiError && err.status === 401) {
        clearSession();
        resetTurnstile();
        setError("Sessão expirada — entre novamente.");
        return;
      }
      const msg = err instanceof Error ? err.message : "Erro ao extrair";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };
```

6. Substitua `handlePaste` por (insere o texto já limpo no cursor, respeitando seleção):

```tsx
  // Colar conteúdo com o termo não é recusado: o termo sai e o resto entra
  // no cursor. Sem o termo, o paste nativo segue intocado.
  const handlePaste = (e: ClipboardEvent<HTMLTextAreaElement>) => {
    const pasted = e.clipboardData.getData("text");
    const cleaned = stripBlockedTerms(pasted);
    if (cleaned === pasted) return;

    e.preventDefault();
    const el = e.currentTarget;
    const start = el.selectionStart ?? text.length;
    const end = el.selectionEnd ?? start;
    const next = text.slice(0, start) + cleaned + text.slice(end);
    setText(next);
    setNotice(TERM_REMOVED_NOTICE);
    const caret = start + cleaned.length;
    requestAnimationFrame(() => {
      el.focus();
      el.setSelectionRange(caret, caret);
    });
  };
```

7. Textarea: `onChange={(e) => { setText(e.target.value); if (notice) setNotice(null); }}`, mantenha `onPaste={handlePaste}`, REMOVA `aria-invalid`, e mantenha `value`, `rows`, `minLength`, `placeholder`, `disabled` e `className`.
8. Substitua o bloco `{blocked && (<div role="alert" ...>...)}` por um aviso informativo (não erro):

```tsx
            {notice && (
              <div role="status" className="rounded-lg border border-line-strong bg-canvas p-3 text-fg-muted">
                {notice}
              </div>
            )}
```

9. `isSubmitDisabled`: `loading || !token || !stripBlockedTerms(text).trim()` (remova `|| blocked`).

Não altere login, Turnstile, renderização de `summary`/`error`/`discarded`, nem crie dependências. `notice` é informativo: nunca desabilita o botão.
  </action>
  <verify>
    <automated>cd frontend; npx tsc --noEmit; npm run lint; npm run build</automated>
  </verify>
  <done>`tsc --noEmit`, `npm run lint` e `npm run build` passam; não existem mais `isBlockedText`, `BLOCKED_TERM_ERROR`, `blocked`, `blockedNotice` nem `aria-invalid`; colar texto com o termo insere o restante no cursor e mostra `role="status"`; `handleSubmit` envia `stripBlockedTerms(text)`; o botão só desabilita por loading, falta de token ou texto (após remoção) vazio.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| admin browser → `POST /api/v1/admin/extract` | Texto colado é entrada não confiável, mesmo vindo de um admin autenticado |
| API → Groq | O texto enviado ao provedor já deve estar sem o termo |
| API → banco | O conteúdo persistido (`source_snippet`) deriva do texto limpo |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-261110-11 | Tampering | cliente (`lib/blocklist.ts`) | mitigate | O strip do cliente é conveniência; a autoridade é o backend — `extract.py` chama `strip_blocked_terms` antes de `extract_jobs`, então chamar a API direto (curl) também não envia o termo ao Groq. |
| T-261110-12 | Denial of Service (ReDoS) | `_TERM_PATTERN` / `TERM_SOURCE` | mitigate | Padrão montado apenas da constante `REMOVED_TERM` (classes de caracteres fixas + `\s+`), nunca de input; sem quantificadores aninhados nem alternância sobre texto do usuário. |
| T-261110-13 | Information Disclosure | `HTTPException(422, detail=...)` e alerta | mitigate | Mensagens são constantes pt-BR que citam apenas o termo; `payload.text` nunca é logado nem ecoado. |
| T-261110-14 | Tampering (bypass por variação) | `strip_blocked_terms` / `stripBlockedTerms` | mitigate | Classes aceitam variantes acentuadas de cada letra + `\s+` entre palavras + caixa alta/baixa; testado em unit tests e no fluxo de API. |
| T-261110-15 | Repudiation (remoção silenciosa) | resposta `alerts` / `role=status` | mitigate | Toda remoção é anunciada: `TERM_REMOVED_ALERT` no summary e `TERM_REMOVED_NOTICE` no formulário. |
| T-261110-16 | — (falso positivo) | regex do termo | accept | Variações próximas (ex.: "JACIRA CHAVARES" → sobra "S") são removidas parcialmente; impacto é cosmético no texto, nunca perda da vaga. |
</threat_model>

<verification>
1. Backend focado: `cd backend; .venv\Scripts\python.exe -m pytest -q tests/test_blocklist.py tests/test_extract_api.py`
2. Backend completo (sem regressões): `cd backend; .venv\Scripts\python.exe -m pytest -q`
3. Frontend: `cd frontend; npx tsc --noEmit; npm run lint; npm run build`
   - Se `next build` falhar só por env ausente, rode com as chaves de dev:
     `$env:NEXT_PUBLIC_API_URL="http://localhost:8000"; $env:NEXT_PUBLIC_TURNSTILE_SITE_KEY="1x00000000000000000000AA"; npm run build`
4. Prova manual opcional (não bloqueante): backend + `npm run dev` → login admin → colar um blob com "jacira chavare" no meio: o textarea recebe o texto SEM o termo, o restante aparece no cursor e o aviso informativo (não vermelho) aparece; "Extrair vagas" segue habilitado; o resumo lista o aviso de remoção e conta a vaga salva.
</verification>

<success_criteria>
- O termo "JACIRA CHAVARE" é REMOVIDO, nunca bloqueado: nenhum 422 por causa do termo quando há conteúdo restante, nenhum `preventDefault` que descarte o paste, nenhum `disabled`/`aria-invalid` por causa do termo.
- Existem exatamente dois pontos de verdade da regra: `backend/app/services/extraction/blocklist.py` (`REMOVED_TERM`, `strip_blocked_terms`) e `frontend/lib/blocklist.ts` (`REMOVED_TERM`, `stripBlockedTerms`), com a mesma semântica.
- `extract_jobs` recebe sempre o texto limpo; o texto ao redor do termo é preservado e o summary informa a remoção via `TERM_REMOVED_ALERT`.
- Texto que é apenas o termo → 422 com "apenas o termo removido", sem chamar o Groq; 413 continua com precedência sobre a remoção.
- Nenhuma dependência nova; board público, review/edit de vagas salvas e regra de extração/LLM intocados.
- `pytest` (focado e completo), `tsc --noEmit`, `lint` e `build` verdes.
</success_criteria>

<output>
Após concluir, crie `.planning/quick/261110-uik-remover-jacira-chavare-do-texto-colado-s/261110-uik-SUMMARY.md` seguindo `@$HOME/.config/opencode/get-shit-done/templates/summary.md`, registrando: arquivos alterados, saída dos comandos de verificação, variações cobertas pelos testes de remoção e a confirmação de que a quick task 261110-u28 (bloqueio 422) foi substituída.
</output>
