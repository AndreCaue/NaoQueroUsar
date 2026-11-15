"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { useAdminGuard } from "@/components/admin/AdminGuard";
import { useToast } from "@/components/admin/ToastProvider";
import {
  ApiError,
  confirmMetaPageSelection,
  disconnectMetaIntegration,
  getMetaIntegrationStatus,
  getMetaPendingSelection,
  startMetaOAuth,
  verifyMetaIntegration,
  type MetaIntegrationStatus,
  type MetaPendingPage,
} from "@/lib/api";

type BannerKind = "success" | "error" | "info";

function formatPtBrDateTime(value: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

function isStatusPayload(
  value: unknown,
): value is MetaIntegrationStatus {
  if (!value || typeof value !== "object") return false;
  const v = value as Partial<MetaIntegrationStatus>;
  return (
    v.provider === "facebook" &&
    (v.status === "connected" ||
      v.status === "needs_reconnect" ||
      v.status === "disconnected") &&
    typeof v.pending_selection === "boolean"
  );
}

export function IntegrationsClient() {
  const token = useAdminGuard();
  const { toast } = useToast();
  const searchParams = useSearchParams();
  const router = useRouter();

  const [status, setStatus] = useState<MetaIntegrationStatus | null>(null);
  const [pendingPages, setPendingPages] = useState<MetaPendingPage[]>([]);
  const [selectedPageId, setSelectedPageId] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<
    "start" | "verify" | "confirm" | "disconnect" | null
  >(null);
  const [pageError, setPageError] = useState<string | null>(null);
  const [transientVerifyMessage, setTransientVerifyMessage] = useState<string | null>(
    null,
  );
  const [banner, setBanner] = useState<{ kind: BannerKind; text: string } | null>(
    null,
  );
  const [showDisconnectDialog, setShowDisconnectDialog] = useState(false);
  const dialogRef = useRef<HTMLDialogElement | null>(null);

  const result = searchParams.get("result");
  const pendingNonce = searchParams.get("pending");
  const reason = searchParams.get("reason");

  const callbackBanner = useMemo(() => {
    if (!result) return null;
    if (result === "connected") {
      return {
        kind: "success" as const,
        text: "Página do Facebook conectada com sucesso.",
      };
    }
    if (result === "cancelled") {
      return {
        kind: "info" as const,
        text: "Conexão com o Facebook cancelada. Nenhuma alteração foi feita.",
      };
    }
    if (result === "select_page") {
      return {
        kind: "info" as const,
        text: "Escolha uma Página do Facebook para concluir a conexão.",
      };
    }
    if (result === "error") {
      const safeReasonText =
        reason && /not.?configured|configur/i.test(reason)
          ? "Integração com Facebook não configurada."
          : null;
      return {
        kind: "error" as const,
        text:
          safeReasonText ??
          "Não foi possível conectar ao Facebook. Tente novamente.",
      };
    }
    return null;
  }, [result, reason]);

  useEffect(() => {
    if (callbackBanner) setBanner(callbackBanner);
  }, [callbackBanner]);

  const refresh = useCallback(
    async (opts?: { keepLoading?: boolean }) => {
      if (!token) return;
      if (!opts?.keepLoading) setLoading(true);
      setPageError(null);
      try {
        const nextStatus = await getMetaIntegrationStatus(token);
        setStatus(nextStatus);

        const shouldLoadPending =
          (result === "select_page" && Boolean(pendingNonce)) ||
          nextStatus.pending_selection;
        if (shouldLoadPending && pendingNonce) {
          const pending = await getMetaPendingSelection(token, pendingNonce);
          setPendingPages(pending.pages ?? []);
          if ((pending.pages ?? []).length === 1) {
            setSelectedPageId(pending.pages[0]?.page_id ?? "");
          }
        } else {
          setPendingPages([]);
          setSelectedPageId("");
        }
      } catch (err) {
        if (err instanceof ApiError) {
          setPageError(err.message || "Não foi possível concluir a ação. Tente novamente em alguns instantes. Se o problema continuar, reconecte sua Página do Facebook.");
        } else {
          setPageError(
            "Não foi possível concluir a ação. Tente novamente em alguns instantes. Se o problema continuar, reconecte sua Página do Facebook.",
          );
        }
      } finally {
        setLoading(false);
      }
    },
    [token, result, pendingNonce],
  );

  useEffect(() => {
    if (!token) return;
    void refresh();
  }, [token, refresh]);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (showDisconnectDialog && !dialog.open) {
      dialog.showModal();
    } else if (!showDisconnectDialog && dialog.open) {
      dialog.close();
    }
  }, [showDisconnectDialog]);

  const clearResultParams = useCallback(() => {
    if (!result) return;
    router.replace("/admin/integracoes");
  }, [result, router]);

  const handleStart = useCallback(async () => {
    if (!token) return;
    setActionLoading("start");
    setPageError(null);
    try {
      const { redirect_url } = await startMetaOAuth(token);
      window.location.assign(redirect_url);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "Não foi possível conectar ao Facebook. Tente novamente.";
      setBanner({ kind: "error", text: message });
      toast(message, "error");
      setActionLoading(null);
    }
  }, [token, toast]);

  const handleVerify = useCallback(async () => {
    if (!token) return;
    setActionLoading("verify");
    setTransientVerifyMessage(null);
    setPageError(null);
    try {
      const data = await verifyMetaIntegration(token);
      if (isStatusPayload(data)) {
        setStatus(data);
        toast("Verificação concluída.", "success");
      } else {
        await refresh({ keepLoading: true });
        toast("Verificação concluída.", "success");
      }
    } catch (err) {
      const isConnected = status?.status === "connected";
      if (isConnected) {
        const msg =
          "Não foi possível verificar a conexão agora. Sua conexão atual foi mantida. Tente novamente em alguns instantes.";
        setTransientVerifyMessage(msg);
        setBanner({ kind: "error", text: msg });
      } else {
        const message =
          err instanceof ApiError
            ? err.message
            : "Não foi possível concluir a ação. Tente novamente em alguns instantes. Se o problema continuar, reconecte sua Página do Facebook.";
        setBanner({ kind: "error", text: message });
        toast(message, "error");
        await refresh({ keepLoading: true });
      }
    } finally {
      setActionLoading(null);
    }
  }, [token, status?.status, toast, refresh]);

  const handleConfirmSelection = useCallback(async () => {
    if (!token || !pendingNonce || !selectedPageId) return;
    setActionLoading("confirm");
    setPageError(null);
    try {
      const payload = { pending_nonce: pendingNonce, page_id: selectedPageId };
      const nextStatus = await confirmMetaPageSelection(token, payload);
      setStatus(nextStatus);
      setPendingPages([]);
      setSelectedPageId("");
      setBanner({
        kind: "success",
        text: "Página do Facebook conectada com sucesso.",
      });
      toast("Página confirmada com sucesso.", "success");
      clearResultParams();
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "Não foi possível concluir a ação. Tente novamente em alguns instantes. Se o problema continuar, reconecte sua Página do Facebook.";
      setBanner({ kind: "error", text: message });
      toast(message, "error");
    } finally {
      setActionLoading(null);
    }
  }, [token, pendingNonce, selectedPageId, toast, clearResultParams]);

  const handleDisconnect = useCallback(async () => {
    if (!token) return;
    setActionLoading("disconnect");
    setPageError(null);
    try {
      const data = await disconnectMetaIntegration(token);
      if (isStatusPayload(data)) {
        setStatus({ ...data, status: "disconnected", pending_selection: false });
      } else {
        await refresh({ keepLoading: true });
      }
      setBanner({
        kind: "info",
        text: "Conexão desconectada.",
      });
      toast("Página desconectada.", "success");
      clearResultParams();
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "Não foi possível concluir a ação. Tente novamente em alguns instantes. Se o problema continuar, reconecte sua Página do Facebook.";
      setBanner({ kind: "error", text: message });
      toast(message, "error");
    } finally {
      setActionLoading(null);
      setShowDisconnectDialog(false);
    }
  }, [token, toast, refresh, clearResultParams]);

  const inSelectionFlow =
    (result === "select_page" && Boolean(pendingNonce)) ||
    (status?.pending_selection && Boolean(pendingNonce) && pendingPages.length > 0);

  const effectiveStatus = status?.status ?? "disconnected";

  const bannerClass =
    banner?.kind === "success"
      ? "border-accent bg-[rgba(139,92,246,0.12)] text-fg"
      : banner?.kind === "error"
        ? "border-danger bg-[rgba(248,113,113,0.12)] text-danger-soft"
        : "border-line bg-surface text-fg";

  if (!token) return null;

  return (
    <div className="mt-6 space-y-4">
      {banner && (
        <div className={`rounded-[12px] border px-4 py-3 text-sm ${bannerClass}`}>
          {banner.text}
        </div>
      )}

      {pageError && (
        <div className="rounded-[12px] border border-danger bg-[rgba(248,113,113,0.12)] px-4 py-3 text-sm text-danger-soft">
          {pageError}
        </div>
      )}

      <section className="rounded-[12px] border border-line bg-surface p-6">
        {loading ? (
          <p className="text-fg-muted">Carregando integrações...</p>
        ) : inSelectionFlow ? (
          <div className="space-y-4">
            <div>
              <h2 className="text-xl font-semibold">Selecione a Página do Facebook</h2>
              <p className="mt-1 text-base text-fg-muted">
                Encontramos mais de uma Página disponível. Escolha apenas uma para concluir a conexão desta conta.
              </p>
            </div>
            <div className="space-y-2">
              {pendingPages.map((page) => {
                const selected = selectedPageId === page.page_id;
                return (
                  <label
                    key={page.page_id}
                    className={`flex min-h-[44px] cursor-pointer items-start gap-3 rounded-[12px] border p-4 transition-colors ${
                      selected
                        ? "border-accent bg-[rgba(139,92,246,0.08)]"
                        : "border-line hover:border-accent"
                    }`}
                  >
                    <input
                      type="radio"
                      name="meta-page"
                      value={page.page_id}
                      checked={selected}
                      onChange={() => setSelectedPageId(page.page_id)}
                      className="mt-1"
                    />
                    <div>
                      <div className="font-semibold text-fg">
                        {page.page_name || "Página sem nome"}
                      </div>
                      <div className="text-sm text-fg-muted">ID da página: {page.page_id}</div>
                    </div>
                  </label>
                );
              })}
              {pendingPages.length === 0 && (
                <p className="text-sm text-fg-muted">
                  Nenhuma página pendente encontrada. Tente reconectar.
                </p>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={handleConfirmSelection}
                disabled={!selectedPageId || !pendingNonce || actionLoading === "confirm"}
                className="inline-flex min-h-[44px] items-center justify-center rounded-[12px] bg-accent px-4 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {actionLoading === "confirm" ? "Conectando..." : "Confirmar página"}
              </button>
              <button
                type="button"
                onClick={handleStart}
                disabled={actionLoading !== null}
                className="inline-flex min-h-[44px] items-center justify-center rounded-[12px] border border-line px-4 py-2 text-sm font-semibold text-fg hover:border-accent disabled:cursor-not-allowed disabled:opacity-50"
              >
                Reconectar
              </button>
            </div>
          </div>
        ) : effectiveStatus === "connected" ? (
          <div className="space-y-4">
            <div>
              <h2 className="text-xl font-semibold">Página do Facebook conectada</h2>
              <p className="mt-1 text-base text-fg-muted">
                A integração está ativa para a página exibida abaixo. Você pode verificar a conexão agora ou desconectar quando quiser.
              </p>
            </div>
            <dl className="grid gap-2 text-sm text-fg-muted sm:grid-cols-2">
              <div>
                <dt className="font-semibold text-fg">Página</dt>
                <dd>{status?.page_name || "—"}</dd>
              </div>
              <div>
                <dt className="font-semibold text-fg">ID da página</dt>
                <dd>{status?.page_id || "—"}</dd>
              </div>
              <div>
                <dt className="font-semibold text-fg">Conectado em</dt>
                <dd>{formatPtBrDateTime(status?.connected_at ?? null)}</dd>
              </div>
              <div>
                <dt className="font-semibold text-fg">Última verificação</dt>
                <dd>{formatPtBrDateTime(status?.token_checked_at ?? null)}</dd>
              </div>
            </dl>
            {status?.alert?.message && (
              <div className="rounded-[12px] border border-line bg-canvas px-4 py-3 text-sm text-fg">
                {status.alert.message}
              </div>
            )}
            {transientVerifyMessage && (
              <div className="rounded-[12px] border border-danger bg-[rgba(248,113,113,0.12)] px-4 py-3 text-sm text-danger-soft">
                {transientVerifyMessage}
              </div>
            )}
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={handleVerify}
                disabled={actionLoading !== null}
                className="inline-flex min-h-[44px] items-center justify-center rounded-[12px] bg-accent px-4 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {actionLoading === "verify" ? "Verificando conexão..." : "Verificar agora"}
              </button>
              <button
                type="button"
                onClick={() => setShowDisconnectDialog(true)}
                disabled={actionLoading !== null}
                className="inline-flex min-h-[44px] items-center justify-center rounded-[12px] border border-danger px-4 py-2 text-sm font-semibold text-danger hover:bg-[rgba(248,113,113,0.08)] disabled:cursor-not-allowed disabled:opacity-50"
              >
                Desconectar
              </button>
            </div>
          </div>
        ) : effectiveStatus === "needs_reconnect" ? (
          <div className="space-y-4">
            <div>
              <h2 className="text-xl font-semibold">Reconexão necessária</h2>
              <p className="mt-1 text-base text-fg-muted">
                A conexão com o Facebook precisa ser renovada. Reconecte para continuar usando a integração com segurança.
              </p>
            </div>
            {status?.page_name && (
              <p className="text-sm text-fg-muted">Página: {status.page_name}</p>
            )}
            {status?.alert?.message && (
              <div className="rounded-[12px] border border-danger bg-[rgba(248,113,113,0.12)] px-4 py-3 text-sm text-danger-soft">
                {status.alert.message}
              </div>
            )}
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={handleStart}
                disabled={actionLoading !== null}
                className="inline-flex min-h-[44px] items-center justify-center rounded-[12px] bg-accent px-4 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {actionLoading === "start" ? "Conectando..." : "Reconectar"}
              </button>
              <button
                type="button"
                onClick={() => setShowDisconnectDialog(true)}
                disabled={actionLoading !== null}
                className="inline-flex min-h-[44px] items-center justify-center rounded-[12px] border border-danger px-4 py-2 text-sm font-semibold text-danger hover:bg-[rgba(248,113,113,0.08)] disabled:cursor-not-allowed disabled:opacity-50"
              >
                Desconectar
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <h2 className="text-xl font-semibold">Nenhuma Página do Facebook conectada</h2>
              <p className="mt-1 text-base text-fg-muted">
                Conecte uma Página para habilitar a publicação automática de vagas no Facebook. Você será redirecionado para o Meta em uma etapa segura no servidor.
              </p>
            </div>
            <button
              type="button"
              onClick={handleStart}
              disabled={actionLoading !== null}
              className="inline-flex min-h-[44px] items-center justify-center rounded-[12px] bg-accent px-4 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {actionLoading === "start" ? "Conectando..." : "Conectar Facebook"}
            </button>
          </div>
        )}
      </section>

      <dialog
        ref={dialogRef}
        onCancel={(e) => {
          e.preventDefault();
          if (actionLoading !== "disconnect") setShowDisconnectDialog(false);
        }}
        className="w-full max-w-lg rounded-[16px] border border-line bg-surface p-0 text-fg backdrop:bg-black/60"
      >
        <form
          method="dialog"
          className="space-y-4 p-6"
          onSubmit={(e) => e.preventDefault()}
        >
          <h3 className="text-xl font-semibold">Desconectar</h3>
          <p className="text-sm text-fg-muted">
            Tem certeza de que deseja desconectar esta Página do Facebook? A publicação automática ficará indisponível até você conectar novamente.
          </p>
          <div className="flex flex-wrap justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowDisconnectDialog(false)}
              disabled={actionLoading === "disconnect"}
              className="inline-flex min-h-[44px] items-center justify-center rounded-[12px] border border-line px-4 py-2 text-sm font-semibold text-fg hover:border-accent disabled:cursor-not-allowed disabled:opacity-50"
            >
              Manter conexão
            </button>
            <button
              type="button"
              onClick={handleDisconnect}
              disabled={actionLoading === "disconnect"}
              className="inline-flex min-h-[44px] items-center justify-center rounded-[12px] border border-danger bg-danger/10 px-4 py-2 text-sm font-semibold text-danger hover:bg-[rgba(248,113,113,0.18)] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {actionLoading === "disconnect" ? "Desconectando..." : "Desconectar página"}
            </button>
          </div>
        </form>
      </dialog>
    </div>
  );
}
