import * as React from "react"
import { cva } from "class-variance-authority";
import { Slot } from "radix-ui"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex shrink-0 items-center justify-center gap-2 text-[12px] font-bold tracking-[0.1em] uppercase whitespace-nowrap transition-none outline-none focus-visible:outline focus-visible:outline-1 focus-visible:outline-offset-3 focus-visible:outline-ring disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-3.5",
  {
    variants: {
      variant: {
        default:
          "border border-foreground bg-transparent text-foreground hover:bg-foreground hover:text-background",
        destructive:
          "border border-destructive text-destructive hover:bg-destructive hover:text-background",
        outline:
          "border border-border bg-transparent text-foreground hover:bg-foreground hover:text-background",
        secondary:
          "border border-border bg-secondary text-secondary-foreground hover:bg-foreground hover:text-background",
        ghost:
          "border border-transparent text-foreground hover:bg-foreground hover:text-background",
        link: "border-0 bg-transparent p-0 text-foreground hover:bg-foreground hover:text-background",
      },
      size: {
        default: "h-auto px-4 py-2",
        xs: "h-auto px-2 py-1 text-[11px]",
        sm: "h-auto px-3 py-1.5 text-[11px]",
        lg: "h-auto px-5 py-2.5",
        icon: "size-9",
        "icon-xs": "size-6 [&_svg:not([class*='size-'])]:size-3",
        "icon-sm": "size-8",
        "icon-lg": "size-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant = "default",
  size = "default",
  asChild = false,
  ...props
}) {
  const Comp = asChild ? Slot.Root : "button"

  return (
    <Comp
      data-slot="button"
      data-variant={variant}
      data-size={size}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props} />
  );
}

export { Button, buttonVariants }
