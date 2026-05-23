import { Activity, Cpu, Zap, WifiOff } from 'lucide-react'
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
          className={cn("flex items-center justify-center w-9 h-9 rounded-xl bg-destructive/10", className)}
          title="Connection Error"
        >
          <WifiOff className="h-4 w-4 text-destructive" />
        </div>
      )
    }

    if (!runtime) {
      return (
        <div
          className={cn("flex items-center justify-center w-9 h-9 rounded-xl bg-muted", className)}
          title="Connecting…"
        >
          <Activity className="h-4 w-4 text-muted-foreground animate-status-pulse" />
        </div>
      )
    }

    const isGPU = runtime.selected_device === 'cuda'
    const deviceName = runtime.gpu_name || 'CPU'

    return (
      <div
        className={cn(
          "flex items-center justify-center w-9 h-9 rounded-xl transition-colors",
          isGPU ? "bg-emerald-500/10" : "bg-amber-500/10",
          className
        )}
        title={isGPU ? `GPU: ${deviceName}` : 'CPU Mode'}
      >
        {isGPU
          ? <Zap className="h-4 w-4 text-emerald-500" />
          : <Cpu className="h-4 w-4 text-amber-500" />
        }
      </div>
    )
  }

  if (error) {
    return (
      <div className={cn(
        "flex items-center gap-2.5 rounded-xl px-3 py-2.5",
        "bg-destructive/8 border border-destructive/15",
        className
      )}>
        <div className="flex items-center justify-center h-7 w-7 rounded-lg bg-destructive/15 flex-shrink-0">
          <WifiOff className="h-3.5 w-3.5 text-destructive" />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-destructive" />
            <span className="text-xs font-semibold text-destructive">Connection Error</span>
          </div>
          <p className="text-[11px] text-muted-foreground truncate mt-0.5">{error}</p>
        </div>
      </div>
    )
  }

  if (!runtime) {
    return (
      <div className={cn(
        "flex items-center gap-2.5 rounded-xl px-3 py-2.5",
        "bg-muted/50 border border-border/50",
        className
      )}>
        <div className="flex items-center justify-center h-7 w-7 rounded-lg bg-muted flex-shrink-0">
          <Activity className="h-3.5 w-3.5 text-muted-foreground animate-status-pulse" />
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/50 animate-status-pulse" />
            <span className="text-xs font-semibold text-muted-foreground">Connecting…</span>
          </div>
          <p className="text-[11px] text-muted-foreground mt-0.5">Initializing runtime</p>
        </div>
      </div>
    )
  }

  const isGPU = runtime.selected_device === 'cuda'
  const deviceName = runtime.gpu_name || 'CPU'
  const deviceCount = runtime.cuda_device_count || 0

  return (
    <div className={cn(
      "flex items-center gap-2.5 rounded-xl px-3 py-2.5",
      "border transition-colors",
      isGPU
        ? "bg-emerald-500/5 border-emerald-500/15"
        : "bg-amber-500/5 border-amber-500/15",
      className
    )}>
      <div className={cn(
        "flex items-center justify-center h-7 w-7 rounded-lg flex-shrink-0",
        isGPU ? "bg-emerald-500/15" : "bg-amber-500/15"
      )}>
        {isGPU
          ? <Zap className="h-3.5 w-3.5 text-emerald-500" />
          : <Cpu className="h-3.5 w-3.5 text-amber-500" />
        }
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <span className={cn(
            "h-1.5 w-1.5 rounded-full",
            isGPU ? "bg-emerald-500" : "bg-amber-500"
          )} />
          <span className="text-xs font-semibold text-foreground">
            {isGPU ? 'GPU Accelerated' : 'CPU Mode'}
          </span>
        </div>
        <p className="text-[11px] text-muted-foreground truncate mt-0.5" title={deviceName}>
          {deviceName}
        </p>
        {isGPU && deviceCount > 0 && (
          <p className="text-[11px] text-muted-foreground mt-0.5 num-tabular">
            {deviceCount} device{deviceCount !== 1 ? 's' : ''} available
          </p>
        )}
      </div>
    </div>
  )
}
