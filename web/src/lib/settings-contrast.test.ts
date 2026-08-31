import { readFileSync } from "node:fs"

import { describe, expect, it } from "vitest"

const stylesheet = readFileSync(new URL("../index.css", import.meta.url), "utf8")

describe("Settings status contrast", () => {
  it("uses theme-aware success colors for the access result", () => {
    expect(stylesheet).toContain("border: 1px solid var(--success-border)")
    expect(stylesheet).toContain("background: var(--success-surface)")
    expect(stylesheet).not.toContain("border: 1px solid oklch(0.85 0.035 155)")
    expect(stylesheet).not.toContain("background: oklch(0.975 0.018 155)")
  })
})
