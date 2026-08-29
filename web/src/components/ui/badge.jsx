import * as React from "react"
import { cva } from "class-variance-authority";
import { Slot } from "radix-ui"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex w-fit shrink-0 items-center justify-center gap-1 overflow-hidden border px-2 py-0.5 text-[10px] font-bold tracking-[0.12em] uppercase whitespace-nowrap transition-none focus-visible:outline focus-visible:outline-1 focus-visible:outline-offset-2 [&>svg]:pointer-events-none [&>svg]:size-3",
  {
    variants: {
      variant: {
        default: "border-foreground bg-foreground text-background",
        secondary:
          "border-border bg-transparent text-foreground",
        destructive:
          "border-destructive text-destructive",
        outline:
          "border-border text-muted-foreground",
        ghost: "border-transparent text-muted-foreground",
        link: "border-0 text-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Badge({
  className,
  variant = "default",
  asChild = false,
  ...props
}) {
  const Comp = asChild ? Slot.Root : "span"

  return (
    <Comp
      data-slot="badge"
      data-variant={variant}
      className={cn(badgeVariants({ variant }), className)}
      {...props} />
  );
}

export { Badge, badgeVariants }
