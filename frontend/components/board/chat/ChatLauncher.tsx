"use client";

interface ChatLauncherProps {
  onOpen: () => void;
}

export function ChatLauncher({ onOpen }: ChatLauncherProps) {
  return (
    <button
      type="button"
      aria-label="Abrir busca por chat"
      onClick={onOpen}
      className="fixed bottom-4 right-4 z-40 inline-flex h-11 min-h-11 items-center justify-center gap-2 rounded-full border border-accent bg-surface px-4 text-sm font-semibold text-accent-soft shadow-lg transition-colors hover:border-accent-soft hover:text-fg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft sm:bottom-6 sm:right-6"
    >
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        className="h-5 w-5"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M21 12c0 4.4-4 8-9 8-1.4 0-2.8-.3-4-.8L3 20l1-4.2C3.4 14.7 3 13.4 3 12c0-4.4 4-8 9-8s9 3.6 9 8Z" />
        <path d="M8 12h.01M12 12h.01M16 12h.01" />
      </svg>
      Chat
    </button>
  );
}
