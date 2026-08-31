import { Moon, Sun } from "lucide-react"

import { useTheme } from "@/components/theme-provider"
import { Button } from "@/components/ui/button"

type ThemeToggleProps = {
  className?: string
}

export function ThemeToggle({ className }: ThemeToggleProps) {
  const { resolvedTheme, setPreference } = useTheme()
  const darkModeEnabled = resolvedTheme === "dark"
  const title = darkModeEnabled ? "Switch to light mode" : "Switch to dark mode"

  return (
    <Button
      type="button"
      className={className}
      variant="ghost"
      size="icon"
      aria-label="Dark mode"
      aria-pressed={darkModeEnabled}
      title={title}
      onClick={() => setPreference(darkModeEnabled ? "light" : "dark")}
    >
      {darkModeEnabled ? <Sun aria-hidden="true" /> : <Moon aria-hidden="true" />}
    </Button>
  )
}
