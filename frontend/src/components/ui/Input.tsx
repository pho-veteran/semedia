import * as React from "react"
import { cn } from "@/lib/utils"

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean
  errorMessage?: string
  icon?: React.ReactNode
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, error, errorMessage, icon, ...props }, ref) => {
    return (
      <div className="w-full">
        <div className="relative">
          {icon && (
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-muted-foreground">
              {icon}
            </div>
          )}
          <input
            type={type}
            className={cn(
              "flex h-10 w-full rounded-xl",
              "border border-border/80 bg-background",
              "px-3 py-2 text-sm text-foreground",
              icon && "pl-9",
              "placeholder:text-muted-foreground/60",
              "hover:border-border",
              "focus-visible:outline-none",
              "focus-visible:border-brand/60",
              "focus-visible:ring-4 focus-visible:ring-brand/10",
              "focus-visible:shadow-[0_0_0_1px_hsl(var(--brand)/0.25)]",
              "disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-muted",
              "transition-all duration-150",
              error && "border-destructive/70 focus-visible:border-destructive focus-visible:ring-destructive/10",
              className
            )}
            ref={ref}
            {...props}
          />
        </div>
        {error && errorMessage && (
          <p className="mt-1.5 text-xs text-destructive flex items-center gap-1" role="alert">
            <span className="inline-block h-1 w-1 rounded-full bg-destructive flex-shrink-0" />
            {errorMessage}
          </p>
        )}
      </div>
    )
  }
)
Input.displayName = "Input"

export { Input }
