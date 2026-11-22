import { describe, expect, it } from "vitest";

import { buildAdminLoginHref, sanitizeAdminReturnTo } from "./adminReturnTo";

describe("sanitizeAdminReturnTo", () => {
  it("accepts valid admin paths", () => {
    expect(sanitizeAdminReturnTo("/admin/review")).toBe("/admin/review");
    expect(sanitizeAdminReturnTo("/admin/review?page=2")).toBe("/admin/review?page=2");
    expect(sanitizeAdminReturnTo("/admin")).toBe("/admin");
  });

  it("maps /admin/login targets to /admin to prevent loops", () => {
    expect(sanitizeAdminReturnTo("/admin/login")).toBe("/admin");
    expect(sanitizeAdminReturnTo("/admin/login?next=/admin/review")).toBe("/admin");
  });

  it("rejects external, protocol-relative, backslash, and non-admin targets", () => {
    expect(sanitizeAdminReturnTo("https://evil.example")).toBeNull();
    expect(sanitizeAdminReturnTo("//evil.example")).toBeNull();
    expect(sanitizeAdminReturnTo("/\\evil")).toBeNull();
    expect(sanitizeAdminReturnTo("/privacidade")).toBeNull();
  });

  it("rejects empty/nullish values", () => {
    expect(sanitizeAdminReturnTo(null)).toBeNull();
    expect(sanitizeAdminReturnTo(undefined)).toBeNull();
    expect(sanitizeAdminReturnTo("")).toBeNull();
  });
});

describe("buildAdminLoginHref", () => {
  it("builds login href with encoded safe next", () => {
    expect(buildAdminLoginHref("/admin/review")).toBe("/admin/login?next=%2Fadmin%2Freview");
  });

  it("returns plain login href when next is missing/unsafe", () => {
    expect(buildAdminLoginHref(null)).toBe("/admin/login");
  });
});
