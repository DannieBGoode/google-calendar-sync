export type AppView = "overview" | "rules" | "activity" | "settings"

export const APP_VIEW_PATHS: Record<AppView, string> = {
  overview: "/overview",
  rules: "/rules",
  activity: "/activity",
  settings: "/settings",
}

const PATH_VIEWS = new Map(
  Object.entries(APP_VIEW_PATHS).map(([view, path]) => [path, view as AppView]),
)

export function appViewFromPathname(pathname: string): AppView {
  const normalized = pathname.length > 1 ? pathname.replace(/\/+$/, "") : pathname
  return PATH_VIEWS.get(normalized) ?? "overview"
}

export function appPathForView(view: AppView): string {
  return APP_VIEW_PATHS[view]
}

export function isKnownAppPath(pathname: string): boolean {
  const normalized = pathname.length > 1 ? pathname.replace(/\/+$/, "") : pathname
  return PATH_VIEWS.has(normalized)
}
