import { describe, expect, it } from "vitest"

import { accountInitials } from "./account-avatar"

describe("accountInitials", () => {
  it("uses the first and last words of a full display name", () => {
    expect(accountInitials("Daniel Calatayud", "daniel@example.com")).toBe("DC")
  })

  it("uses a structured email name when the display name is only a calendar label", () => {
    expect(accountInitials("Personal", "daniel.calatayud@example.com")).toBe("DC")
  })

  it("falls back safely when identity fields are sparse", () => {
    expect(accountInitials("", "daniel@example.com")).toBe("DA")
    expect(accountInitials("", "")).toBe("?")
  })
})
