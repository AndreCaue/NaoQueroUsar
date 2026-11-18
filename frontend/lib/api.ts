import type { CitySlug } from "./cities";

export type JobStatus = "pending" | "published" | "needs_review" | "invalid";

/**
 * Public job payload (contact-free by design — PUBL-05/D-18).
 *
 * These are exactly the fields the board is allowed to render. The backend
 * guarantees `contact_email`/`contact_phone` never appear in the list/detail
 * response, so the board cannot leak a contact even by accident.
 */
export interface JobPublic {
  id: string;
  title: string;
  company: string | null;
  activities: string | null;
  requirements: string | null;
  salary: string | null;
  benefits: string | null;
  city: string;
  status: JobStatus;
  created_at: string; // ISO 8601
  expires_at: string; // ISO 8601
}

/**
 * Admin job payload — includes contact fields for admin review.
 *
 * This shape is used only behind AdminGuard (token-protected admin routes).
 * Contact fields are stripped from JobPublic and only available here.
 */
export interface JobAdmin {
  id: string;
  title: string;
  company: string | null;
  activities: string | null;
  requirements: string | null;
  salary: string | null;
  benefits: string | null;
  city: string;
  status: JobStatus;
  contact_email: string | null;
  contact_phone: string | null;
  source_snippet: string | null;
  created_at: string; // ISO 8601
  updated_at: string; // ISO 8601
  expires_at: string; // ISO 8601
}

/**
 * Partial fields that can be updated by admin via updateJob.
 *
 * Mirrors the backend `JobUpdate`: status and source_snippet are NOT editable
 * here (Pydantic silently ignores unknown fields, so advertising them would
 * let a caller believe a change was applied when it was not).
 */
export interface JobUpdate {
  title?: string;
  company?: string | null;
  activities?: string | null;
  requirements?: string | null;
  salary?: string | null;
  benefits?: string | null;
  city?: string;
  contact_email?: string | null;
  contact_phone?: string | null;
}

/** Response from listAdminJobs — paginated admin list. */
export interface JobAdminListResponse {
  items: JobAdmin[];
  page: number;
  limit: number;
  total: number;
}

/** Response from list public jobs — paginated public list. */
export interface JobListResponse {
  items: JobPublic[];
  page: number;
  limit: number;
  total: number;
}

/**
 * Summary of job extraction results.
 */
export interface ExtractSummary {
  saved_pending: number;
  saved_needs_review: number;
  discarded: Array<{ reason: string; snippet: string }>;
  divergent: boolean;
  detected_count: number | null;
  extracted_count: number;
  truncated: boolean;
  model_used: string;
  chunks: number;
  alerts: string[];
}

/**
 * Admin API base.
 *
 * Production builds (``next build``, ``NODE_ENV === "production"``) refuse to
 * fall back to localhost: if ``NEXT_PUBLIC_API_URL`` is missing — typo, wrong
 * Vercel scope, renamed variable — the build fails loudly instead of
 * shipping a bundle that sends every request (including the admin password
 * and Turnstile tokens) to the visitor's own machine (WR-04). The localhost
 * fallback exists only for development.
 */
function resolveApiBase(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (fromEnv) {
    return fromEnv;
  }
  if (process.env.NODE_ENV === "production") {
    throw new Error(
      "NEXT_PUBLIC_API_URL is not set. Configure it in the Vercel project " +
        "env (Production scope) — production builds cannot fall back to " +
        "http://localhost:8000.",
    );
  }
  return "http://localhost:8000";
}

const API = resolveApiBase();

/**
 * HTTP error that preserves the status code so callers can react to 401
 * (expired admin session) instead of only showing the message.
 */
export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/**
 * Extract a human-readable message from an error response.
 * FastAPI returns `detail` as a string for HTTPException but as an array for
 * RequestValidationError — flatten both instead of showing "Erro 422".
 */
async function readError(res: Response): Promise<string> {
  const fallback = `Erro ${res.status}`;
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (Array.isArray(body?.detail)) {
      const parts = body.detail
        .map((item: { loc?: (string | number)[]; msg?: string }) =>
          [item.loc?.slice(1).join("."), item.msg].filter(Boolean).join(": "),
        )
        .filter(Boolean);
      if (parts.length > 0) return parts.join("; ");
    }
  } catch {
    // non-JSON body — the status is still authoritative
  }
  return fallback;
}

/**
 * Login admin via password + Cloudflare Turnstile token.
 * Returns JWT access_token stored in sessionStorage as "nqu_admin_token".
 */
export async function loginAdmin(password: string, cfToken: string): Promise<string> {
  const res = await fetch(`${API}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password, cf_token: cfToken }),
  });

  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }

  const body = (await res.json()) as { access_token?: string };
  if (!body.access_token) {
    throw new Error("Token não recebido");
  }
  return body.access_token;
}

/**
 * Extract jobs from raw text using the Groq LLM.
 * Emits ExtractSummary with saved_pending, saved_needs_review, etc.
 */
export async function extractJobs(token: string, text: string): Promise<ExtractSummary> {
  const res = await fetch(`${API}/api/v1/admin/extract`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ text }),
  });

  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }

  return (await res.json()) as ExtractSummary;
}

/**
 * Reveal request budget — a cold backend must fail into a retryable state.
 */
const REVEAL_TIMEOUT_MS = 15_000;

/**
 * Reveal a job's contact behind the Turnstile gate (PUBL-04).
 *
 * The token is single-use: every failure path here means the caller must
 * remount the widget before the next attempt (D-10/T-04-12). Errors carry the
 * backend `detail` verbatim plus `status`/`kind`/`retryAfter` so the UI can
 * pick the approved state without parsing strings.
 */
export async function revealContact(
  jobId: string,
  cfToken: string,
): Promise<ContactRevealResponse> {
  let res: Response;
  try {
    res = await fetch(
      `${API}/api/v1/public/jobs/${encodeURIComponent(jobId)}/reveal-contact`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cf_token: cfToken }),
        signal: AbortSignal.timeout(REVEAL_TIMEOUT_MS),
      },
    );
  } catch (error) {
    const timedOut =
      error instanceof Error &&
      (error.name === "TimeoutError" || error.name === "AbortError");
    throw new RevealError(timedOut ? "timeout" : "network", {
      status: 0,
      kind: timedOut ? "timeout" : "network",
      retryAfter: null,
    });
  }

  if (!res.ok) {
    const detail = await readError(res);
    const retryAfterHeader = res.headers.get("Retry-After");
    const retryAfter = retryAfterHeader
      ? Number.parseInt(retryAfterHeader, 10)
      : Number.NaN;
    throw new RevealError(detail, {
      status: res.status,
      kind: "http",
      retryAfter: Number.isFinite(retryAfter) ? retryAfter : null,
    });
  }

  try {
    return (await res.json()) as ContactRevealResponse;
  } catch {
    throw new RevealError("network", {
      status: 0,
      kind: "network",
      retryAfter: null,
    });
  }
}

/** Contact reveal response shape. */
export interface ContactRevealResponse {
  job_id: string;
  contact_email: string | null;
  contact_phone: string | null;
}

/** Reveal error kind. */
export type RevealErrorKind = "http" | "network" | "timeout";

/** Reveal error class for HTTP and transport failures. */
export class RevealError extends Error {
  /** HTTP status, or `0` for network/timeout failures. */
  readonly status: number;
  readonly kind: RevealErrorKind;
  /** `Retry-After` seconds from a 429, when the header is readable. */
  readonly retryAfter: number | null;

  constructor(
    message: string,
    options: {
      status: number;
      kind: RevealErrorKind;
      retryAfter: number | null;
    },
  ) {
    super(message);
    this.name = "RevealError";
    this.status = options.status;
    this.kind = options.kind;
    this.retryAfter = options.retryAfter;
  }
}

/**
 * Report submit budget — mirrors revealContact: a cold/half-open backend
 * must fail into the dialog's retryable error state, not hang forever.
 */
const REPORT_TIMEOUT_MS = 10_000;

/**
 * Report a job to the master (TRST-02, D-06).
 *
 * Anonymous: no token, no Turnstile. `reason` is optional (max 500 chars,
 * enforced server-side). The backend only logs the report — nothing is
 * persisted and the caller cannot tell whether the job exists; on any
 * non-2xx the `detail` message is surfaced via `ApiError`. A 429 (rate
 * limit, 5/minute per IP) carries the pt-BR message and the `Retry-After`
 * countdown is not exposed here — the dialog renders its own copy.
 */
export async function reportJob(
  jobId: string,
  reason?: string,
): Promise<{ status: string }> {
  const trimmed = reason?.trim();
  let res: Response;
  try {
    res = await fetch(
      `${API}/api/v1/public/jobs/${encodeURIComponent(jobId)}/report`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(trimmed ? { reason: trimmed } : {}),
        signal: AbortSignal.timeout(REPORT_TIMEOUT_MS),
      },
    );
  } catch (error) {
    // Abort/timeout and network failures are retryable — the dialog already
    // renders the "Tentar novamente" path for any thrown error (IN-03).
    const timedOut =
      error instanceof Error &&
      (error.name === "TimeoutError" || error.name === "AbortError");
    throw new ApiError(
      timedOut
        ? "A requisição demorou demais. Verifique sua conexão e tente novamente."
        : "Não foi possível enviar o reporte. Verifique sua conexão e tente novamente.",
      0,
    );
  }

  if (!res.ok) {
    if (res.status === 429) {
      throw new ApiError(
        "Muitas tentativas. Aguarde alguns segundos e tente novamente.",
        429,
      );
    }
    throw new ApiError(await readError(res), res.status);
  }

  return (await res.json()) as { status: string };
}

/** Discarded job snippet. */
export interface DiscardedJob {
  reason: string;
  snippet: string;
}

/** --- Admin helper functions (Task 05-02) --- */

/**
 * List admin jobs with optional filters (status, city) and pagination.
 * GET /api/v1/admin/jobs?status=pending&city=sao-paulo&page=1&limit=24
 *
 * The admin endpoint only accepts `pending` / `needs_review`; `city` is a
 * slug (the backend resolves slug/canonical/label server-side).
 */
export async function listAdminJobs(
  token: string,
  params?: {
    status?: "pending" | "needs_review";
    city?: CitySlug;
    page?: number;
    limit?: number;
  },
): Promise<JobAdminListResponse> {
  const url = new URL(`${API}/api/v1/admin/jobs`);
  if (params) {
    if (params.status) url.searchParams.set("status", params.status);
    if (params.city) url.searchParams.set("city", params.city);
    if (params.page !== undefined) url.searchParams.set("page", String(params.page));
    if (params.limit !== undefined) url.searchParams.set("limit", String(params.limit));
  }

  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }

  return (await res.json()) as JobAdminListResponse;
}

/** --- Social post draft (Phase 16) --- */

export type SocialPublishMode = "publish_now" | "schedule";
export type SocialDraftOrigin = "llm" | "template_fallback";
export type SocialApproveStatus = "registered" | "skipped" | "warning";

export interface SocialPostDraft {
  job_id: string;
  provider: "facebook";
  status: "draft" | "scheduled" | "publishing" | "published" | "failed" | "cancelled";
  text: string;
  publish_mode: SocialPublishMode | null;
  scheduled_at: string | null;
  origin: SocialDraftOrigin | null;
  saved: boolean;
  frozen: boolean;
  warning: string | null;
}

export interface SocialApproveOutcome {
  status: SocialApproveStatus;
  code?: string | null;
  message?: string | null;
}

export interface JobApproveResponse {
  job: JobAdmin;
  social: SocialApproveOutcome;
}

export interface SocialDraftGenerateRequest {
  publish_mode: SocialPublishMode;
  scheduled_date?: string;
  scheduled_time?: string;
  text?: string;
}

export interface SocialDraftSaveRequest {
  publish_mode: SocialPublishMode;
  scheduled_date?: string;
  scheduled_time?: string;
  text?: string;
}

/** Approve a job by ID (PATCH /api/v1/admin/jobs/{id}/approve). */
export async function approveJob(token: string, id: string): Promise<JobApproveResponse> {
  const res = await fetch(`${API}/api/v1/admin/jobs/${id}/approve`, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }

  return (await res.json()) as JobApproveResponse;
}

export async function getSocialDraft(
  token: string,
  jobId: string,
): Promise<SocialPostDraft | null> {
  const res = await fetch(`${API}/api/v1/admin/jobs/${jobId}/social-post`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.status === 404) {
    return null;
  }
  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }
  return (await res.json()) as SocialPostDraft;
}

export async function generateSocialDraft(
  token: string,
  jobId: string,
  payload?: SocialDraftGenerateRequest,
): Promise<SocialPostDraft> {
  const res = await fetch(`${API}/api/v1/admin/jobs/${jobId}/social-post/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: payload ? JSON.stringify(payload) : undefined,
  });
  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }
  return (await res.json()) as SocialPostDraft;
}

export async function saveSocialDraft(
  token: string,
  jobId: string,
  payload: SocialDraftSaveRequest,
): Promise<SocialPostDraft> {
  const res = await fetch(`${API}/api/v1/admin/jobs/${jobId}/social-post`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }
  return (await res.json()) as SocialPostDraft;
}

/** Update a job by ID (PUT /api/v1/admin/jobs/{id}). */
export async function updateJob(token: string, id: string, data: JobUpdate): Promise<JobAdmin> {
  const res = await fetch(`${API}/api/v1/admin/jobs/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }

  return (await res.json()) as JobAdmin;
}

/** Delete a job by ID (DELETE /api/v1/admin/jobs/{id}). */
export async function deleteJob(token: string, id: string): Promise<void> {
  const res = await fetch(`${API}/api/v1/admin/jobs/${id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }
}

/** --- Meta/Facebook integrations (admin) --- */

export interface MetaIntegrationAlert {
  code: string;
  message: string;
}

export interface MetaIntegrationStatus {
  provider: "facebook";
  status: "connected" | "needs_reconnect" | "disconnected";
  page_id: string | null;
  page_name: string | null;
  connected_at: string | null;
  token_checked_at: string | null;
  pending_selection: boolean;
  alert: MetaIntegrationAlert | null;
}

export interface MetaPendingPage {
  page_id: string;
  page_name: string | null;
}

export interface MetaPendingSelectionResponse {
  pending: boolean;
  pages: MetaPendingPage[];
}

export interface MetaSelectPageRequest {
  pending_nonce: string;
  page_id: string;
}

export interface MetaOAuthStartResponse {
  redirect_url: string;
}

export interface MetaActionResponse {
  status: "connected" | "needs_reconnect" | "disconnected";
  message?: string | null;
  pending_selection?: boolean | null;
}

export async function getMetaIntegrationStatus(
  token: string,
): Promise<MetaIntegrationStatus> {
  const res = await fetch(`${API}/api/v1/admin/integrations/meta/status`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }
  return (await res.json()) as MetaIntegrationStatus;
}

export async function startMetaOAuth(
  token: string,
): Promise<MetaOAuthStartResponse> {
  const res = await fetch(`${API}/api/v1/admin/integrations/meta/oauth/start`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }
  return (await res.json()) as MetaOAuthStartResponse;
}

export async function verifyMetaIntegration(
  token: string,
): Promise<MetaIntegrationStatus | MetaActionResponse> {
  const res = await fetch(`${API}/api/v1/admin/integrations/meta/verify`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }
  return (await res.json()) as MetaIntegrationStatus | MetaActionResponse;
}

export async function getMetaPendingSelection(
  token: string,
  pendingNonce: string,
): Promise<MetaPendingSelectionResponse> {
  const url = `${API}/api/v1/admin/integrations/meta/pending-selection?pending=${encodeURIComponent(pendingNonce)}`;
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }
  return (await res.json()) as MetaPendingSelectionResponse;
}

export async function confirmMetaPageSelection(
  token: string,
  payload: MetaSelectPageRequest,
): Promise<MetaIntegrationStatus> {
  const res = await fetch(`${API}/api/v1/admin/integrations/meta/select-page`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }
  return (await res.json()) as MetaIntegrationStatus;
}

export async function disconnectMetaIntegration(
  token: string,
): Promise<MetaIntegrationStatus | MetaActionResponse> {
  const res = await fetch(`${API}/api/v1/admin/integrations/meta/disconnect`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }
  return (await res.json()) as MetaIntegrationStatus | MetaActionResponse;
}

/** --- Admin social publication status/retry (Phase 17) --- */

export type SocialStatusValue =
  | "none"
  | "draft"
  | "scheduled"
  | "publishing"
  | "published"
  | "failed"
  | "cancelled";

export interface SocialPostStatusItem {
  job_id: string;
  job_title?: string | null;
  provider: "facebook";
  status: SocialStatusValue;
  status_label: string;
  last_error: string | null;
  published_url: string | null;
  external_post_id: string | null;
  attempts: number;
  next_retry_at: string | null;
  scheduled_at: string | null;
  published_at: string | null;
  can_retry: boolean;
  retry_block_reason: string | null;
}

export interface SocialPostStatusListResponse {
  items: SocialPostStatusItem[];
  total?: number;
}

export interface SocialRetryResponse {
  outcome?: "retried" | "noop" | "not_eligible" | "not_found";
  item?: SocialPostStatusItem | null;
  message?: string | null;
  status?: string;
}

export async function getSocialStatus(
  token: string,
  jobId: string,
): Promise<SocialPostStatusItem | null> {
  const res = await fetch(`${API}/api/v1/admin/jobs/${jobId}/social-status`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.status === 404) {
    return null;
  }
  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }
  return (await res.json()) as SocialPostStatusItem;
}

export async function getAdminSocialPosts(
  token: string,
  params?: { page?: number; limit?: number },
): Promise<SocialPostStatusListResponse> {
  const url = new URL(`${API}/api/v1/admin/social-posts`);
  if (params?.page !== undefined) url.searchParams.set("page", String(params.page));
  if (params?.limit !== undefined) url.searchParams.set("limit", String(params.limit));
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }
  return (await res.json()) as SocialPostStatusListResponse;
}

export async function retrySocialPost(
  token: string,
  jobId: string,
): Promise<SocialRetryResponse> {
  const res = await fetch(`${API}/api/v1/admin/jobs/${jobId}/social-post/retry`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }
  return (await res.json()) as SocialRetryResponse;
}

/** --- Public chat search (Phase 21) --- */

export type ChatFieldStatus = "aplicado" | "ignorado" | "aproximado";

export interface ChatFieldAssessment {
  field: string;
  understood: unknown;
  applied: unknown;
  status: ChatFieldStatus;
  reason_code: string;
  reason: string;
}

export interface ChatAppliedParams {
  q: string | null;
  city: string | null;
  sort: "recentes" | "antigas" | null;
}

export interface ChatInterpretation {
  understood: Record<string, unknown>;
  field_statuses: ChatFieldAssessment[];
  applied_params: ChatAppliedParams;
  limitations: string[];
  meta: Record<string, unknown> & {
    degraded?: boolean;
    degradation_reason?: string;
    guidance?: string;
  };
}

export interface ChatSearchResults {
  items: JobPublic[];
  page: number;
  limit: number;
  total: number;
}

export interface ChatSearchRequest {
  message: string;
  page?: number;
  limit?: number;
}

export interface ChatSearchResponse {
  interpretation: ChatInterpretation;
  results: ChatSearchResults;
}

export async function chatSearch(
  payload: ChatSearchRequest,
): Promise<ChatSearchResponse> {
  let res: Response;
  try {
    res = await fetch(`${API}/api/v1/public/chat-search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(15_000),
    });
  } catch (error) {
    const timedOut =
      error instanceof Error &&
      (error.name === "TimeoutError" || error.name === "AbortError");
    throw new ApiError(
      timedOut
        ? "A requisição demorou demais. Verifique sua conexão e tente novamente."
        : "Não foi possível buscar agora. Verifique sua conexão e tente novamente.",
      0,
    );
  }

  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }

  return (await res.json()) as ChatSearchResponse;
}