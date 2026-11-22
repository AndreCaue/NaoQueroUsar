const ADMIN_LOGIN_PATH = "/admin/login";

function hasControlChars(value: string): boolean {
  for (let i = 0; i < value.length; i += 1) {
    const code = value.charCodeAt(i);
    if (code < 32 || code === 127) return true;
  }
  return false;
}

function getPathname(value: string): string {
  const match = /^[^?#]*/.exec(value);
  return match ? match[0] : value;
}

export function sanitizeAdminReturnTo(value: string | null | undefined): string | null {
  if (value == null) return null;
  if (typeof value !== "string") return null;

  const trimmed = value.trim();
  if (!trimmed) return null;
  if (hasControlChars(trimmed)) return null;
  if (!trimmed.startsWith("/admin")) return null;
  if (trimmed.startsWith("//")) return null;
  if (trimmed.includes("\\")) return null;

  const pathname = getPathname(trimmed);
  if (
    pathname === ADMIN_LOGIN_PATH ||
    pathname.startsWith(`${ADMIN_LOGIN_PATH}/`)
  ) {
    return "/admin";
  }

  return trimmed;
}

export function buildAdminLoginHref(next: string | null | undefined): string {
  const safe = sanitizeAdminReturnTo(next);
  if (!safe) return ADMIN_LOGIN_PATH;
  return `${ADMIN_LOGIN_PATH}?next=${encodeURIComponent(safe)}`;
}
