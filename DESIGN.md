---
name: Google Calendar Sync
description: Calm, trustworthy control for a self-hosted calendar synchronizer
colors:
  status-cobalt: "oklch(0.50 0.16 250)"
  daylight: "oklch(1 0 0)"
  quiet-surface: "oklch(0.975 0.006 250)"
  muted-surface: "oklch(0.955 0.009 250)"
  calm-ink: "oklch(0.20 0.02 250)"
  muted-ink: "oklch(0.43 0.025 250)"
  quiet-border: "oklch(0.89 0.012 250)"
  healthy-soft: "oklch(0.94 0.04 155)"
  healthy-ink: "oklch(0.31 0.09 155)"
  attention-soft: "oklch(0.94 0.055 80)"
  attention-ink: "oklch(0.34 0.08 70)"
  destructive: "oklch(0.50 0.18 25)"
typography:
  headline:
    fontFamily: "Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "2rem"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.025em"
  title:
    fontFamily: "Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "1rem"
    fontWeight: 700
    lineHeight: 1.35
  body:
    fontFamily: "Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "0.85rem"
    fontWeight: 600
    lineHeight: 1.4
rounded:
  sm: "6px"
  md: "8px"
  lg: "10px"
  panel: "12px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "40px"
components:
  button-primary:
    backgroundColor: "{colors.status-cobalt}"
    textColor: "{colors.daylight}"
    rounded: "{rounded.md}"
    padding: "10px 16px"
    height: "40px"
  button-outline:
    backgroundColor: "{colors.daylight}"
    textColor: "{colors.calm-ink}"
    rounded: "{rounded.md}"
    padding: "10px 16px"
    height: "40px"
  input:
    backgroundColor: "{colors.daylight}"
    textColor: "{colors.calm-ink}"
    rounded: "{rounded.md}"
    padding: "8px 12px"
    height: "40px"
  health-badge:
    backgroundColor: "{colors.healthy-soft}"
    textColor: "{colors.healthy-ink}"
    rounded: "999px"
    padding: "4px 10px"
---

# Design System: Google Calendar Sync

## Overview

**Creative North Star: "The Quiet Status Light"**

The interface feels like a quiet kitchen at 7am: cool daylight, familiar controls, and one blue appliance indicator confirming that everything is in order. It serves a nontechnical administrator first, with audit and provider evidence available through progressive disclosure.

The layout uses a restrained top navigation and a readable central work area rather than a permanent dashboard sidebar. Stable information stays flat. Forms and workflows use familiar shadcn/ui affordances, while domain-specific health strips and directional rule rows carry the product language.

**Key Characteristics:**

- Calm operational summaries with specific next actions
- Privacy consequences visible before synchronization begins
- Human language at the surface, diagnostics one level deeper
- Responsive state feedback without decorative entrances
- Structural mobile layouts with unchanged text hierarchy

## Colors

Pure neutral daylight supports a cobalt indicator color, with distinct low-chroma semantic surfaces for health and attention.

### Primary

- **Status Cobalt**: Primary actions, selected navigation, focus, and active setup progress. It is never decorative.

### Secondary

- **Healthy Moss**: Quiet confirmation surfaces and healthy text.
- **Attention Ochre**: Incidents and conditions requiring action.
- **Destructive Red**: Confirmed destructive actions and validation errors only.

### Neutral

- **Daylight**: Main page and field background.
- **Quiet Surface**: Grouped controls, intro panels, and inactive structure.
- **Muted Surface**: Hover, selected-neutral, and skeleton states.
- **Calm Ink**: Primary text.
- **Muted Ink**: Supporting text that still passes body-text contrast.
- **Quiet Border**: Dividers and field boundaries.

### Named Rules

**The Quiet Indicator Rule.** Status Cobalt occupies no more than 10% of a screen. Its rarity makes action and focus immediately legible.

**The Status Is Not Just Color Rule.** Healthy, degraded, running, and failed states always combine color with text and an icon.

## Typography

**Display Font:** Inter with the system sans-serif stack

**Body Font:** Inter with the system sans-serif stack

**Character:** A single humanist-leaning sans family keeps small status labels and longer guidance equally legible. Weight and a compact fixed scale create hierarchy without a display face.

### Hierarchy

- **Headline**: Screen titles at a strong but quiet scale.
- **Title**: Rule names, grouped settings, and recovery headings.
- **Body**: Instructions and explanations, capped near 70 characters per line.
- **Label**: Field labels, navigation, compact state, and metadata in sentence case.

### Named Rules

**The Calendar Language Rule.** Labels use the domain glossary and plain calendar terminology. Provider codes, tokens, and infrastructure terms remain in diagnostic details.

## Elevation

The system is flat by default. Tonal layering, dividers, and spacing establish structure. Only transient menus, dialogs, and toasts may lift above the page; stable panels never use decorative shadows.

### Named Rules

**The Stable Surface Rule.** A shadow signals a temporary layer. If a resting container appears to float, remove the shadow.

## Components

### Buttons

- **Shape:** Gently curved and compact.
- **Primary:** Status Cobalt with white text, reserved for the next meaningful action.
- **Hover / Focus:** A small tonal change and a visible cobalt focus ring over 180 milliseconds.
- **Secondary / Ghost:** Neutral structure for reversible and navigational actions.

### Chips

- **Style:** Full-pill semantic tint with text and an icon.
- **State:** Health, attention, and neutral lifecycle labels use separate named roles.

### Cards / Containers

- **Corner Style:** Panels use the panel radius; list structure often uses dividers with no card at all.
- **Background:** Daylight or Quiet Surface.
- **Shadow Strategy:** None at rest.
- **Border:** One quiet full border only when grouping needs a boundary.
- **Internal Padding:** 16 to 24 pixels depending on workflow density.

### Inputs / Fields

- **Style:** Daylight fill, quiet border, compact curved edge.
- **Focus:** Cobalt border and visible low-opacity ring.
- **Error / Disabled:** Error text accompanies destructive color; disabled controls remain readable and explain their prerequisite nearby.

### Navigation

The desktop top bar uses text labels and a two-pixel active underline. Mobile replaces it with a full-width menu using the same labels and familiar icons. Navigation never competes with the current task.

### Health Strip

A single horizontal summary combines an icon, plain-language state, status badge, and three compact facts. It is a status surface, not a metric-card grid.

## Do's and Don'ts

### Do:

- **Do** lead with current synchronization health and the next meaningful action.
- **Do** make rule direction, privacy policy, and exclusions readable before enablement.
- **Do** use list rhythm and progressive disclosure instead of nesting cards.
- **Do** implement hover, focus, active, disabled, loading, and error states for every control.
- **Do** preserve full keyboard operation, reduced motion, mobile structure, and non-color status cues.

### Don't:

- **Don't** build a generic SaaS analytics dashboard with oversized metric cards, dense decorative charts, promotional copy, or a permanent icon-heavy sidebar.
- **Don't** imitate Google Calendar's visual language or calendar grid.
- **Don't** make setup or recovery resemble a terminal or infrastructure console.
- **Don't** reproduce a Datadog-style observability console with chart walls, compact technical labels, or excessive severity color.
- **Don't** use decorative shadows, gradient text, glass panels, colored side stripes, or display typography in controls.
