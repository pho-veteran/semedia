import * as React from "react"
import { cn } from "@/lib/utils"

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {}

const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "rounded-xl overflow-hidden",
          "skeleton-shimmer",
          className
        )}
        aria-hidden="true"
        {...props}
      />
    )
  }
)
Skeleton.displayName = "Skeleton"

export function useMinimumLoadingTime(isLoading: boolean, minTime: number = 200): boolean {
  const [showSkeleton, setShowSkeleton] = React.useState(isLoading)
  const loadingStartTime = React.useRef<number | null>(null)

  React.useEffect(() => {
    if (isLoading) {
      loadingStartTime.current = Date.now()
      setShowSkeleton(true)
    } else if (loadingStartTime.current !== null) {
      const elapsed = Date.now() - loadingStartTime.current
      const remaining = Math.max(0, minTime - elapsed)

      if (remaining > 0) {
        const timer = setTimeout(() => {
          setShowSkeleton(false)
          loadingStartTime.current = null
        }, remaining)
        return () => clearTimeout(timer)
      } else {
        setShowSkeleton(false)
        loadingStartTime.current = null
      }
    }
  }, [isLoading, minTime])

  return showSkeleton
}

const SkeletonMediaCard: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn("rounded-2xl overflow-hidden", className)}>
    <Skeleton className="aspect-[16/10] w-full rounded-none" />
    <div className="p-4 space-y-2.5">
      <Skeleton className="h-4 w-3/4 rounded-lg" />
      <Skeleton className="h-3 w-2/5 rounded-lg" />
      <Skeleton className="h-3 w-full rounded-lg" />
      <Skeleton className="h-3 w-5/6 rounded-lg" />
    </div>
  </div>
)
SkeletonMediaCard.displayName = "SkeletonMediaCard"

const SkeletonListItem: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn("flex gap-4 p-4 rounded-2xl border border-border/50", className)}>
    <Skeleton className="h-20 w-28 rounded-xl flex-shrink-0" />
    <div className="flex-1 space-y-2.5 py-1">
      <Skeleton className="h-4 w-3/4 rounded-lg" />
      <Skeleton className="h-3 w-2/5 rounded-lg" />
      <Skeleton className="h-3 w-full rounded-lg" />
    </div>
  </div>
)
SkeletonListItem.displayName = "SkeletonListItem"

const SkeletonSearchResult: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn("rounded-2xl overflow-hidden border border-border/50", className)}>
    <Skeleton className="aspect-[16/10] w-full rounded-none" />
    <div className="p-4 space-y-2">
      <Skeleton className="h-4 w-3/4 rounded-lg" />
      <Skeleton className="h-3 w-1/2 rounded-lg" />
      <div className="flex gap-1.5 pt-1">
        <Skeleton className="h-5 w-16 rounded-full" />
        <Skeleton className="h-5 w-20 rounded-full" />
      </div>
    </div>
  </div>
)
SkeletonSearchResult.displayName = "SkeletonSearchResult"

export { Skeleton, SkeletonMediaCard, SkeletonListItem, SkeletonSearchResult }
