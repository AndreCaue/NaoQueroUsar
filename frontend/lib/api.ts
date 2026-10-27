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

/** Partial fields that can be updated by admin via updateJob. */
export interface JobUpdate {
  title?: string;
  company?: string | null;
  activities?: string | null;
  requirements?: string | null;
  salary?: string | null;
  benefits?: string | null;
  city?: string;
  status?: JobStatus;
  contact_email?: string | null;
  contact_phone?: string | null;
  source_snippet?: string | null;
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
 * Admin API base — falls back to localhost for local dev.
 * All admin endpoints are under /api/v1/admin/jobs.
 */
const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
    let detail = `Erro ${res.status}`;
    try {
      const body = await res.json();
      if (body && typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // ignore JSON parse errors
    }
    throw new Error(detail);
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
    let detail = `Erro ${res.status}`;
    try {
      const body = await res.json();
      if (body && typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // ignore JSON parse errors
    }
    throw new Error(detail);
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
    let detail = `Erro ${res.status}`;
    try {
      const body = await res.json();
      if (body && typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // ignore JSON parse errors — the status is still authoritative
    }
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

/** Discarded job snippet. */
export interface DiscardedJob {
  reason: string;
  snippet: string;
}

/** --- Admin helper functions (Task 05-02) --- */

/**
 * List admin jobs with optional filters (status, city) and pagination.
 * GET /api/v1/admin/jobs?status=pending&city=SP&page=1&limit=24
 */
export async function listAdminJobs(
  token: string,
  params?: {
    status?: JobStatus;
    city?: "SP" | "RJ" | "BH" | "Remoto";
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
    let detail = `Erro ${res.status}`;
    try {
      const body = await res.json();
      if (body && typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // ignore JSON parse errors
    }
    throw new Error(detail);
  }

  return (await res.json()) as JobAdminListResponse;
}

/** Approve a job by ID (PATCH /api/v1/admin/jobs/{id}/approve). */
export async function approveJob(token: string, id: string): Promise<JobAdmin> {
  const res = await fetch(`${API}/api/v1/admin/jobs/${id}/approve`, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    let detail = `Erro ${res.status}`;
    try {
      const body = await res.json();
      if (body && typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // ignore JSON parse errors
    }
    throw new Error(detail);
  }

  return (await res.json()) as JobAdmin;
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
    let detail = `Erro ${res.status}`;
    try {
      const body = await res.json();
      if (body && typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // ignore JSON parse errors
    }
    throw new Error(detail);
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
    let detail = `Erro ${res.status}`;
    try {
      const body = await res.json();
      if (body && typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // ignore JSON parse errors
    }
    throw new Error(detail);
  }
}