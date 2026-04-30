import { Activity, Cpu, Zap } from 'lucide-react'
import { Card, CardContent } from '@/components/ui'
import { cn } from '@/lib/utils'
import type { RuntimeStatus } from '../types/api'

interface RuntimeBadgeProps {
  runtime: RuntimeStatus | null
  error: string | null
  className?: string
  compact?: boolean
}

export function RuntimeBadge({ runtime, error, className, compact = false }: RuntimeBadgeProps) {
  if (compact) {
    if (error) {
      return (
        <div 
          className={cn("flex items-center justify-center w-8 h-8 rounded-lg bg-destructive/20", className)}
          title="Connection Error"
        >
          <Activity className="h-4 w-4 text-destructive" />
        </div>
      )
    }

    if (!runtime) {
      return (
        <div 
          className={cn("flex items-center justify-center w-8 h-8 rounded-lg bg-muted", className)}
          title="Connecting..."
        >
          <Activity className="h-4 w-4 text-muted-foreground animate-pulse" />
        </div>
      )
    }

    const isGPU = runtime.selected_device === 'cuda'
    const deviceName = runtime.gpu_name || 'CPU'
    const displayTitle = isGPU ? `GPU: ${deviceName}` : 'CPU Mode'

    return (
      <div 
        className={cn(
          "flex items-center justify-center w-8 h-8 rounded-lg",
          isGPU ? "bg-green-500/20" : "bg-yellow-500/20",
          className
        )}
        title={displayTitle}
      >
        {isGPU ? (
          <Zap className="h-4 w-4 text-green-600 dark:text-green-400" />
        ) : (
          <Cpu className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
        )}
      </div>
    )
  }


  if (error) {
    return (
      <Card className={cn("bg-destructive/10 border-destructive/20", className)}>
        <CardContent className="p-3">
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-destructive/20">
              <Activity className="h-4 w-4 text-destructive" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="h-2 w-2 rounded-full bg-red-500" />
                <span className="text-xs font-medium text-destructive">Connection Error</span>
              </div>
              <p className="text-xs text-muted-foreground truncate">{error}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!runtime) {
    return (
      <Card className={cn("bg-muted/50", className)}>
        <CardContent className="p-3">
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
              <Activity className="h-4 w-4 text-muted-foreground animate-pulse" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="h-2 w-2 rounded-full bg-gray-400 animate-pulse" />
                <span className="text-xs font-medium text-muted-foreground">Connecting...</span>
              </div>
              <p className="text-xs text-muted-foreground">Initializing runtime</p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const isGPU = runtime.selected_device === 'cuda'
  const deviceName = runtime.gpu_name || 'CPU'
  const deviceCount = runtime.cuda_device_count || 0

  return (
    <Card className={cn("bg-gradient-to-br from-primary/5 to-primary/10 border-primary/20", className)}>
      <CardContent className="p-3">
        <div className="flex items-start gap-3">
          <div className={cn(
            "flex h-8 w-8 items-center justify-center rounded-lg",
            isGPU ? "bg-green-500/20" : "bg-yellow-500/20"
          )}>
            {isGPU ? (
              <Zap className="h-4 w-4 text-green-600 dark:text-green-400" />
            ) : (
              <Cpu className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className={cn(
                "h-2 w-2 rounded-full",
                isGPU ? "bg-green-500" : "bg-yellow-500"
              )} />
              <span className="text-xs font-medium">
                {isGPU ? 'GPU Accelerated' : 'CPU Mode'}
              </span>
            </div>
            <p className="text-xs text-muted-foreground truncate" title={deviceName}>
              {deviceName}
            </p>
            {isGPU && deviceCount > 0 && (
              <p className="text-xs text-muted-foreground mt-0.5">
                {deviceCount} {deviceCount === 1 ? 'device' : 'devices'} available
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

