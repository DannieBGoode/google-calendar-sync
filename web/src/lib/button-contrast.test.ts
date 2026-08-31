import { readFileSync } from "node:fs"

import { describe, expect, it } from "vitest"

import buttonSource from "../components/ui/button.tsx?raw"

const stylesheet = readFileSync(new URL("../index.css", import.meta.url), "utf8")

describe("link-rendered button contrast", () => {
  it("keeps the primary foreground utility free from an unlayered anchor override", () => {
    expect(buttonSource).toContain("bg-primary text-primary-foreground")
    expect(stylesheet).not.toMatch(/(?:^|\n)a\s*\{\s*color:\s*inherit/)
  })
})
