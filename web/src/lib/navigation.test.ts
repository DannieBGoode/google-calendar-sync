import { describe, expect, it } from "vitest"

import { appPathForView, appViewFromPathname, isKnownAppPath } from "./navigation"

describe("application section URLs", () => {
  it.each([
    ["overview", "/overview"],
    ["rules", "/rules"],
    ["activity", "/activity"],
    ["settings", "/settings"],
  ] as const)("maps %s to %s", (view, path) => {
    expect(appPathForView(view)).toBe(path)
    expect(appViewFromPathname(path)).toBe(view)
    expect(isKnownAppPath(path)).toBe(true)
  })

  it("normalizes trailing slashes and falls back to Overview", () => {
    expect(appViewFromPathname("/rules/")).toBe("rules")
    expect(appViewFromPathname("/")).toBe("overview")
    expect(appViewFromPathname("/unknown")).toBe("overview")
    expect(isKnownAppPath("/unknown")).toBe(false)
  })
})
