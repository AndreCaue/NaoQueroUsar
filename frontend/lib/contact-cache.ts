import type { ContactRevealResponse } from "@/lib/api";

/**
 * Tab-scoped contact cache (D-10, T-04-13).
 *
 * A revealed contact lives **only** in this module's memory for the lifetime
 * of the tab: reopening the same job shows the contact again without minting a
 * new Turnstile token, and a full reload clears everything.
 *
 * Deliberately NOT persisted anywhere — no `sessionStorage`, `localStorage`,
 * IndexedDB, cookie or URL. This module is imported only by client components,
 * so a server render can never read it (the board HTML must stay contact-free
 * — PUBL-05).
 */
const cache = new Map<string, ContactRevealResponse>();

export function getCachedContact(jobId: string): ContactRevealResponse | null {
  return cache.get(jobId) ?? null;
}

export function setCachedContact(
  jobId: string,
  contact: ContactRevealResponse,
): void {
  cache.set(jobId, contact);
}

/** Test/hot-reload escape hatch — never called by product code. */
export function clearContactCache(): void {
  cache.clear();
}
