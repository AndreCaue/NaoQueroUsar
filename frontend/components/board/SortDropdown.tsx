"use client";

import { useEffect, useId, useRef, useState } from "react";

import type { Sort } from "@/lib/filters";

interface SortDropdownProps {
  value: Sort;
  onChange: (value: Sort) => void;
}

const OPTIONS: { value: Sort; label: string }[] = [
  { value: "recentes", label: "Mais recentes" },
  { value: "antigas", label: "Mais antigas" },
];

export function SortDropdown({ value, onChange }: SortDropdownProps) {
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(() =>
    Math.max(
      0,
      OPTIONS.findIndex((option) => option.value === value),
    ),
  );

  const rootRef = useRef<HTMLDivElement | null>(null);
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const optionRefs = useRef<Array<HTMLButtonElement | null>>([]);

  const listboxId = useId();
  const selectedIndex = Math.max(
    0,
    OPTIONS.findIndex((option) => option.value === value),
  );
  const activeOptionId = `${listboxId}-option-${activeIndex}`;

  useEffect(() => {
    if (!open) {
      return;
    }

    const handlePointerDown = (event: MouseEvent | TouchEvent) => {
      const target = event.target as Node | null;
      if (target && rootRef.current && !rootRef.current.contains(target)) {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("touchstart", handlePointerDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("touchstart", handlePointerDown);
    };
  }, [open]);

  useEffect(() => {
    if (open) {
      optionRefs.current[activeIndex]?.focus();
    }
  }, [open, activeIndex]);

  const openList = (index = selectedIndex) => {
    setActiveIndex(index);
    setOpen(true);
  };

  const closeList = (restoreFocus = false) => {
    setOpen(false);
    if (restoreFocus) {
      triggerRef.current?.focus();
    }
  };

  const selectOption = (index: number) => {
    const option = OPTIONS[index];
    if (!option) {
      return;
    }
    onChange(option.value);
    setOpen(false);
    triggerRef.current?.focus();
  };

  const moveActive = (delta: number) => {
    setActiveIndex((current) => {
      const next = current + delta;
      if (next < 0) {
        return OPTIONS.length - 1;
      }
      if (next >= OPTIONS.length) {
        return 0;
      }
      return next;
    });
  };

  const handleTriggerKeyDown = (
    event: React.KeyboardEvent<HTMLButtonElement>,
  ) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      if (open) {
        moveActive(1);
      } else {
        openList(selectedIndex);
      }
      return;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      if (open) {
        moveActive(-1);
      } else {
        openList(selectedIndex);
      }
      return;
    }

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      if (open) {
        selectOption(activeIndex);
      } else {
        openList(selectedIndex);
      }
      return;
    }

    if (event.key === "Escape") {
      if (open) {
        event.preventDefault();
        closeList(true);
      }
    }
  };

  const handleOptionKeyDown = (
    event: React.KeyboardEvent<HTMLButtonElement>,
    index: number,
  ) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      moveActive(1);
      return;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      moveActive(-1);
      return;
    }

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      selectOption(index);
      return;
    }

    if (event.key === "Escape") {
      event.preventDefault();
      closeList(true);
      return;
    }

    if (event.key === "Tab") {
      closeList(false);
    }
  };

  const triggerLabel =
    OPTIONS.find((option) => option.value === value)?.label ?? "Mais recentes";

  return (
    <div ref={rootRef} className="relative">
      <button
        ref={triggerRef}
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listboxId}
        aria-label="Ordenar por"
        onClick={() => (open ? closeList(false) : openList(selectedIndex))}
        onKeyDown={handleTriggerKeyDown}
        className={[
          "h-11 w-40 rounded-lg border bg-canvas px-3 text-left text-sm transition-colors",
          "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-soft",
          "hover:border-accent hover:text-accent-soft",
          open
            ? "border-accent text-accent-soft"
            : "border-line-strong text-fg",
        ].join(" ")}
      >
        {triggerLabel}
      </button>

      {open ? (
        <ul
          id={listboxId}
          role="listbox"
          aria-label="Ordenar por"
          aria-activedescendant={activeOptionId}
          className="absolute right-0 z-20 mt-1 w-40 overflow-hidden rounded-lg border border-line bg-surface py-1 shadow-[0_8px_24px_rgba(0,0,0,0.35)]"
        >
          {OPTIONS.map((option, index) => {
            const selected = option.value === value;
            const active = index === activeIndex;
            return (
              <li
                key={option.value}
                role="option"
                aria-selected={selected}
                id={`${listboxId}-option-${index}`}
              >
                <button
                  ref={(element) => {
                    optionRefs.current[index] = element;
                  }}
                  type="button"
                  tabIndex={active ? 0 : -1}
                  onMouseEnter={() => setActiveIndex(index)}
                  onClick={() => selectOption(index)}
                  onKeyDown={(event) => handleOptionKeyDown(event, index)}
                  className={[
                    "flex min-h-11 w-full items-center px-3 text-left text-sm transition-colors",
                    "hover:bg-accent/10 hover:text-accent-soft",
                    active ? "bg-accent/10 text-accent-soft" : "text-fg",
                    selected ? "font-semibold text-accent-soft" : "",
                  ].join(" ")}
                >
                  {option.label}
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}
