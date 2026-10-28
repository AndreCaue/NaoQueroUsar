import type { SVGProps } from "react";

/**
 * The admin's eight inline icons (UI-SPEC §Design System) — no icon library.
 * 20px default, 1.75 stroke, `currentColor`, decorative by default so a
 * screen reader skips them when the adjacent text already carries the meaning.
 */
interface IconProps extends Omit<SVGProps<SVGSVGElement>, "children"> {
  size?: number;
}

function iconProps({
  size = 20,
  strokeWidth = 1.75,
  className,
  ...props
}: IconProps) {
  return {
    "aria-hidden": true,
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    className,
    ...props,
  };
}

export function Check(props: IconProps) {
  return (
    <svg {...iconProps(props)}>
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}

export function Pencil(props: IconProps) {
  return (
    <svg {...iconProps(props)}>
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5Z" />
    </svg>
  );
}

export function Trash(props: IconProps) {
  return (
    <svg {...iconProps(props)}>
      <path d="M3 6h18" />
      <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
      <path d="M10 11v6" />
      <path d="M14 11v6" />
    </svg>
  );
}

export function Logout(props: IconProps) {
  return (
    <svg {...iconProps(props)}>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <path d="m16 17 5-5-5-5" />
      <path d="M21 12H9" />
    </svg>
  );
}

export function Plus(props: IconProps) {
  return (
    <svg {...iconProps(props)}>
      <path d="M12 5v14" />
      <path d="M5 12h14" />
    </svg>
  );
}

export function X(props: IconProps) {
  return (
    <svg {...iconProps(props)}>
      <path d="M18 6 6 18" />
      <path d="m6 6 12 12" />
    </svg>
  );
}

export function ChevronDown(props: IconProps) {
  return (
    <svg {...iconProps(props)}>
      <path d="m6 9 6 6 6-6" />
    </svg>
  );
}

export function Spinner({ className, ...props }: IconProps) {
  return (
    <svg
      {...iconProps({
        ...props,
        className: ["animate-spin", className].filter(Boolean).join(" "),
      })}
    >
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}
