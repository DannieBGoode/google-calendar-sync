import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useLayoutEffect,
  useMemo,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from "react"

import {
  applyTheme,
  parseThemePreference,
  readThemePreference,
  resolveTheme,
  SYSTEM_DARK_MODE_QUERY,
  THEME_STORAGE_KEY,
  writeThemePreference,
  type ResolvedTheme,
  type ThemePreference,
} from "@/lib/theme"

type ThemeContextValue = {
  preference: ThemePreference
  resolvedTheme: ResolvedTheme
  setPreference: (preference: ThemePreference) => void
}

type ThemeProviderProps = {
  children: ReactNode
  defaultPreference?: ThemePreference
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

function systemPrefersDark(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia(SYSTEM_DARK_MODE_QUERY).matches
  )
}

function subscribeToSystemPreference(onChange: () => void): () => void {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") return () => {}

  const mediaQuery = window.matchMedia(SYSTEM_DARK_MODE_QUERY)
  mediaQuery.addEventListener("change", onChange)
  return () => mediaQuery.removeEventListener("change", onChange)
}

export function ThemeProvider({ children, defaultPreference = "system" }: ThemeProviderProps) {
  const [preference, setPreferenceState] = useState<ThemePreference>(
    () => readThemePreference() ?? defaultPreference,
  )
  const prefersDark = useSyncExternalStore(
    subscribeToSystemPreference,
    systemPrefersDark,
    () => false,
  )
  const resolvedTheme = resolveTheme(preference, prefersDark)

  const setPreference = useCallback((nextPreference: ThemePreference) => {
    setPreferenceState(nextPreference)
    writeThemePreference(nextPreference)
  }, [])

  useLayoutEffect(() => {
    applyTheme(resolvedTheme)
  }, [resolvedTheme])

  useEffect(() => {
    if (typeof window === "undefined") return

    const handleStorage = (event: StorageEvent) => {
      if (event.key !== THEME_STORAGE_KEY && event.key !== null) return
      setPreferenceState(parseThemePreference(event.newValue) ?? defaultPreference)
    }

    window.addEventListener("storage", handleStorage)
    return () => window.removeEventListener("storage", handleStorage)
  }, [defaultPreference])

  const value = useMemo(
    () => ({ preference, resolvedTheme, setPreference }),
    [preference, resolvedTheme, setPreference],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

// The hook and provider intentionally share their private context boundary.
// eslint-disable-next-line react-refresh/only-export-components
export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext)
  if (!context) throw new Error("useTheme must be used within a ThemeProvider")
  return context
}
