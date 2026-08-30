import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Activity, CalendarCheck2, LogOut, Menu, Settings2, Waypoints, X } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { AuthScreen } from "@/features/auth-screen"
import { Dashboard, type AppView } from "@/features/dashboard"
import { api } from "@/lib/api"
import { cn } from "@/lib/utils"

const navItems: { id: AppView; label: string; icon: typeof Waypoints }[] = [
  { id: "overview", label: "Overview", icon: CalendarCheck2 },
  { id: "rules", label: "Rules", icon: Waypoints },
  { id: "activity", label: "Activity", icon: Activity },
  { id: "settings", label: "Settings", icon: Settings2 },
]

export default function App() {
  const setup = useQuery({ queryKey: ["setup"], queryFn: api.setup })
  const session = useQuery({
    queryKey: ["session"],
    queryFn: api.session,
    enabled: setup.data?.administrator_configured === true,
  })

  if (setup.isPending || (setup.data?.administrator_configured && session.isPending)) {
    return <div className="startup-loading" aria-label="Loading Calendar Sync"><Skeleton className="size-12" /><Skeleton className="h-5 w-36" /></div>
  }
  if (setup.error || session.error) {
    return <main className="fatal-state"><h1>Calendar Sync is unavailable</h1><p>The browser could not reach the local service.</p><Button onClick={() => window.location.reload()}>Reload page</Button></main>
  }
  if (!setup.data.administrator_configured) return <AuthScreen mode="setup" />
  if (!session.data?.authenticated) return <AuthScreen mode="login" />
  return <AuthenticatedApp />
}
function AuthenticatedApp() {
  const [view, setView] = useState<AppView>("overview")
  const [mobileNav, setMobileNav] = useState(false)
  const queryClient = useQueryClient()
  const logout = useMutation({ mutationFn: api.logOut, onSuccess: () => queryClient.clear() })

  function changeView(next: AppView) {
    setView(next)
    setMobileNav(false)
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="wordmark" onClick={() => changeView("overview")} aria-label="Calendar Sync overview">
          <span className="wordmark-icon"><CalendarCheck2 /></span><span>Calendar Sync</span>
        </button>
        <nav className={cn("primary-nav", mobileNav && "open")} aria-label="Primary navigation">
          {navItems.map((item) => {
            const Icon = item.icon
            return <button key={item.id} className={cn("nav-item", view === item.id && "active")} onClick={() => changeView(item.id)} aria-current={view === item.id ? "page" : undefined}><Icon /><span>{item.label}</span></button>
          })}
        </nav>
        <div className="topbar-actions">
          <Button variant="ghost" size="sm" onClick={() => logout.mutate()} disabled={logout.isPending}><LogOut /> <span className="desktop-only">Sign out</span></Button>
          <Button className="menu-button" variant="ghost" size="icon" onClick={() => setMobileNav((open) => !open)} aria-expanded={mobileNav} aria-label={mobileNav ? "Close navigation" : "Open navigation"}>{mobileNav ? <X /> : <Menu />}</Button>
        </div>
      </header>
      <main className="app-main"><Dashboard view={view} onViewChange={changeView} /></main>
      <footer className="app-footer"><span>Local installation</span><span aria-hidden="true">·</span><a href="/api/docs">API documentation</a></footer>
    </div>
  )
}
