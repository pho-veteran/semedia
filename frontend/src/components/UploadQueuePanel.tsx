import { useState, useEffect, useRef } from 'react'
import { ChevronDown, X, RotateCcw, ExternalLink, Film, ImageIcon } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, Button, Badge } from '@/components/ui'
import { cn } from '@/lib/utils'
import type { UploadQueueItem } from '../types/api'

interface UploadQueuePanelProps {
  items: UploadQueueItem[]
  onOpenMedia: (mediaId: number) => void
  onCancelUpload?: (id: string) => void
  onRetryUpload?: (id: string) => void
}

const statusVariant: Record<UploadQueueItem['status'], 'uploading' | 'processing' | 'completed' | 'failed'> = {
  uploading:  'uploading',
  pending:    'uploading',
  processing: 'processing',
  completed:  'completed',
  failed:     'failed',
}

const statusLabel: Record<UploadQueueItem['status'], string> = {
  uploading:  'Uploading',
  pending:    'Pending',
  processing: 'Processing',
  completed:  'Done',
  failed:     'Failed',
}

const statusBarColor: Record<UploadQueueItem['status'], string> = {
  uploading:  'bg-blue-500',
  pending:    'bg-muted-foreground',
  processing: 'bg-amber-500',
  completed:  'bg-emerald-500',
  failed:     'bg-destructive',
}

function VideoPreviewFrame({ src }: { src: string }) {
  const [thumbUrl, setThumbUrl] = useState<string | null>(null)
  const [failed, setFailed] = useState(false)
  const attemptedRef = useRef(false)

  useEffect(() => {
    if (attemptedRef.current) return
    attemptedRef.current = true

    const video = document.createElement('video')
    video.preload = 'auto'  // blob URLs are local — no network cost
    video.muted = true
    video.playsInline = true

    const cleanup = () => {
      video.removeAttribute('src')
      video.load()
    }

    video.addEventListener('loadedmetadata', () => {
      video.currentTime = Math.min(0.5, video.duration || 0)
    }, { once: true })

    video.addEventListener('seeked', () => {
      try {
        const vw = video.videoWidth || 320
        const vh = video.videoHeight || 180
        const scale = Math.min(1, 320 / vw)
        const canvas = document.createElement('canvas')
        canvas.width = Math.round(vw * scale)
        canvas.height = Math.round(vh * scale)
        const ctx = canvas.getContext('2d')
        if (ctx) {
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
          setThumbUrl(canvas.toDataURL('image/jpeg', 0.7))
        }
      } catch {
        setFailed(true)
      }
      cleanup()
    }, { once: true })

    video.addEventListener('error', () => { setFailed(true); cleanup() }, { once: true })

    const timeout = setTimeout(() => { setFailed(true); cleanup() }, 5000)
    video.addEventListener('seeked', () => clearTimeout(timeout), { once: true })
    video.addEventListener('error', () => clearTimeout(timeout), { once: true })

    video.src = src
  }, [src])

  if (thumbUrl) {
    return <img src={thumbUrl} alt="Video preview" className="w-full h-full object-cover" />
  }

  if (failed) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-muted">
        <Film size={20} className="text-muted-foreground/50" />
      </div>
    )
  }

  return (
    <div className="w-full h-full flex items-center justify-center bg-muted animate-pulse">
      <Film size={20} className="text-muted-foreground/30" />
    </div>
  )
}

function UploadItemCard({
  item,
  onOpenMedia,
  onCancel,
  onRetry,
}: {
  item: UploadQueueItem
  onOpenMedia: (mediaId: number) => void
  onCancel?: (id: string) => void
  onRetry?: (id: string) => void
}) {
  const [shouldRemove, setShouldRemove] = useState(false)
  const [, setTick] = useState(0)

  useEffect(() => {
    if (item.status === 'completed') setShouldRemove(true)
  }, [item.status])

  useEffect(() => {
    if (item.status === 'uploading' || item.status === 'processing') {
      const interval = setInterval(() => setTick(t => t + 1), 1000)
      return () => clearInterval(interval)
    }
  }, [item.status])

  useEffect(() => () => {
    if (shouldRemove && item.previewUrl) URL.revokeObjectURL(item.previewUrl)
  }, [shouldRemove, item.previewUrl])

  const getProgress = () => {
    switch (item.status) {
      case 'uploading': {
        const ms = Date.now() - new Date(item.updatedAt).getTime()
        return Math.max(Math.min(Math.floor((ms / 10000) * 70), 70), 10)
      }
      case 'processing': {
        const ms = Date.now() - new Date(item.updatedAt).getTime()
        return Math.max(70 + Math.min(Math.floor((ms / 15000) * 20), 20), 70)
      }
      case 'completed': return 100
      default: return 0
    }
  }

  if (shouldRemove) return null

  const progress = getProgress()
  const canCancel = item.status === 'uploading' || item.status === 'processing'
  const canRetry = item.status === 'failed'

  return (
    <div className={cn(
      "flex-shrink-0 w-[264px] rounded-2xl border border-border/60 bg-card overflow-hidden",
      "shadow-sm animate-fade-in-up",
    )}>
      <div className="relative w-full aspect-video bg-muted overflow-hidden">
        {item.previewUrl ? (
          item.mediaType === 'video' ? (
            <VideoPreviewFrame src={item.previewUrl} />
          ) : (
            <img
              src={item.previewUrl}
              alt={item.name}
              className="w-full h-full object-cover"
            />
          )
        ) : (
          <div className="w-full h-full flex items-center justify-center text-muted-foreground">
            {item.mediaType === 'video'
              ? <Film size={24} strokeWidth={1.5} />
              : <ImageIcon size={24} strokeWidth={1.5} />
            }
          </div>
        )}

        <div className="absolute top-2 left-2">
          <Badge variant={statusVariant[item.status]} className="text-[10px] h-5 px-2 shadow-sm">
            {statusLabel[item.status]}
          </Badge>
        </div>
      </div>

      <div className="px-3 pt-3 pb-3 space-y-2.5">
        <p
          className="text-[13px] font-medium text-foreground truncate"
          title={item.name}
        >
          {item.name}
        </p>

        <div className="space-y-1">
          <div className="w-full rounded-full h-1.5 bg-muted overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full transition-all duration-500",
                statusBarColor[item.status],
                (item.status === 'uploading' || item.status === 'processing') && "relative overflow-hidden",
              )}
              style={{ width: `${progress}%` }}
            >
              {(item.status === 'uploading' || item.status === 'processing') && (
                <span
                  aria-hidden="true"
                  className="absolute inset-0 bg-gradient-to-r from-transparent via-white/25 to-transparent animate-shimmer"
                  style={{ backgroundSize: '200% 100%' }}
                />
              )}
            </div>
          </div>
          <div className="flex justify-between text-[10px] text-muted-foreground num-tabular">
            <span>{progress}%</span>
            {item.status === 'failed' && item.message && (
              <span className="text-destructive truncate max-w-[140px]" title={item.message}>
                {item.message}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          {canCancel && onCancel && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onCancel(item.id)}
              className="h-7 px-2 text-xs text-muted-foreground flex-1"
            >
              <X size={12} className="mr-1" />
              Cancel
            </Button>
          )}
          {canRetry && onRetry && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onRetry(item.id)}
              className="h-7 px-2 text-xs flex-1"
            >
              <RotateCcw size={12} className="mr-1" />
              Retry
            </Button>
          )}
          {item.mediaId && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onOpenMedia(item.mediaId!)}
              className="h-7 px-2 text-xs flex-1"
            >
              <ExternalLink size={12} className="mr-1" />
              Open
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}

export function UploadQueuePanel({
  items,
  onOpenMedia,
  onCancelUpload,
  onRetryUpload,
}: UploadQueuePanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const activeItems = items.filter(item => item.status !== 'completed')

  if (activeItems.length === 0) return null

  const activeCount = activeItems.filter(i => i.status === 'uploading' || i.status === 'processing').length

  return (
    <Card className="w-full overflow-hidden">
      <CardHeader className="pb-3 border-b border-border/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <CardTitle className="text-sm font-semibold">
              Uploads
            </CardTitle>
            <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
              <span className="num-tabular">{activeItems.length}</span> item{activeItems.length !== 1 ? 's' : ''}
              {activeCount > 0 && (
                <>
                  <span>·</span>
                  <span className="text-brand num-tabular">{activeCount} active</span>
                </>
              )}
            </span>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="h-7 w-7"
            aria-label={isCollapsed ? 'Expand upload queue' : 'Collapse upload queue'}
          >
            <ChevronDown
              size={14}
              className={cn(
                "transition-transform duration-200",
                isCollapsed && "rotate-180"
              )}
            />
          </Button>
        </div>
      </CardHeader>

      {!isCollapsed && (
        <CardContent className="pt-4">
          <div className="flex gap-3 overflow-x-auto pb-1 -mx-6 px-6 snap-x snap-mandatory">
            {activeItems.map(item => (
              <div key={item.id} className="snap-start">
                <UploadItemCard
                  item={item}
                  onOpenMedia={onOpenMedia}
                  onCancel={onCancelUpload}
                  onRetry={onRetryUpload}
                />
              </div>
            ))}
          </div>
        </CardContent>
      )}
    </Card>
  )
}
