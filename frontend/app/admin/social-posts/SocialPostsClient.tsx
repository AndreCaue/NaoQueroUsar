"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import { useAdminGuard } from "@/components/admin/AdminGuard";
import { useToast } from "@/components/admin/ToastProvider";
import {
  ApiError,
  getAdminSocialPosts,
  getSocialPostLogs,
  retrySocialPost,
  type SocialPostLogItem,
  type SocialPostStatusItem,
} from "@/lib/api";
import { buildAdminLoginHref } from "@/lib/adminReturnTo";
import { TOKEN_KEY } from "@/lib/auth";

function formatBrtDateTime(value: string | null | undefined): string | null {
  if (!value) return null;
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return null;
  return new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).format(d);
}

function badgeClass(status: SocialPostStatusItem["status"]): string {
  if (status === "failed") {
    return "border border-danger bg-[rgba(248,113,113,0.12)] text-danger-soft";
  }
  if (status === "published") {
    return "border border-accent bg-[rgba(139,92,246,0.12)] text-fg";
  }
  if (status === "publishing" || status === "scheduled") {
    return "border border-accent/40 bg-[rgba(139,92,246,0.08)] text-fg";
  }
  return "border border-line bg-canvas text-fg-muted";
}

function providerLabel(provider: SocialPostStatusItem["provider"]): string {
  return provider === "instagram" ? "Instagram" : "Facebook";
}

function itemKey(item: Pick<SocialPostStatusItem, "job_id" | "provider">): string {
  return `${item.job_id}:${item.provider}`;
}

export function SocialPostsClient() {
  const token = useAdminGuard();
  const { toast } = useToast();
  const [items, setItems] = useState<SocialPostStatusItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState<Record<string, boolean>>({});
  const [logsOpen, setLogsOpen] = useState<Record<string, boolean>>({});
  const [logsLoading, setLogsLoading] = useState<Record<string, boolean>>({});
  const [logsByKey, setLogsByKey] = useState<Record<string, SocialPostLogItem[]>>({});
  const retryingRef = useRef<Record<string, boolean>>({});

  const handleAuthError = useCallback((err: unknown): boolean => {
    if (err instanceof ApiError && err.status === 401) {
      try {
        sessionStorage.removeItem(TOKEN_KEY);
      } catch {
        // ignore
      }
      window.location.replace(
        buildAdminLoginHref(`${window.location.pathname}${window.location.search}`),
      );
      return true;
    }
    return false;
  }, []);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getAdminSocialPosts(token);
      setItems(Array.isArray(data?.items) ? data.items : []);
    } catch (err) {
      if (handleAuthError(err)) return;
      setItems([]);
      setError(
        "Não foi possível carregar o status das publicações. Tente novamente em alguns instantes.",
      );
    } finally {
      setLoading(false);
    }
  }, [token, handleAuthError]);

  useEffect(() => {
    void load();
  }, [load]);

  const loadLogs = useCallback(
    async (item: SocialPostStatusItem) => {
      if (!token) return;
      const key = itemKey(item);
      setLogsLoading((prev) => ({ ...prev, [key]: true }));
      try {
        const res = await getSocialPostLogs(token, item.job_id, item.provider);
        setLogsByKey((prev) => ({ ...prev, [key]: res.items ?? [] }));
      } catch (err) {
        if (handleAuthError(err)) return;
        toast("Não foi possível carregar o histórico de auditoria.", "error");
      } finally {
        setLogsLoading((prev) => ({ ...prev, [key]: false }));
      }
    },
    [token, handleAuthError, toast],
  );

  const toggleLogs = async (item: SocialPostStatusItem) => {
    const key = itemKey(item);
    const willOpen = !logsOpen[key];
    setLogsOpen((prev) => ({ ...prev, [key]: willOpen }));
    if (willOpen && !logsByKey[key]) {
      await loadLogs(item);
    }
  };

  const handleRetry = async (item: SocialPostStatusItem) => {
    if (!token) return;
    const key = itemKey(item);
    if (retryingRef.current[key]) return;
    retryingRef.current[key] = true;
    setRetrying((prev) => ({ ...prev, [key]: true }));
    try {
      const res = await retrySocialPost(token, item.job_id, item.provider);
      if (res.item) {
        setItems((prev) =>
          prev.map((it) => (itemKey(it) === key ? (res.item as SocialPostStatusItem) : it)),
        );
      } else {
        await load();
      }
      if (logsOpen[key]) {
        await loadLogs(item);
      }
      const outcome = res.outcome;
      if (outcome === "noop" || outcome === "not_eligible") {
        toast(res.message || "Nenhuma nova tentativa foi necessária. Status atualizado.", "success");
      } else {
        toast(res.message || "Nova tentativa iniciada.", "success");
      }
    } catch (err) {
      if (handleAuthError(err)) return;
      toast(
        "Não foi possível iniciar a nova tentativa. Tente novamente em alguns instantes.",
        "error",
      );
      await load();
    } finally {
      retryingRef.current[key] = false;
      setRetrying((prev) => ({ ...prev, [key]: false }));
    }
  };

  if (!token) return null;

  return (
    <div className="mt-6 space-y-4">
      {loading ? (
        <div className="rounded-[12px] border border-line bg-surface p-6">
          <p className="text-fg-muted">Carregando...</p>
        </div>
      ) : null}

      {!loading && error ? (
        <div className="rounded-[12px] border border-danger bg-[rgba(248,113,113,0.12)] p-4">
          <p className="text-[14px] text-danger-soft">{error}</p>
          <button
            type="button"
            onClick={() => void load()}
            className="mt-3 inline-flex min-h-11 items-center rounded-lg border border-line-strong px-4 text-sm font-semibold text-fg transition-colors hover:border-accent hover:text-accent-soft"
          >
            Tentar novamente
          </button>
        </div>
      ) : null}

      {!loading && !error && items.length === 0 ? (
        <div className="rounded-[12px] border border-line bg-surface p-6">
          <h2 className="text-xl font-semibold text-fg">
            Nenhuma publicação social encontrada
          </h2>
          <p className="mt-2 text-base text-fg-muted">
            Quando uma vaga for aprovada com postagem social, o status aparecerá aqui. Abra uma vaga na revisão para gerar ou acompanhar o rascunho.
          </p>
          <Link
            href="/admin/review"
            className="mt-4 inline-flex min-h-11 items-center rounded-lg bg-accent-strong px-4 text-sm font-semibold text-white transition-colors hover:bg-accent-strong-hover"
          >
            Ir para a fila de revisão
          </Link>
        </div>
      ) : null}

      {!loading && !error && items.length > 0 ? (
        <ul className="grid grid-cols-1 gap-3">
          {items.map((item) => {
            const key = itemKey(item);
            const isRetrying = Boolean(retrying[key]);
            const scheduled = formatBrtDateTime(item.scheduled_at);
            const published = formatBrtDateTime(item.published_at);
            const reconciledAt = formatBrtDateTime(item.ig_last_reconciled_at);
            const reconnectNeeded = Boolean(
              item.retry_block_reason && /reconect/i.test(item.retry_block_reason),
            );
            const platform = providerLabel(item.provider);
            const permalink = item.published_permalink || item.published_url;
            const logs = logsByKey[key] ?? [];
            const isLogsOpen = Boolean(logsOpen[key]);
            const isLogsLoading = Boolean(logsLoading[key]);

            return (
              <li key={key}>
                <article className="rounded-[12px] border border-line bg-surface p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-[12px] font-semibold uppercase tracking-wide text-fg-muted">
                        {platform}
                      </p>
                      <h3 className="text-[20px] font-semibold leading-tight text-fg [overflow-wrap:anywhere]">
                        {item.job_title || "Vaga"}
                      </h3>
                      <p className="mt-1 text-[14px] text-fg-muted [overflow-wrap:anywhere]">
                        ID da vaga: {item.job_id}
                      </p>
                    </div>
                    <span
                      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-[14px] ${badgeClass(item.status)}`}
                    >
                      {item.status === "publishing" ? (
                        <span
                          className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-accent-soft border-t-transparent"
                          aria-hidden="true"
                        />
                      ) : null}
                      {item.status_label}
                    </span>
                  </div>

                  <div className="mt-3 space-y-2 text-[14px]">
                    <p className="text-fg-muted">Tentativas: {item.attempts}</p>

                    {item.status === "scheduled" ? (
                      <p className="text-fg-muted">
                        {scheduled
                          ? `Publicação agendada para ${scheduled} (America/Sao_Paulo).`
                          : "Publicação agendada."}
                      </p>
                    ) : null}

                    {item.status === "publishing" ? (
                      <p className="text-fg-muted">
                        Publicação em andamento. Atualize em instantes para ver o resultado.
                      </p>
                    ) : null}

                    {item.status === "published" ? (
                      <div className="space-y-1">
                        <p className="text-fg">Publicado no {platform}.</p>
                        {published ? (
                          <p className="text-fg-muted">Publicado em {published} (America/Sao_Paulo).</p>
                        ) : null}
                        {permalink ? (
                          <a
                            href={permalink}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex min-h-11 items-center font-medium text-accent-soft underline-offset-4 hover:text-accent hover:underline"
                          >
                            Ver post no {platform}
                          </a>
                        ) : (
                          <p className="text-fg-muted">
                            Publicado no {platform}. Link indisponível.
                          </p>
                        )}
                      </div>
                    ) : null}

                    {item.status === "failed" ? (
                      <p className="text-danger-soft">
                        {item.last_error ||
                          "Não foi possível publicar este post. Tente novamente quando estiver disponível."}
                      </p>
                    ) : null}

                    {item.status === "draft" ? (
                      <p className="text-fg-muted">
                        Rascunho salvo. Aprove a vaga para agendar ou publicar.
                      </p>
                    ) : null}

                    {item.status === "none" ? (
                      <p className="text-fg-muted">
                        Nenhum post social registrado para esta vaga.
                      </p>
                    ) : null}

                    {item.retry_block_reason ? (
                      <p className={item.reconciliation_required ? "text-accent-soft" : "text-fg-muted"}>
                        {item.retry_block_reason}
                      </p>
                    ) : null}

                    {item.reconciliation_required ? (
                      <p className="text-fg-muted">
                        Reconciliação necessária: antes de tentar publicar novamente, o sistema verifica IDs/status conhecidos no Instagram.
                      </p>
                    ) : null}

                    {item.external_post_id ? (
                      <p className="text-fg-muted [overflow-wrap:anywhere]">ID externo: {item.external_post_id}</p>
                    ) : null}
                    {item.ig_container_id ? (
                      <p className="text-fg-muted [overflow-wrap:anywhere]">Container IG: {item.ig_container_id}</p>
                    ) : null}
                    {item.ig_media_id ? (
                      <p className="text-fg-muted [overflow-wrap:anywhere]">Mídia IG: {item.ig_media_id}</p>
                    ) : null}
                    {reconciledAt ? (
                      <p className="text-fg-muted">Última reconciliação IG: {reconciledAt} (America/Sao_Paulo).</p>
                    ) : null}

                    {reconnectNeeded ? (
                      <a
                        href="/admin/integracoes"
                        className="inline-flex min-h-11 items-center rounded-lg border border-line-strong px-4 text-sm font-semibold text-fg transition-colors hover:border-accent hover:text-accent-soft"
                      >
                        Abrir Integrações
                      </a>
                    ) : null}
                  </div>

                  <div className="mt-4 flex flex-wrap gap-2">
                    {item.can_retry ? (
                      <button
                        type="button"
                        onClick={() => void handleRetry(item)}
                        disabled={isRetrying}
                        className="inline-flex min-h-11 items-center justify-center rounded-lg bg-accent-strong px-4 text-sm font-semibold text-white transition-colors hover:bg-accent-strong-hover disabled:opacity-50"
                      >
                        {isRetrying ? "Tentando novamente..." : "Tentar novamente"}
                      </button>
                    ) : null}
                    <button
                      type="button"
                      onClick={() => void toggleLogs(item)}
                      className="inline-flex min-h-11 items-center justify-center rounded-lg border border-line-strong px-4 text-sm font-semibold text-fg transition-colors hover:border-accent hover:text-accent-soft"
                    >
                      {isLogsOpen ? "Ocultar histórico" : "Ver histórico"}
                    </button>
                  </div>

                  {isLogsOpen ? (
                    <div className="mt-3 rounded-lg border border-line bg-canvas p-3">
                      <p className="text-[14px] font-semibold text-fg">Histórico seguro de auditoria</p>
                      {isLogsLoading ? (
                        <p className="mt-2 text-[14px] text-fg-muted">Carregando histórico...</p>
                      ) : logs.length === 0 ? (
                        <p className="mt-2 text-[14px] text-fg-muted">Nenhum evento registrado.</p>
                      ) : (
                        <ul className="mt-2 space-y-2">
                          {logs.map((log, idx) => (
                            <li key={`${key}-log-${idx}-${log.created_at}`} className="text-[13px] text-fg-muted [overflow-wrap:anywhere]">
                              <span className="font-medium text-fg">
                                #{log.attempt_number} {log.result}
                              </span>
                              {" · "}
                              {formatBrtDateTime(log.created_at) ?? "-"}
                              {log.error_message ? ` · ${log.error_message}` : ""}
                              {log.response_summary ? ` · ${log.response_summary}` : ""}
                              {log.external_post_id ? ` · ID: ${log.external_post_id}` : ""}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ) : null}
                </article>
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}

export default SocialPostsClient;
