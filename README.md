# NQU — NaoQueroUsar
Plataforma pública de busca de emprego cujo diferencial é eliminar a burocracia de cadastro: qualquer pessoa vê as vagas e o contato sem criar conta, sem login e sem etapas intermediárias.

Slogan: "Procurar um emprego, não deve dar trabalho"

## Dev
- cd backend && uv sync
- uv run uvicorn app.main:app --reload

## Deploy
- Runbook de produção (Render + Vercel + Neon, CORS, cron, cold-start, rollback): [docs/DEPLOY.md](docs/DEPLOY.md)

