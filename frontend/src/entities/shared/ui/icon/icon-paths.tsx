import type { ReactNode } from "react";

export const iconPaths = {
  sparkles: (
    <>
      <path d="M12 3l1.15 3.1L16 7.3l-2.85 1.15L12 12l-1.15-3.55L8 7.3l2.85-1.2L12 3z" />
      <path d="M6.2 12l.8 2.1 2 .8-2 .8-.8 2.3-.8-2.3-2-.8 2-.8.8-2.1zM17.6 13l.55 1.5 1.45.55-1.45.6-.55 1.55-.6-1.55-1.4-.6 1.4-.55.6-1.5z" />
    </>
  ),
  catalog: (
    <>
      <rect x="4" y="4" width="16" height="16" rx="3" />
      <path d="M8 9h8M8 13h8M8 17h5" />
    </>
  ),
  history: (
    <>
      <path d="M4 12a8 8 0 1 0 2.35-5.65L4 8.7" />
      <path d="M4 4v4l2.7 1.7" />
    </>
  ),
  help: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M9.8 9a2.4 2.4 0 1 1 3.25 2.25c-.8.35-1.05.85-1.05 1.5M12 16.7h.01" />
    </>
  ),
  chevron: <path d="M8.5 10l3.5 3.5 3.5-3.5" />,
  check: <path d="M5 12.5l4.2 4.2L19 7" />,
  alert: (
    <>
      <path d="M12 3l9 16H3l9-16z" />
      <path d="M12 9v4M12 16.2h.01" />
    </>
  ),
  search: (
    <>
      <circle cx="10.5" cy="10.5" r="6.5" />
      <path d="M15.5 15.5L20 20" />
    </>
  ),
  bell: <path d="M6 16h12l-1.3-2V9a4.7 4.7 0 0 0-9.4 0v5L6 16zM10 19h4" />,
  plus: <path d="M12 5v14M5 12h14" />,
  refresh: (
    <>
      <path d="M19 7v5h-5" />
      <path d="M18 12a6.5 6.5 0 1 0-1.9 4.6" />
    </>
  ),
  edit: (
    <>
      <path d="M4 20l4.2-1 10.4-10.4a2.1 2.1 0 0 0-3-3L5.2 16 4 20z" />
      <path d="M14.3 6.9l2.8 2.8" />
    </>
  ),
  trash: <path d="M5 7h14M9 7V4h6v3M7 7l1 13h8l1-13M10 11v5M14 11v5" />,
  arrow: <path d="M5 12h14M15 8l4 4-4 4" />,
  box: (
    <>
      <path d="M4 7.5L12 3l8 4.5v9L12 21l-8-4.5v-9z" />
      <path d="M4.5 7.5L12 12l7.5-4.5M12 12v9" />
    </>
  ),
  sun: (
    <>
      <circle cx="12" cy="12" r="3.5" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </>
  ),
  moon: <path d="M20 15.5A8.5 8.5 0 0 1 8.5 4 8.5 8.5 0 1 0 20 15.5z" />,
} satisfies Record<string, ReactNode>;

export type IconName = keyof typeof iconPaths;
