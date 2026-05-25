const GITHUB_URL = import.meta.env.VITE_GITHUB_URL ?? "#";
const API_DOCS_URL =
  (import.meta.env.VITE_API_BASE ?? "http://localhost:3001").replace(
    /\/$/,
    ""
  ) + "/api/docs";

export function HeaderLinks() {
  return (
    <div className="header-links" data-testid="header-links">
      <a
        href={GITHUB_URL}
        target="_blank"
        rel="noreferrer"
        aria-label="GitHub source"
        data-testid="header-github"
        className="header-link"
      >
        <svg
          width="24"
          height="24"
          viewBox="0 0 16 16"
          aria-hidden="true"
          focusable="false"
          fill="currentColor"
        >
          <path d="M8 0C3.58 0 0 3.58 0 8a8 8 0 005.47 7.59c.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
        </svg>
      </a>
      <a
        href={API_DOCS_URL}
        target="_blank"
        rel="noreferrer"
        aria-label="API Docs"
        data-testid="header-api-docs"
        className="header-link"
      >
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          aria-hidden="true"
          focusable="false"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v17H6.5A2.5 2.5 0 0 0 4 21.5z" />
          <path d="M4 4.5v17" />
          <path d="M8 7h8" />
          <path d="M8 11h8" />
          <path d="M8 15h5" />
        </svg>
      </a>
    </div>
  );
}
