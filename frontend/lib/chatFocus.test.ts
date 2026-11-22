import { describe, expect, it, vi } from "vitest";

import { getChatDetailCloseFocusTarget } from "./chatFocus";

describe("getChatDetailCloseFocusTarget", () => {
  it("returns trigger when trigger.isConnected is true", () => {
    const trigger = { isConnected: true, focus: vi.fn() } as unknown as HTMLElement;
    const fallback = { isConnected: true, focus: vi.fn() } as unknown as HTMLElement;

    expect(getChatDetailCloseFocusTarget(trigger, fallback)).toBe(trigger);
  });

  it("returns fallback when trigger is disconnected or null and fallback.isConnected is true", () => {
    const disconnectedTrigger = {
      isConnected: false,
      focus: vi.fn(),
    } as unknown as HTMLElement;
    const fallback = { isConnected: true, focus: vi.fn() } as unknown as HTMLElement;

    expect(getChatDetailCloseFocusTarget(disconnectedTrigger, fallback)).toBe(fallback);
    expect(getChatDetailCloseFocusTarget(null, fallback)).toBe(fallback);
  });

  it("returns null when no connected target exists", () => {
    const disconnectedTrigger = {
      isConnected: false,
      focus: vi.fn(),
    } as unknown as HTMLElement;
    const disconnectedFallback = {
      isConnected: false,
      focus: vi.fn(),
    } as unknown as HTMLElement;

    expect(getChatDetailCloseFocusTarget(disconnectedTrigger, disconnectedFallback)).toBeNull();
    expect(getChatDetailCloseFocusTarget(null, null)).toBeNull();
  });

  it("accepts null and undefined safely", () => {
    expect(getChatDetailCloseFocusTarget(undefined, undefined)).toBeNull();
    expect(getChatDetailCloseFocusTarget(null, undefined)).toBeNull();
    expect(getChatDetailCloseFocusTarget(undefined, null)).toBeNull();
  });
});
