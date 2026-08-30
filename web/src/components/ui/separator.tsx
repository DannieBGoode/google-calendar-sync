import { cn } from "@/lib/utils"

function Separator({ className }: { className?: string }) {
  return <div aria-hidden="true" className={cn("h-px w-full bg-border", className)} />
}

export { Separator }
