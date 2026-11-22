export function getChatDetailCloseFocusTarget(
  trigger: HTMLElement | null | undefined,
  fallback: HTMLElement | null | undefined,
): HTMLElement | null {
  if (trigger?.isConnected) return trigger;
  if (fallback?.isConnected) return fallback;
  return null;
}
