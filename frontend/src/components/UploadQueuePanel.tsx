import { useState, useEffect } from 'react'
import { ChevronDown, X, RotateCcw } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, Button, Badge } from '@/components/ui'
import { cn } from '@/lib/utils'
import type { UploadQueueItem } from '../types/api'
import { formatDateTime } from '../utils/format'

interface UploadQueuePanelProps {
  items: UploadQueueItem[]
  onOpenMedia: (mediaId: number) => void
  onCancelUpload?: (id: string) => void
  onRetryUpload?: (id: string) => void
}

const getStatusColor = (status: UploadQueueItem['status']) => {
  switch (status) {
    case 'uploading':
      return 'bg-blue-100 text-blue-700'
    case 'processing':
      return 'bg-orange-100 text-orange-700'
    case 'completed':
      return 'bg-green-100 text-green-700'
    case 'failed':
      return 'bg-red-100 text-red-700'
    default:
      return 'bg-gray-100 text-gray-700'
  }
}

interface UploadItemProps {
  item: UploadQueueItem
  onOpenMedia: (mediaId: number) => void
  onCancel?: (id: string) => void
  onRetry?: (id: string) => void
}

function UploadItemCard({ item, onOpenMedia, onCancel, onRetry }: UploadItemProps) {
  const [shouldRemove, setShouldRemove] = useState(false)
  const [, setTick] = useState(0)

  // Auto-remove completed items immediately
  useEffect(() => {
    if (item.status === 'completed') {
      setShouldRemove(true)
    }
  }, [item.status])

  // Cleanup preview URL only when component is actually removed
  useEffect(() => {
    return () => {
      if (shouldRemove && item.previewUrl) {
        URL.revokeObjectURL(item.previewUrl)
      }
    }
  }, [shouldRemove, item.previewUrl])

  useEffect(() => {
    if (item.status === 'uploading' || item.status === 'processing') {
      const interval = setInterval(() => {
        setTick(tick => tick + 1)
      }, 1000) 
      
      return () => clearInterval(interval)
    }
  }, [item.status])

  const getProgress = () => {
    switch (item.status) {
      case 'uploading':
        const uploadTime = Date.now() - new Date(item.updatedAt).getTime()
        const estimatedUploadTime = 10000 
        const uploadProgress = Math.min(Math.floor((uploadTime / estimatedUploadTime) * 70), 70)
        return Math.max(uploadProgress, 10) 
      case 'processing':
        const processingTime = Date.now() - new Date(item.updatedAt).getTime()
        const estimatedProcessingTime = 15000 
        const processingProgress = Math.min(Math.floor((processingTime / estimatedProcessingTime) * 20), 20)
        return Math.max(70 + processingProgress, 70) 
      case 'completed':
        return 100
      case 'failed':
        return 0
      default:
        return 0
    }
  }

  const progress = getProgress()
  const canCancel = item.status === 'uploading' || item.status === 'processing'
  const canRetry = item.status === 'failed'

  if (shouldRemove) {
    return null
  }

  return (
    <div 
      className={cn(
        "flex-shrink-0 w-[280px] rounded-lg border border-border bg-card p-3",
        "animate-in slide-in-from-top-2 duration-250"
      )}
    >

      <div className="relative mb-3">
        <div className="w-full aspect-video bg-muted rounded-md overflow-hidden flex items-center justify-center">
          {item.previewUrl ? (
            item.mediaType === 'video' ? (
              <video 
                src={item.previewUrl} 
                className="w-full h-full object-cover"
                preload="metadata"
                muted
                playsInline
              />
            ) : (
              <img 
                src={item.previewUrl} 
                alt={item.name}
                className="w-full h-full object-cover"
              />
            )
          ) : (
            <span className="text-xs text-muted-foreground font-medium">
              {item.name.split('.').pop()?.toUpperCase()}
            </span>
          )}
        </div>
        <Badge className={cn("absolute top-2 left-2 text-xs", getStatusColor(item.status))}>
          {item.status === 'uploading' ? 'Uploading' :
           item.status === 'processing' ? 'Processing' :
           item.status === 'completed' ? 'Completed' :
           item.status === 'failed' ? 'Failed' : 'Pending'}
        </Badge>
      </div>
      
      {/* File info */}
      <div className="space-y-2">
        <p className="text-sm font-medium text-foreground truncate" title={item.name}>
          {item.name}
        </p>
        
        {/* Progress bar */}
        <div className="w-full bg-muted rounded-full h-2">
          <div 
            className={cn(
              "h-2 rounded-full transition-all duration-300",
              item.status === 'uploading' ? 'bg-blue-500' :
              item.status === 'processing' ? 'bg-orange-500' :
              item.status === 'completed' ? 'bg-green-500' :
              item.status === 'failed' ? 'bg-red-500' : 'bg-gray-500'
            )}
            style={{ width: `${progress}%` }}
          />
        </div>
        
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{progress}%</span>
          <span>{formatDateTime(item.updatedAt)}</span>
        </div>
        
        {/* Actions */}
        <div className="flex items-center gap-2 pt-1">
          {canCancel && onCancel && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onCancel(item.id)}
              className="flex-1 h-8"
            >
              <X size={14} className="mr-1" />
              Cancel
            </Button>
          )}
          
          {canRetry && onRetry && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onRetry(item.id)}
              className="flex-1 h-8"
            >
              <RotateCcw size={14} className="mr-1" />
              Retry
            </Button>
          )}
          
          {item.mediaId && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onOpenMedia(item.mediaId!)}
              className="flex-1 h-8"
            >
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
  onRetryUpload 
}: UploadQueuePanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(false)

  // Filter out completed items
  const activeItems = items.filter(item => item.status !== 'completed')

  // Don't render if no active items
  if (activeItems.length === 0) {
    return null
  }

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg" aria-live="polite" aria-atomic="true">
            Upload Queue ({activeItems.length})
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="h-8 w-8 p-0"
            aria-label={isCollapsed ? 'Expand upload queue' : 'Collapse upload queue'}
          >
            <ChevronDown 
              size={16} 
              className={cn(
                "transition-transform duration-200",
                isCollapsed && "rotate-180"
              )} 
            />
          </Button>
        </div>
      </CardHeader>
      
      {!isCollapsed && (
        <CardContent className="pt-0">
          {/* Horizontal scroll container for upload items */}
          <div className="flex gap-3 overflow-x-auto pb-2 -mx-6 px-6">
            {activeItems.map((item) => (
              <UploadItemCard
                key={item.id}
                item={item}
                onOpenMedia={onOpenMedia}
                onCancel={onCancelUpload}
                onRetry={onRetryUpload}
              />
            ))}
          </div>
        </CardContent>
      )}
    </Card>
  )
}
