import type { JobListResponse, JobPublic } from "@/lib/api";
import { PAGE_SIZE, toApiParams, type Filters } from "@/lib/filters";

/**
 * Server-side board fetches (D-07/D-08).
 *
 * `BACKEND_API_URL` is read first on purpose: `NEXT_PUBLIC_*` is inlined at
 * BUILD time, so a server fetch keyed off it would pin the build machine's URL
 * in production. The public fallback keeps the existing local `.env.local`
 * working unchanged.
 *
 * Every request is `cache: "no-store"` with a 15 s timeout: the board must
 * never serve a build-time snapshot, and a cold backend must surface a real
 * timeout state instead of hanging the render.
 */
const API =
  process.env.BACKEND_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

const TIMEOUT_MS = 15_000;

export type BoardErrorKind = "timeout" | "http" | "network";

/**
 * Board fetch failure. `message` is the kind so the client error boundary can
 * pick the cold-start copy without importing this server module.
 */
export class BoardError extends Error {
  readonly kind: BoardErrorKind;
  readonly status?: number;

  constructor(kind: BoardErrorKind, status?: number) {
    super(kind);
    this.name = "BoardError";
    this.kind = kind;
    this.status = status;
  }
}

async function request(path: string): Promise<Response> {
  try {
    return await fetch(`${API}${path}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
  } catch (error) {
    if (
      error instanceof Error &&
      (error.name === "TimeoutError" || error.name === "AbortError")
    ) {
      throw new BoardError("timeout");
    }
    throw new BoardError("network");
  }
}

async function parseJson<T>(response: Response): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch {
    throw new BoardError("network");
  }
}

export async function fetchBoard(filters: Filters): Promise<JobListResponse> {
  const params = new URLSearchParams(toApiParams(filters));
  params.set("limit", String(PAGE_SIZE));

  const response = await request(`/api/v1/public/jobs?${params.toString()}`);
  if (!response.ok) {
    throw new BoardError("http", response.status);
  }
  return parseJson<JobListResponse>(response);
}

/** Contact-free public detail; `null` means 404 (missing or expired). */
export async function fetchJob(id: string): Promise<JobPublic | null> {
  const response = await request(
    `/api/v1/public/jobs/${encodeURIComponent(id)}`,
  );
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new BoardError("http", response.status);
  }
  return parseJson<JobPublic>(response);
}
