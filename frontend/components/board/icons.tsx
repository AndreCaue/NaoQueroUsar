import type { SVGProps } from "react";

/**
 * The board's five inline icons (UI-SPEC §Design System) — no icon library.
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

export function Search(props: IconProps) {
  return (
    <svg {...iconProps(props)}>
      <circle cx="11" cy="11" r="7" />
      <path d="m16.5 16.5 4 4" />
    </svg>
  );
}

export function X(props: IconProps) {
  return (
    <svg {...iconProps(props)}>
      <path d="M6 6l12 12" />
      <path d="M18 6 6 18" />
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

export function MapPin(props: IconProps) {
  return (
    <svg {...iconProps(props)}>
      <path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" />
      <circle cx="12" cy="10" r="2.5" />
    </svg>
  );
}

export function Whatsapp(props: IconProps) {
  return (
    <svg {...iconProps(props)}>
      <path d="M21 11.5a8.4 8.4 0 0 1-12.3 7.4L3 20l1.2-5.5A8.4 8.4 0 1 1 21 11.5Z" />
      <path d="M8.6 8.3c.2-.4.4-.4.7-.4h.5c.2 0 .4 0 .5.4l.7 1.6c.1.2 0 .4-.1.6l-.5.6c-.1.2-.1.3 0 .5.4.7 1 1.3 1.8 1.7.2.1.3.1.5-.1l.6-.6c.2-.2.4-.2.6-.1l1.6.7c.3.1.4.3.4.5v.5c0 .3-.1.6-.4.8-.4.3-.9.5-1.5.5-2.9 0-5.3-2.4-5.3-5.3 0-.6.2-1.1.4-1.6Z" />
    </svg>
  );
}
