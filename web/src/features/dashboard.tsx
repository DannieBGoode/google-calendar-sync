import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  CircleDot,
  ExternalLink,
  KeyRound,
  Link2,
  Plus,
  RefreshCw,
  ShieldAlert,
} from "lucide-react"
import { useState, type FormEvent } from "react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { NativeSelect } from "@/components/ui/native-select"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import { useTheme } from "@/components/theme-provider"
import { api } from "@/lib/api"
import type { ThemePreference } from "@/lib/theme"

export type AppView = "overview" | "rules" | "activity" | "settings"

export function Dashboard({ view, onViewChange }: { view: AppView; onViewChange: (view: AppView) => void }) {
  const dashboard = useQuery({ queryKey: ["dashboard"], queryFn: api.dashboard })
  const rules = useQuery({ queryKey: ["rules"], queryFn: api.rules })
  const google = useQuery({
    queryKey: ["google-configuration"],
    queryFn: api.googleConfiguration,
  })

  if (dashboard.isPending || rules.isPending || google.isPending) return <DashboardSkeleton />
  if (dashboard.error || rules.error || google.error) {
    return (
      <section className="page-section" role="alert">
        <h1>Calendar Sync could not load</h1>
        <p className="page-intro">Check that the local service is running, then reload this page.</p>
        <Button onClick={() => window.location.reload()}><RefreshCw /> Reload page</Button>
      </section>
    )
  }

  if (view === "rules") return <RulesView rules={rules.data} dashboard={dashboard.data} />
  if (view === "activity") return <ActivityView />
  if (view === "settings") return <SettingsView googleConfigured={google.data.configured} />

  const empty = dashboard.data.connected_accounts === 0
  return (
    <div className="page-section">
      <div className="page-heading-row">
        <div>
          <p className="page-context">Overview</p>
          <h1>{empty ? "Set up your first synchronization" : "Synchronization is healthy"}</h1>
          <p className="page-intro">
            {empty
              ? "Connect a Google identity, choose two calendars, then preview exactly what the rule will create."
              : "Calendar Sync is checking for changes every five minutes."}
          </p>
        </div>
        {!empty && <Button onClick={() => onViewChange("rules")}><RefreshCw /> Review and sync</Button>}
      </div>

      <section className="health-strip" aria-label="Installation health">
        <div className="health-signal">{dashboard.data.health === "healthy" ? <CheckCircle2 aria-hidden="true" /> : <ShieldAlert aria-hidden="true" />}</div>
        <div className="health-copy">
          <div className="health-title-row">
            <h2>{empty ? "Ready for setup" : dashboard.data.health === "healthy" ? "Everything is quiet" : "An incident needs attention"}</h2>
            <Badge variant={dashboard.data.health === "healthy" ? "healthy" : "attention"}><CircleDot aria-hidden="true" /> {dashboard.data.health === "healthy" ? "Healthy" : "Attention"}</Badge>
          </div>
          <p>{empty ? "The service is running and waiting for a connected account." : dashboard.data.health === "healthy" ? "No incidents need your attention." : `${dashboard.data.open_incidents} open incident${dashboard.data.open_incidents === 1 ? "" : "s"}. Open Activity for details.`}</p>
        </div>
        <dl className="health-facts">
          <div><dt>Accounts</dt><dd>{dashboard.data.connected_accounts}</dd></div>
          <div><dt>Rules</dt><dd>{dashboard.data.sync_rules}</dd></div>
          <div><dt>Incidents</dt><dd>{dashboard.data.open_incidents}</dd></div>
        </dl>
      </section>

      {empty ? (
        <OnboardingSteps
          onViewChange={onViewChange}
          googleConfigured={google.data.configured}
        />
      ) : (
        <RecentRules onViewChange={onViewChange} count={rules.data.length} />
      )}
    </div>
  )
}

function OnboardingSteps({
  onViewChange,
  googleConfigured,
}: {
  onViewChange: (view: AppView) => void
  googleConfigured: boolean
}) {
  return (
    <section className="workflow" aria-labelledby="workflow-title">
      <div className="section-heading">
        <div><h2 id="workflow-title">Start with an account</h2><p>Nothing is written to Google until a rule passes preview and you enable it.</p></div>
        <span className="step-progress">Step 1 of 3</span>
      </div>
      <ol className="step-list">
        <li className="step-row current">
          <span className="step-number">1</span>
          <div className="step-content">
            <div><h3>Connect a Google identity</h3><p>Authorize calendar discovery and event access for one Google account.</p></div>
            <div className="step-action">
              <Button
                disabled={!googleConfigured}
                onClick={() => window.location.assign("/api/v1/oauth/google/start")}
              >
                <KeyRound /> Connect Google account <ExternalLink />
              </Button>
              {!googleConfigured && (
                <p className="configuration-note" role="status">
                  Add the master key and Google OAuth credentials in <code>.env</code>, then
                  restart.
                </p>
              )}
            </div>
          </div>
        </li>
        <li className="step-row pending">
          <span className="step-number">2</span>
          <div className="step-content"><div><h3>Create a directional rule</h3><p>Choose one source calendar, one destination calendar, and a privacy policy.</p></div></div>
        </li>
        <li className="step-row pending">
          <span className="step-number">3</span>
          <div className="step-content"><div><h3>Preview and enable</h3><p>Review eligible events and destination projections before the first write.</p></div></div>
        </li>
      </ol>
      <Button variant="ghost" onClick={() => onViewChange("rules")}>Learn how rules work <ArrowRight /></Button>
    </section>
  )
}

function RecentRules({ onViewChange, count }: { onViewChange: (view: AppView) => void; count: number }) {
  return (
    <section className="workflow">
      <div className="section-heading">
        <div><h2>Directional rules</h2><p>{count} configured relationship{count === 1 ? "" : "s"}.</p></div>
        <Button onClick={() => onViewChange("rules")}><Link2 /> View rules</Button>
      </div>
    </section>
  )
}

function RulesView({
  rules,
  dashboard,
}: {
  rules: Awaited<ReturnType<typeof api.rules>>
  dashboard: Awaited<ReturnType<typeof api.dashboard>>
}) {
  const queryClient = useQueryClient()
  const [showBuilder, setShowBuilder] = useState(false)
  const [previews, setPreviews] = useState<Record<string, Awaited<ReturnType<typeof api.previewRule>>>>({})
  const preview = useMutation({
    mutationFn: api.previewRule,
    onSuccess: async (result) => {
      setPreviews((current) => ({ ...current, [result.rule_id]: result }))
      await queryClient.invalidateQueries({ queryKey: ["rules"] })
    },
  })
  const enable = useMutation({
    mutationFn: api.enableRule,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["rules"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      ])
    },
  })
  const sync = useMutation({
    mutationFn: api.syncRule,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["activity"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      ])
    },
  })
  const pause = useMutation({
    mutationFn: api.pauseRule,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["rules"] })
    },
  })
  const reconcile = useMutation({
    mutationFn: api.reconcileRule,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["activity"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      ])
    },
  })

  return (
    <div className="page-section">
      <div className="page-heading-row">
        <div>
          <p className="page-context">Rules</p>
          <h1>Directional sync rules</h1>
          <p className="page-intro">
            Each rule observes one source calendar and manages projections in one destination
            calendar.
          </p>
        </div>
        <Button
          disabled={dashboard.connected_accounts === 0}
          onClick={() => setShowBuilder((visible) => !visible)}
        >
          <Plus /> {showBuilder ? "Close rule builder" : "Create sync rule"}
        </Button>
      </div>
      {showBuilder && <RuleBuilder onCreated={() => setShowBuilder(false)} />}
      {rules.length === 0 ? (
        <section className="empty-panel">
          <div className="empty-icon"><Link2 /></div>
          <h2>No rules yet</h2>
          <p>{dashboard.connected_accounts === 0 ? "Connect a Google account before creating your first rule." : "Create a rule, preview its effects, then enable it."}</p>
          <Button
            disabled={dashboard.connected_accounts === 0}
            onClick={() => setShowBuilder(true)}
          >
            <Plus /> Create sync rule
          </Button>
        </section>
      ) : (
        <div className="rule-list">
          {rules.map((rule) => {
            const latestPreview = previews[rule.id]
            return (
              <div className="rule-row" key={rule.id}>
                <div>
                  <div className="rule-direction">
                    <span>{rule.source.calendar_id}</span><ArrowRight />
                    <span>{rule.destination.calendar_id}</span>
                  </div>
                  <p className="rule-policy">
                    {rule.privacy_policy === "busy_only" ? "Busy only" : "Copy details"}
                    {rule.sync_all_day_events ? ", including all-day events" : ", timed events only"}
                  </p>
                  {latestPreview && (
                    <p className="preview-result" role="status">
                      Preview found {latestPreview.eligible_events} eligible and {latestPreview.excluded_events} excluded events.
                    </p>
                  )}
                </div>
                <div className="rule-actions">
                  <Badge variant={rule.state === "enabled" ? "healthy" : "neutral"}>{rule.state.replaceAll("_", " ")}</Badge>
                  {["draft", "paused", "degraded"].includes(rule.state) && (
                    <Button variant="outline" onClick={() => preview.mutate(rule.id)} disabled={preview.isPending}>
                      {preview.isPending ? "Previewing…" : rule.state === "degraded" ? "Validate recovery" : "Preview rule"}
                    </Button>
                  )}
                  {rule.state === "dry_run_validated" && (
                    <Button onClick={() => enable.mutate(rule.id)} disabled={enable.isPending}>
                      Enable rule
                    </Button>
                  )}
                  {rule.state === "enabled" && (
                    <>
                      <Button variant="outline" onClick={() => sync.mutate(rule.id)} disabled={sync.isPending || reconcile.isPending}>
                        <RefreshCw /> {sync.isPending ? "Syncing…" : "Sync now"}
                      </Button>
                      <Button variant="ghost" onClick={() => reconcile.mutate(rule.id)} disabled={sync.isPending || reconcile.isPending}>
                        {reconcile.isPending ? "Reconciling…" : "Reconcile now"}
                      </Button>
                      <Button variant="ghost" onClick={() => pause.mutate(rule.id)} disabled={sync.isPending || reconcile.isPending || pause.isPending}>
                        {pause.isPending ? "Pausing…" : "Pause"}
                      </Button>
                    </>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
      {(preview.error || enable.error || sync.error || reconcile.error || pause.error) && (
        <div className="inline-error" role="alert">{(preview.error ?? enable.error ?? sync.error ?? reconcile.error ?? pause.error)?.message}</div>
      )}
    </div>
  )
}

function RuleBuilder({ onCreated }: { onCreated: () => void }) {
  const queryClient = useQueryClient()
  const accounts = useQuery({ queryKey: ["accounts"], queryFn: api.accounts })
  const [sourceAccount, setSourceAccount] = useState("")
  const [destinationAccount, setDestinationAccount] = useState("")
  const [sourceCalendar, setSourceCalendar] = useState("")
  const [destinationCalendar, setDestinationCalendar] = useState("")
  const [privacy, setPrivacy] = useState<"busy_only" | "copy_details">("busy_only")
  const [allDay, setAllDay] = useState(true)

  const resolvedSourceAccount = sourceAccount || accounts.data?.[0]?.id || ""
  const resolvedDestinationAccount = destinationAccount || accounts.data?.[0]?.id || ""

  const sourceCalendars = useQuery({
    queryKey: ["calendars", resolvedSourceAccount],
    queryFn: () => api.calendars(resolvedSourceAccount),
    enabled: Boolean(resolvedSourceAccount),
  })
  const destinationCalendars = useQuery({
    queryKey: ["calendars", resolvedDestinationAccount],
    queryFn: () => api.calendars(resolvedDestinationAccount),
    enabled: Boolean(resolvedDestinationAccount),
  })

  const resolvedSourceCalendar = sourceCalendar || sourceCalendars.data?.[0]?.id || ""
  const writableDestination = destinationCalendars.data?.find((calendar) =>
    ["writer", "owner"].includes(calendar.access_role),
  )
  const resolvedDestinationCalendar = destinationCalendar || writableDestination?.id || ""

  const create = useMutation({
    mutationFn: () =>
      api.createRule({
        source: {
          connected_account_id: resolvedSourceAccount,
          calendar_id: resolvedSourceCalendar,
        },
        destination: {
          connected_account_id: resolvedDestinationAccount,
          calendar_id: resolvedDestinationCalendar,
        },
        privacy_policy: privacy,
        sync_all_day_events: allDay,
      }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["rules"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      ])
      onCreated()
    },
  })

  const sameEndpoint =
    resolvedSourceAccount === resolvedDestinationAccount &&
    resolvedSourceCalendar === resolvedDestinationCalendar
  const canSubmit = Boolean(
    resolvedSourceAccount &&
      resolvedDestinationAccount &&
      resolvedSourceCalendar &&
      resolvedDestinationCalendar &&
      !sameEndpoint,
  )

  function submit(event: FormEvent) {
    event.preventDefault()
    if (canSubmit) create.mutate()
  }

  return (
    <section className="rule-builder" aria-labelledby="builder-title">
      <div className="section-heading">
        <div>
          <h2 id="builder-title">Choose the relationship</h2>
          <p>Save a draft first. Preview is required before the rule can be enabled.</p>
        </div>
      </div>
      <form className="rule-form" onSubmit={submit}>
        <fieldset>
          <legend>Source calendar</legend>
          <div className="field-stack">
            <Label htmlFor="source-account">Google identity</Label>
            <NativeSelect id="source-account" value={resolvedSourceAccount} onChange={(event) => { setSourceAccount(event.target.value); setSourceCalendar("") }}>
              {accounts.data?.map((account) => <option key={account.id} value={account.id}>{account.display_name} ({account.email})</option>)}
            </NativeSelect>
          </div>
          <div className="field-stack">
            <Label htmlFor="source-calendar">Calendar</Label>
            <NativeSelect id="source-calendar" value={resolvedSourceCalendar} onChange={(event) => setSourceCalendar(event.target.value)}>
              {sourceCalendars.data?.map((calendar) => <option key={calendar.id} value={calendar.id}>{calendar.summary}</option>)}
            </NativeSelect>
          </div>
        </fieldset>
        <div className="direction-marker" aria-hidden="true"><ArrowRight /></div>
        <fieldset>
          <legend>Destination calendar</legend>
          <div className="field-stack">
            <Label htmlFor="destination-account">Google identity</Label>
            <NativeSelect id="destination-account" value={resolvedDestinationAccount} onChange={(event) => { setDestinationAccount(event.target.value); setDestinationCalendar("") }}>
              {accounts.data?.map((account) => <option key={account.id} value={account.id}>{account.display_name} ({account.email})</option>)}
            </NativeSelect>
          </div>
          <div className="field-stack">
            <Label htmlFor="destination-calendar">Writable calendar</Label>
            <NativeSelect id="destination-calendar" value={resolvedDestinationCalendar} onChange={(event) => setDestinationCalendar(event.target.value)}>
              {destinationCalendars.data?.filter((calendar) => ["writer", "owner"].includes(calendar.access_role)).map((calendar) => <option key={calendar.id} value={calendar.id}>{calendar.summary}</option>)}
            </NativeSelect>
          </div>
        </fieldset>
        <fieldset className="policy-fields">
          <legend>Projection policy</legend>
          <div className="field-stack">
            <Label htmlFor="privacy-policy">Event information</Label>
            <NativeSelect id="privacy-policy" value={privacy} onChange={(event) => setPrivacy(event.target.value as "busy_only" | "copy_details")}>
              <option value="busy_only">Busy only (recommended)</option>
              <option value="copy_details">Copy title, description, and location</option>
            </NativeSelect>
          </div>
          <label className="checkbox-row"><input type="checkbox" checked={allDay} onChange={(event) => setAllDay(event.target.checked)} /><span><strong>Sync all-day events</strong><small>Turn this off to synchronize timed events only.</small></span></label>
        </fieldset>
        {sameEndpoint && <p className="field-error" role="alert">Choose a different destination calendar.</p>}
        {create.error && <div className="inline-error" role="alert">{create.error.message}</div>}
        <div className="form-actions"><Button type="submit" disabled={!canSubmit || create.isPending}>{create.isPending ? "Saving draft…" : "Save rule draft"}</Button></div>
      </form>
    </section>
  )
}

function ActivityView() {
  const activity = useQuery({ queryKey: ["activity"], queryFn: api.activity })
  const incidents = useQuery({ queryKey: ["incidents"], queryFn: api.incidents })
  if (activity.isPending || incidents.isPending) return <DashboardSkeleton />
  if (activity.error || incidents.error) return <div className="inline-error" role="alert">Activity could not be loaded.</div>
  return <div className="page-section"><div><p className="page-context">Activity</p><h1>Incidents and audit activity</h1><p className="page-intro">Operational details appear here without retaining event titles or descriptions.</p></div>
    {incidents.data.length > 0 && <section className="workflow"><div className="section-heading"><div><h2>Incidents</h2><p>Authorization and repeated provider failures that may require attention.</p></div></div><div className="rule-list">{incidents.data.map((incident) => <div className="rule-row" key={incident.id}><div><strong>{incident.summary}</strong><p className="rule-policy">Rule {incident.rule_id ?? "installation"} · Updated {new Date(incident.updated_at).toLocaleString()}</p></div><Badge variant={incident.state === "open" ? "attention" : "neutral"}>{incident.state}</Badge></div>)}</div></section>}
    {activity.data.length === 0 ? <section className="empty-panel"><div className="empty-icon"><Activity /></div><h2>No synchronization activity</h2><p>Activity will appear after an enabled rule completes its first run.</p></section> : <section className="workflow"><div className="section-heading"><div><h2>Latest actions</h2><p>The 100 most recent synchronization decisions.</p></div></div><div className="rule-list">{activity.data.map((entry, index) => <div className="rule-row" key={`${entry.occurred_at}-${entry.rule_id}-${index}`}><div><strong>{entry.action.replaceAll("_", " ")}</strong><p className="rule-policy">{entry.detail} · {new Date(entry.occurred_at).toLocaleString()}</p></div><Badge variant={entry.outcome === "completed" ? "healthy" : "attention"}>{entry.outcome}</Badge></div>)}</div></section>}
  </div>
}

function SettingsView({ googleConfigured }: { googleConfigured: boolean }) {
  const { preference, setPreference } = useTheme()

  return (
    <div className="page-section">
      <div>
        <p className="page-context">Settings</p>
        <h1>Installation settings</h1>
        <p className="page-intro">Operational defaults apply to this self-hosted installation.</p>
      </div>
      <div className="settings-list">
        <div className="setting-row">
          <div>
            <h2>Appearance</h2>
            <p>Follow this device, or keep the interface light or dark in this browser.</p>
          </div>
          <div className="appearance-control">
            <NativeSelect
              id="theme-preference"
              aria-label="Color theme"
              value={preference}
              onChange={(event) => setPreference(event.target.value as ThemePreference)}
            >
              <option value="system">Device setting</option>
              <option value="light">Light</option>
              <option value="dark">Dark</option>
            </NativeSelect>
          </div>
        </div>
        <Separator />
        <div className="setting-row">
          <div>
            <h2>Scheduled sync</h2>
            <p>Check enabled rules for changes every five minutes.</p>
          </div>
          <Badge variant="healthy"><CheckCircle2 /> Active</Badge>
        </div>
        <Separator />
        <div className="setting-row">
          <div>
            <h2>Google authorization</h2>
            <p>Reconnect an identity after an authorization incident, then validate recovery from Rules.</p>
          </div>
          {googleConfigured
            ? <a className="button-link" href="/api/v1/oauth/google/start">Reconnect account</a>
            : <Badge variant="attention">Not configured</Badge>}
        </div>
        <Separator />
        <div className="setting-row">
          <div>
            <h2>Incident notifications</h2>
            <p>Incidents always appear in Activity. Optional SMTP and webhook delivery are configured through the self-hosted environment.</p>
          </div>
          <a className="button-link" href="/api/docs" target="_blank" rel="noreferrer">API docs</a>
        </div>
      </div>
    </div>
  )
}

function DashboardSkeleton() {
  return <div className="page-section" aria-label="Loading overview"><Skeleton className="h-4 w-24" /><Skeleton className="h-10 w-80 max-w-full" /><Skeleton className="h-20 w-full" /><Skeleton className="h-72 w-full" /></div>
}
