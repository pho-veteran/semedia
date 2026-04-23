import * as React from "react"
import { ImageOff, SearchX, Film, type LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "./Button"

export type EmptyStateVariant = "empty-library" | "no-results" | "no-scenes" | "no-search" | "custom"

interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: EmptyStateVariant
  icon?: LucideIcon
  title?: string
  description?: string
  action?: {
    label: string
    onClick: () => void
  }
}

const variantConfig: Record<
  Exclude<EmptyStateVariant, "custom">,
  {
    icon: LucideIcon
    title: string
    description: string
  }
> = {
  "empty-library": {
    icon: ImageOff,
    title: "No media yet",
    description: "Upload your first image or video to get started.",
  },
  "no-results": {
    icon: SearchX,
    title: "No results found",
    description: "Try different search terms or filters.",
  },
  "no-scenes": {
    icon: Film,
    title: "No scenes detected",
    description: "This video doesn't contain any detectable scenes.",
  },
  "no-search": {
    icon: SearchX,
    title: "Start searching",
    description: "Run a text query or submit a reference image to find matches.",
  },
}

const EmptyState = React.forwardRef<HTMLDivElement, EmptyStateProps>(
  (
    {
      className,
      variant = "custom",
      icon: CustomIcon,
      title: customTitle,
      description: customDescription,
      action,
      ...props
    },
    ref
  ) => {
    const config = variant !== "custom" ? variantConfig[variant] : null
    const Icon = CustomIcon || config?.icon || ImageOff
    const title = customTitle || config?.title || "No content"
    const description = customDescription || config?.description || ""

    return (
      <div
        ref={ref}
        className={cn(
          "flex flex-col items-center justify-center py-16 text-center",
          className
        )}
        {...props}
      >
        <div className="rounded-full bg-muted p-4 mb-4">
          <Icon className="text-muted-foreground" size={32} />
        </div>
        <h3 className="text-lg font-semibold text-foreground mb-1">{title}</h3>
        {description && (
          <p className="text-sm text-muted-foreground mb-4 max-w-sm">
            {description}
          </p>
        )}
        {action && (
          <Button onClick={action.onClick}>{action.label}</Button>
        )}
      </div>
    )
  }
)
EmptyState.displayName = "EmptyState"

export { EmptyState }
