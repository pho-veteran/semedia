import * as React from "react"
import { cn } from "@/lib/utils"

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {}

const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("animate-pulse rounded-md bg-muted", className)}
        {...props}
      />
    )
  }
)
Skeleton.displayName = "Skeleton"

/**
 * Hook to manage minimum display time for loading states.
 * Ensures skeleton displays for at least minTime milliseconds to prevent flashing.
 * 
 * @param isLoading - Current loading state
 * @param minTime - Minimum display time in milliseconds (default: 200)
 * @returns Whether to show the skeleton
 */
export function useMinimumLoadingTime(isLoading: boolean, minTime: number = 200): boolean {
  const [showSkeleton, setShowSkeleton] = React.useState(isLoading)
  const loadingStartTime = React.useRef<number | null>(null)

  React.useEffect(() => {
    if (isLoading) {
      // Start loading - record start time and show skeleton
      loadingStartTime.current = Date.now()
      setShowSkeleton(true)
    } else if (loadingStartTime.current !== null) {
      // Loading finished - ensure minimum display time
      const elapsed = Date.now() - loadingStartTime.current
      const remaining = Math.max(0, minTime - elapsed)

      if (remaining > 0) {
        // Wait for remaining time before hiding
        const timer = setTimeout(() => {
          setShowSkeleton(false)
          loadingStartTime.current = null
        }, remaining)
        return () => clearTimeout(timer)
      } else {
        // Minimum time already elapsed
        setShowSkeleton(false)
        loadingStartTime.current = null
      }
    }
  }, [isLoading, minTime])

  return showSkeleton
}

/**
 * Pre-built skeleton variant for media card loading states.
 * Displays a card-shaped skeleton with aspect ratio 16/10 and content lines.
 */
const SkeletonMediaCard: React.FC<{ className?: string }> = ({ className }) => {
  return (
    <div className={cn("space-y-3", className)}>
      <Skeleton className="aspect-[16/10] w-full rounded-lg" />
      <div className="space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
        <Skeleton className="h-3 w-full" />
      </div>
    </div>
  )
}
SkeletonMediaCard.displayName = "SkeletonMediaCard"

/**
 * Pre-built skeleton variant for list item loading states.
 * Displays a horizontal layout with thumbnail and text lines.
 */
const SkeletonListItem: React.FC<{ className?: string }> = ({ className }) => {
  return (
    <div className={cn("flex gap-3 p-3", className)}>
      <Skeleton className="h-[80px] w-[120px] rounded-md" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
        <Skeleton className="h-3 w-full" />
      </div>
    </div>
  )
}
SkeletonListItem.displayName = "SkeletonListItem"

/**
 * Pre-built skeleton variant for search result loading states.
 * Similar to media card but optimized for search result layout.
 */
const SkeletonSearchResult: React.FC<{ className?: string }> = ({ className }) => {
  return (
    <div className={cn("space-y-3", className)}>
      <Skeleton className="aspect-[16/10] w-full rounded-lg" />
      <div className="space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
        <Skeleton className="h-3 w-full" />
      </div>
    </div>
  )
}
SkeletonSearchResult.displayName = "SkeletonSearchResult"

export { Skeleton, SkeletonMediaCard, SkeletonListItem, SkeletonSearchResult }
