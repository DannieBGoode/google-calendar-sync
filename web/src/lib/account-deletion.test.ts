import { describe, expect, it } from "vitest"

import dashboardSource from "../features/dashboard.tsx?raw"
import apiSource from "./api.ts?raw"

describe("permanent Connected Account deletion", () => {
  it("keeps disconnect and permanent deletion as separate confirmed actions", () => {
    expect(apiSource).toContain("/disconnect")
    expect(apiSource).toContain("deleteAccount")
    expect(dashboardSource).toContain("Delete account")
    expect(dashboardSource).toContain("Delete permanently")
    expect(dashboardSource).toContain("Managed Projections in Google Calendar will not be deleted")
  })
})
