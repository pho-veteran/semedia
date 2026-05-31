import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
import { Loader2 } from "lucide-react"

const buttonVariants = cva(
  [
    "inline-flex items-center justify-center gap-2 whitespace-nowrap",
    "font-medium text-sm tracking-tight",
    "rounded-xl border border-transparent",
    "transition-all duration-150 ease-smooth",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
    "disabled:pointer-events-none disabled:opacity-40",
    "active:scale-[0.97]",
    "cursor-pointer select-none",
  ].join(" "),
  {
    variants: {
      variant: {
        default: [
          "bg-brand-gradient text-brand-foreground shadow-md shadow-brand/20",
          "hover:shadow-lg hover:shadow-brand/30 hover:brightness-105",
        ].join(" "),
        secondary: [
          "bg-secondary text-secondary-foreground border-border/60",
          "hover:bg-secondary/70 hover:border-border",
        ].join(" "),
        destructive: [
          "bg-destructive text-destructive-foreground shadow-sm",
          "hover:bg-destructive/90 hover:shadow-md",
        ].join(" "),
        outline: [
          "bg-transparent border-border text-foreground",
          "hover:bg-accent hover:text-accent-foreground hover:border-brand/30",
        ].join(" "),
        ghost: [
          "bg-transparent text-muted-foreground border-transparent",
          "hover:bg-muted hover:text-foreground",
        ].join(" "),
        link: [
          "bg-transparent text-brand border-transparent underline-offset-4",
          "hover:underline hover:text-brand/80",
        ].join(" "),
      },
      size: {
        sm:   "h-8  px-3  text-xs  rounded-lg",
        md:   "h-10 px-4  text-sm  rounded-xl",
        lg:   "h-11 px-6  text-sm  rounded-xl",
        xl:   "h-12 px-8  text-base rounded-2xl",
        icon: "h-9  w-9   rounded-xl",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
  loading?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, loading, disabled, children, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || loading}
        aria-disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <Loader2
            className="h-4 w-4 animate-spin"
            aria-hidden="true"
          />
        )}
        {children}
      </button>
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
