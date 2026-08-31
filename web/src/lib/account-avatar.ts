function firstCharacter(value: string): string {
  return Array.from(value)[0] ?? ""
}

function firstTwoCharacters(value: string): string {
  return Array.from(value).slice(0, 2).join("")
}

function initialsFromParts(parts: string[]): string {
  return `${firstCharacter(parts[0] ?? "")}${firstCharacter(parts.at(-1) ?? "")}`
}

export function accountInitials(displayName: string, email: string): string {
  const nameParts = displayName.trim().split(/\s+/).filter(Boolean)
  if (nameParts.length > 1) return initialsFromParts(nameParts).toLocaleUpperCase()

  const emailName = email.split("@", 1)[0]?.trim() ?? ""
  const emailParts = emailName.split(/[._+-]+/).filter(Boolean)
  if (emailParts.length > 1) return initialsFromParts(emailParts).toLocaleUpperCase()

  const fallback = emailName || nameParts[0] || "?"
  return firstTwoCharacters(fallback).toLocaleUpperCase()
}
