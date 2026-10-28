"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { useAdminGuard } from "@/components/admin/AdminGuard";
import { CityChips } from "@/components/admin/CityChips";
import { ReviewRow } from "@/components/admin/ReviewRow";
import { useToast } from "@/components/admin/ToastProvider";
import {
  ApiError,
  approveJob,
  deleteJob,
  listAdminJobs,
  type JobAdmin,
} from "@/lib/api";
import { TOKEN_KEY } from "@/lib/auth";
import type { CitySlug } from "@/lib/cities";

import { DeleteConfirmDialog } from "./DeleteConfirmDialog";
import { EditJobDialog } from "./EditJobDialog";

const PAGE_SIZE = 24;

/** A 401 means the JWT expired: end the session instead of looping on retry. */
function handleAuthError(err: unknown): boolean {
  if (err instanceof ApiError && err.status === 401) {
    try {
      sessionStorage.removeItem(TOKEN_KEY);
    } catch {
      // ignore storage errors
    }
    window.location.replace("/admin/paste");
    return true;
  }
  return false;
}

type Tab = "pending" | "needs_review";

const TAB_LABELS: Record<Tab, string> = {
  pending: "Pendentes",
  needs_review: "Precisam correção",
};

/**
 * ReviewQueue — estado, fetch, tabs, filtro de cidade, paginação e
 * atualizações otimistas da fila de revisão (REVW-01..05).
 *
 * O fetch roda em um único efeito com dependências explícitas
 * (token/tab/city/page/refreshKey) — sem loop de refetch. Mutações removem
 * o item da lista na hora e, em erro, restauram o snapshot (lista, total e
 * badges) sem disparar um novo fetch que pudesse mascarar o rollback.
 */
export function ReviewQueue() {
  const token = useAdminGuard();
  const { toast } = useToast();

  const [tab, setTab] = useState<Tab>("pending");
  const [city, setCity] = useState<CitySlug | null>(null);
  const [page, setPage] = useState(1);

  const [items, setItems] = useState<JobAdmin[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const [counts, setCounts] = useState<Record<Tab, number | null>>({
    pending: null,
    needs_review: null,
  });

  const [selectedJob, setSelectedJob] = useState<JobAdmin | null>(null);
  const [editOpen, setEditOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<JobAdmin | null>(null);

  // Serializes mutations: a second approve/delete while one is in flight would
  // apply an optimistic update on top of a snapshot that is already stale.
  const mutatingRef = useRef(false);

  const reload = useCallback(() => setRefreshKey((key) => key + 1), []);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    setLoading(true);
    setError(null);

    listAdminJobs(token, {
      status: tab,
      city: city ?? undefined,
      page,
      limit: PAGE_SIZE,
    })
      .then((result) => {
        if (cancelled) return;
        setItems(result.items);
        setTotal(result.total);
        setCounts((prev) => ({ ...prev, [tab]: result.total }));
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (handleAuthError(err)) return;
        setItems([]);
        setTotal(0);
        setError(
          err instanceof Error
            ? err.message
            : "Não foi possível carregar a fila.",
        );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [token, tab, city, page, refreshKey]);

  // Keep the inactive tab's badge in sync without blocking the main fetch.
  // The badge respects the active city filter so the numbers match what the
  // tab will actually show when clicked.
  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    const other: Tab = tab === "pending" ? "needs_review" : "pending";

    listAdminJobs(token, {
      status: other,
      city: city ?? undefined,
      page: 1,
      limit: 1,
    })
      .then((result) => {
        if (!cancelled) {
          setCounts((prev) => ({ ...prev, [other]: result.total }));
        }
      })
      .catch(() => {
        // Counts are cosmetic; failures are ignored.
      });

    return () => {
      cancelled = true;
    };
  }, [token, tab, city, refreshKey]);

  const handleTabChange = (next: Tab) => {
    if (next === tab) return;
    setTab(next);
    setPage(1);
    setItems([]);
  };

  const handleCityChange = (next: CitySlug | null) => {
    setCity(next);
    setPage(1);
  };

  const handleApprove = async (job: JobAdmin) => {
    if (!token) return;
    if (mutatingRef.current) {
      toast("Aguarde a operação anterior.", "error");
      return;
    }
    mutatingRef.current = true;
    const snapshot = items;
    const previousTotal = total;
    const previousCounts = counts;

    setItems((prev) => prev.filter((item) => item.id !== job.id));
    setTotal((prev) => Math.max(0, prev - 1));
    setCounts((prev) => ({
      ...prev,
      [tab]: Math.max(0, (prev[tab] ?? 1) - 1),
    }));

    try {
      await approveJob(token, job.id);
      toast("Vaga aprovada e publicada.", "success");
      if (snapshot.length === 1 && page > 1) {
        setPage((prev) => prev - 1);
      } else {
        reload();
      }
    } catch (err) {
      setItems(snapshot);
      setTotal(previousTotal);
      setCounts(previousCounts);
      if (handleAuthError(err)) return;
      const message = err instanceof Error ? err.message : "Falha ao aprovar";
      toast(`Erro: ${message}`, "error");
    } finally {
      mutatingRef.current = false;
    }
  };

  const handleConfirmDelete = async () => {
    if (!token || !deleteTarget) return;
    if (mutatingRef.current) {
      toast("Aguarde a operação anterior.", "error");
      // Re-throw so DeleteConfirmDialog keeps itself open instead of closing
      // as if the delete had succeeded.
      throw new Error("Operação em andamento");
    }
    mutatingRef.current = true;
    const target = deleteTarget;
    const snapshot = items;
    const previousTotal = total;
    const previousCounts = counts;

    setItems((prev) => prev.filter((item) => item.id !== target.id));
    setTotal((prev) => Math.max(0, prev - 1));
    setCounts((prev) => ({
      ...prev,
      [tab]: Math.max(0, (prev[tab] ?? 1) - 1),
    }));

    try {
      await deleteJob(token, target.id);
      toast("Vaga excluída.", "success");
      setDeleteTarget(null);
      if (snapshot.length === 1 && page > 1) {
        setPage((prev) => prev - 1);
      } else {
        reload();
      }
    } catch (err) {
      setItems(snapshot);
      setTotal(previousTotal);
      setCounts(previousCounts);
      if (handleAuthError(err)) throw err;
      const message = err instanceof Error ? err.message : "Falha ao excluir";
      toast(`Erro: ${message}`, "error");
      throw err;
    } finally {
      mutatingRef.current = false;
    }
  };

  const handleSaved = (updated: JobAdmin) => {
    setItems((prev) =>
      prev.map((item) => (item.id === updated.id ? updated : item)),
    );
    setSelectedJob(null);
    reload();
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const renderSkeleton = () => (
    <div className="mt-6 space-y-3" aria-busy="true" aria-hidden="true">
      {Array.from({ length: 6 }).map((_, index) => (
        <div
          key={index}
          className="h-28 animate-pulse rounded-[12px] border border-line bg-surface"
        />
      ))}
    </div>
  );

  const renderEmpty = () => {
    if (city && total === 0) {
      return (
        <div className="mt-8 rounded-lg border border-line bg-surface p-6 text-center">
          <h3 className="text-[14px] font-medium text-fg">
            Nenhuma vaga nesta cidade
          </h3>
          <p className="mt-2 text-[14px] text-fg-muted">
            Remova o filtro de cidade para ver todas.
          </p>
          <button
            type="button"
            onClick={() => handleCityChange(null)}
            className="mt-3 text-[14px] text-accent-soft hover:text-accent"
          >
            Limpar filtro
          </button>
        </div>
      );
    }

    if (tab === "needs_review") {
      return (
        <div className="mt-8 rounded-lg border border-line bg-surface p-6 text-center">
          <h3 className="text-[14px] font-medium text-fg">
            Nenhuma vaga para correção
          </h3>
          <p className="mt-2 text-[14px] text-fg-muted">
            A extração não gerou vagas com defeitos. Volte quando colar um novo
            texto.
          </p>
        </div>
      );
    }

    return (
      <div className="mt-8 rounded-lg border border-line bg-surface p-6 text-center">
        <h3 className="text-[14px] font-medium text-fg">
          Nenhuma vaga pendente
        </h3>
        <p className="mt-2 text-[14px] text-fg-muted">
          Todas as vagas extraídas já foram revisadas. Cole um novo texto em
          &quot;Colar vagas&quot;.
        </p>
      </div>
    );
  };

  return (
    <section className="mt-6">
      <div
        role="tablist"
        aria-label="Status das vagas"
        className="flex flex-wrap gap-2 border-b border-line"
      >
        {(Object.keys(TAB_LABELS) as Tab[]).map((key) => {
          const active = tab === key;
          const count = counts[key];
          return (
            <button
              key={key}
              type="button"
              role="tab"
              id={`review-tab-${key}`}
              aria-selected={active}
              aria-controls="review-tabpanel"
              onClick={() => handleTabChange(key)}
              className={`min-h-11 rounded-t-lg px-4 text-sm transition-colors ${
                active
                  ? "bg-accent-strong font-semibold text-white"
                  : "text-fg-muted hover:text-fg"
              }`}
            >
              {TAB_LABELS[key]}
              {count !== null ? ` (${count})` : ""}
            </button>
          );
        })}
      </div>

      <div
        id="review-tabpanel"
        role="tabpanel"
        aria-labelledby={`review-tab-${tab}`}
      >
        <CityChips selected={city} onChange={handleCityChange} />

        {loading ? (
          <>
            <p role="status" className="sr-only">
              Carregando vagas…
            </p>
            {renderSkeleton()}
          </>
        ) : null}

        {!loading && error ? (
          <div className="mt-6 rounded-lg border border-danger bg-[rgba(248,113,113,0.1)] p-4">
            <p className="text-[14px] text-danger-soft">
              Não foi possível carregar a fila: {error}
            </p>
            <button
              type="button"
              onClick={reload}
              className="mt-2 text-[14px] text-accent-soft hover:text-accent"
            >
              Tentar novamente
            </button>
          </div>
        ) : null}

        {!loading && !error && items.length === 0 ? renderEmpty() : null}

        {!loading && !error && items.length > 0 ? (
          <ul className="mt-6 grid grid-cols-1 gap-3">
            {items.map((job) => (
              <li key={job.id}>
                <ReviewRow
                  job={job}
                  onApprove={() => handleApprove(job)}
                  onEdit={() => {
                    setSelectedJob(job);
                    setEditOpen(true);
                  }}
                  onDelete={() => setDeleteTarget(job)}
                />
              </li>
            ))}
          </ul>
        ) : null}

        {!loading && !error && total > PAGE_SIZE ? (
          <nav
            aria-label="Paginação"
            className="mt-6 flex items-center justify-between gap-3"
          >
            <button
              type="button"
              onClick={() => setPage((prev) => Math.max(1, prev - 1))}
              disabled={page <= 1}
              className="min-h-11 rounded-lg border border-line-strong px-4 text-sm text-fg transition-colors hover:border-accent hover:text-accent-soft disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Anterior
            </button>
            <span className="text-[14px] text-fg-muted">
              Página {page} de {totalPages}
            </span>
            <button
              type="button"
              onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
              disabled={page >= totalPages}
              className="min-h-11 rounded-lg border border-line-strong px-4 text-sm text-fg transition-colors hover:border-accent hover:text-accent-soft disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Próxima
            </button>
          </nav>
        ) : null}
      </div>

      <EditJobDialog
        job={selectedJob}
        token={token}
        open={editOpen}
        onClose={() => setEditOpen(false)}
        onSaved={handleSaved}
      />

      <DeleteConfirmDialog
        open={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleConfirmDelete}
      />
    </section>
  );
}

export default ReviewQueue;
