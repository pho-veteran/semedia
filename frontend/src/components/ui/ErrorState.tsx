import * as React from "react"
import { AlertCircle, type LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "./Button"

export type ErrorStateVariant = "page" | "banner"

interface ErrorStateBaseProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: ErrorStateVariant
  icon?: LucideIcon
  title?: string
  description?: string
  onRetry?: () => void
  retryLabel?: string
}

type ErrorStateProps = ErrorStateBaseProps

const ErrorState = React.forwardRef<HTMLDivElement, ErrorStateProps>(
  (
    {
      className,
      variant = "page",
      icon: CustomIcon,
      title = "Something went wrong",
      description = "An error occurred. Please try again.",
      onRetry,
      retryLabel = "Try again",
      ...props
    },
    ref
  ) => {
    const Icon = CustomIcon || AlertCircle

    if (variant === "banner") {
      return (
        <div
          ref={ref}
          role="alert"
          className={cn(
            "flex items-start gap-3 rounded-lg border border-destructive bg-destructive/10 p-4",
            className
          )}
          {...props}
        >
          <Icon className="text-destructive mt-0.5 flex-shrink-0" size={16} />
          <div className="flex-1 space-y-1">
            <h4 className="text-sm font-semibold text-destructive">{title}</h4>
            {description && (
              <p className="text-sm text-destructive/90">{description}</p>
            )}
          </div>
          {onRetry && (
            <Button
              variant="link"
              size="sm"
              onClick={onRetry}
              className="text-destructive hover:text-destructive/90 h-auto p-0 ml-2"
            >
              {retryLabel}
            </Button>
          )}
        </div>
      )
    }

    // Page variant (default)
    return (
      <div
        ref={ref}
        role="alert"
        className={cn(
          "flex flex-col items-center justify-center py-16 text-center",
          className
        )}
        {...props}
      >
        <Icon className="text-destructive mb-4" size={40} />
        <h3 className="text-lg font-semibold text-foreground">{title}</h3>
        {description && (
          <p className="text-sm text-muted-foreground mt-1 mb-4 max-w-sm">
            {description}
          </p>
        )}
        {onRetry && (
          <Button variant="outline" onClick={onRetry}>
            {retryLabel}
          </Button>
        )}
      </div>
    )
  }
)
ErrorState.displayName = "ErrorState"

export { ErrorState }
