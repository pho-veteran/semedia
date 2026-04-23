import { useEffect, useRef, useState } from 'react'
import { ArrowLeft, Download, Link as LinkIcon, Trash2, Film } from 'lucide-react'
import { toast } from 'sonner'
import { deleteMediaById, getMediaDetail } from '../api/client'
import type { MediaDetail, ProcessingStatus } from '../types/api'
import {
  formatFileSize,
  formatRelativeTime,
  formatSeconds,
  toAbsoluteUrl,
} from '../utils/format'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/Dialog'
import { EmptyState } from '../components/ui/EmptyState'
import { Skeleton } from '../components/ui/Skeleton'
import { cn } from '../lib/utils'

interface MediaDetailPageProps {
  initialStartTime: number | null
  mediaId: number
  onBack: () => void
  onDeleted: (mediaId: number) => void | Promise<void>
  onNavigateToMedia: (mediaId: number, startTime: number | null) => void
}

export function MediaDetailPage({
  initialStartTime,
  mediaId,
  onBack,
  onDeleted,
  onNavigateToMedia,
}: MediaDetailPageProps) {
  const [detail, setDetail] = useState<MediaDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [seekTarget, setSeekTarget] = useState<number | null>(initialStartTime)
  const [copySuccess, setCopySuccess] = useState(false)
  const videoRef = useRef<HTMLVideoElement | null>(null)

  useEffect(() => {
    setSeekTarget(initialStartTime)
  }, [initialStartTime, mediaId])

  useEffect(() => {
    let cancelled = false
    let pollTimer: number | undefined

    const loadDetail = async () => {
      try {
        const nextDetail = await getMediaDetail(mediaId)
        if (cancelled) {
          return
        }

        setDetail(nextDetail)
        setError(null)

        if (nextDetail.status === 'pending' || nextDetail.status === 'processing') {
          pollTimer = window.setTimeout(() => {
            void loadDetail()
          }, 3000)
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(requestError instanceof Error ? requestError.message : 'Failed to load media detail.')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    setLoading(true)
    void loadDetail()

    return () => {
      cancelled = true
      if (pollTimer !== undefined) {
        window.clearTimeout(pollTimer)
      }
    }
  }, [mediaId])

  useEffect(() => {
    if (seekTarget === null || !detail || detail.media_type !== 'video') {
      return
    }

    const element = videoRef.current
    if (!element) {
      return
    }

    const applySeek = () => {
      const duration = Number.isFinite(element.duration) ? element.duration : seekTarget
      const safeTarget = Math.min(Math.max(seekTarget, 0), Math.max(duration - 0.1, 0))
      element.currentTime = safeTarget
    }

    if (element.readyState >= 1) {
      applySeek()
      return
    }

    element.addEventListener('loadedmetadata', applySeek, { once: true })
    return () => {
      element.removeEventListener('loadedmetadata', applySeek)
    }
  }, [detail, seekTarget])

  const handleDelete = async () => {
    setDeleting(true)
    setError(null)
    try {
      await deleteMediaById(mediaId)
      toast.success('Media deleted', {
        duration: 5000,
        action: {
          label: 'Undo',
          onClick: () => {
            toast.info('Undo functionality requires backend support - not yet implemented')
          },
        },
      })
      await onDeleted(mediaId)
      setDeleteDialogOpen(false)
    } catch (requestError) {
      const errorMessage = requestError instanceof Error ? requestError.message : 'Delete failed.'
      setError(errorMessage)
      toast.error('Failed to delete media', {
        description: errorMessage,
        duration: 10000,
      })
      setDeleteDialogOpen(false)
    } finally {
      setDeleting(false)
    }
  }

  const handleDownload = () => {
    if (!detail) return
    const link = document.createElement('a')
    link.href = toAbsoluteUrl(detail.file)
    link.download = detail.original_filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const handleShare = async () => {
    if (!detail) return
    const url = window.location.href
    try {
      await navigator.clipboard.writeText(url)
      setCopySuccess(true)
      setTimeout(() => setCopySuccess(false), 3000)
    } catch (err) {
      console.error('Failed to copy URL:', err)
    }
  }

  const handleSceneClick = (startTime: number) => {
    setSeekTarget(startTime)
    onNavigateToMedia(mediaId, startTime)
  }

  const getStatusVariant = (status: ProcessingStatus): 'uploading' | 'processing' | 'completed' | 'failed' => {
    switch (status) {
      case 'pending':
        return 'uploading'
      case 'processing':
        return 'processing'
      case 'completed':
        return 'completed'
      case 'failed':
        return 'failed'
      default:
        return 'completed'
    }
  }

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-3 py-4 md:px-6 md:py-8">
        <Skeleton className="h-8 w-32 mb-6" />
        <div className="grid lg:grid-cols-[1.5fr_1fr] gap-6">
          <div className="space-y-6">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-[400px] w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
          <Skeleton className="h-[600px] w-full" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-3 py-4 md:px-6 md:py-8">
        <Button variant="ghost" size="sm" onClick={onBack} className="mb-6">
          <ArrowLeft size={16} className="mr-1" />
          Back to Library
        </Button>
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">{error}</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!detail) {
    return (
      <div className="max-w-7xl mx-auto px-3 py-4 md:px-6 md:py-8">
        <Button variant="ghost" size="sm" onClick={onBack} className="mb-6">
          <ArrowLeft size={16} className="mr-1" />
          Back to Library
        </Button>
        <EmptyState
          icon={Film}
          title="Media not found"
          description="The requested media item does not exist."
        />
      </div>
    )
  }

  const isVideo = detail.media_type === 'video'

  return (
    <div className="max-w-7xl mx-auto px-3 py-4 md:px-6 md:py-8">
      {/* Breadcrumb and Back Button */}
      <div className="mb-6">
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ArrowLeft size={16} className="mr-1" />
          Back to Library
        </Button>
        <div className="text-sm text-muted-foreground mt-2">
          Dashboard &gt; Library &gt; Media Detail
        </div>
      </div>

      {/* 2-column layout for videos, single column for images */}
      <div className={cn(
        "grid gap-6",
        isVideo && detail.scenes.length > 0 ? "lg:grid-cols-[1.5fr_1fr]" : "grid-cols-1"
      )}>
        {/* Left column: Media + Caption */}
        <div className="space-y-6">
          {/* Metadata header */}
          <div className="space-y-3">
            <h1 className="text-2xl font-bold text-foreground truncate">
              {detail.original_filename}
            </h1>
            
            <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
              <Badge variant={getStatusVariant(detail.status)}>
                {detail.status}
              </Badge>
              <span>·</span>
              <span className="capitalize">{detail.media_type}</span>
              <span>·</span>
              <span>{formatFileSize(detail.file_size)}</span>
              {isVideo && detail.duration !== null && (
                <>
                  <span>·</span>
                  <span>{formatSeconds(detail.duration)}</span>
                </>
              )}
              <span>·</span>
              <span>{formatRelativeTime(detail.uploaded_at)}</span>
            </div>
            
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={handleDownload}>
                <Download size={16} />
                Download
              </Button>
              <Button variant="outline" size="sm" onClick={handleShare}>
                <LinkIcon size={16} />
                {copySuccess ? 'Copied!' : 'Share'}
              </Button>
              <Button 
                variant="destructive" 
                size="sm" 
                onClick={() => setDeleteDialogOpen(true)}
              >
                <Trash2 size={16} />
                Delete
              </Button>
            </div>
          </div>
          
          {/* Media preview */}
          <Card>
            <CardContent className="p-0">
              {isVideo ? (
                <div className="relative w-full aspect-video">
                  <video
                    ref={videoRef}
                    src={toAbsoluteUrl(detail.file)}
                    controls
                    className="w-full h-full object-contain bg-black rounded-lg"
                  />
                </div>
              ) : (
                <div className="relative w-full">
                  <img
                    src={toAbsoluteUrl(detail.file)}
                    alt={detail.original_filename}
                    className="w-full h-auto object-contain rounded-lg"
                  />
                </div>
              )}
            </CardContent>
          </Card>
          
          {/* Caption */}
          <Card>
            <CardHeader>
              <CardTitle>Caption</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-foreground leading-relaxed">
                {detail.caption || detail.error_message || 'No caption available'}
              </p>
            </CardContent>
          </Card>
        </div>
        
        {/* Right column: Video Scenes (only for videos with scenes) */}
        {isVideo && detail.scenes.length > 0 && (
          <div>
            <Card className="lg:sticky lg:top-6">
              <CardHeader>
                <CardTitle>Video Scenes ({detail.scenes.length})</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-[calc(100vh-200px)] overflow-y-auto pr-2">
                  {detail.scenes.map((scene) => (
                    <button
                      key={scene.id}
                      onClick={() => handleSceneClick(scene.start_time)}
                      className="w-full rounded-lg overflow-hidden border border-border hover:border-primary hover:shadow-md transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-ring text-left"
                    >
                      <div className="relative aspect-video">
                        <img
                          src={toAbsoluteUrl(scene.thumbnail_image || scene.keyframe_image)}
                          alt={`Scene ${scene.scene_index + 1}`}
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute top-2 left-2 bg-black/70 text-white text-xs px-2 py-1 rounded-md font-medium">
                          Scene {scene.scene_index + 1}
                        </div>
                      </div>
                      <div className="p-3 bg-card">
                        <div className="text-xs text-muted-foreground font-medium mb-1">
                          {formatSeconds(scene.start_time)} – {formatSeconds(scene.end_time)}
                        </div>
                        <p className="text-sm text-foreground line-clamp-2">
                          {scene.caption || 'No caption available'}
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Empty state for videos without scenes */}
        {isVideo && detail.scenes.length === 0 && (
          <div>
            <Card>
              <CardContent className="pt-6">
                <EmptyState
                  icon={Film}
                  title="No scenes detected"
                  description="This video has not been processed for scene detection yet."
                />
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {/* Delete confirmation dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Media</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{detail.original_filename}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteDialogOpen(false)}
              disabled={deleting}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              loading={deleting}
              disabled={deleting}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
