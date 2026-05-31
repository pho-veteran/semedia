import { RefreshCw } from 'lucide-react'
import { Link } from '../components/Link'
import { MediaCard } from '../components/MediaCard'
import { UploadDropzone } from '../components/UploadDropzone'
import { UploadQueuePanel } from '../components/UploadQueuePanel'
import { Button, Card, CardContent, CardHeader, CardTitle, Skeleton, EmptyState } from '../components/ui'
import { cn } from '../lib/utils'
import type { MediaSummary, RuntimeStatus, UploadQueueItem } from '../types/api'

interface DashboardPageProps {
  mediaItems: MediaSummary[]
  mediaLoading: boolean
  mediaError: string | null
  onFilesSelected: (files: File[]) => void
  onOpenMedia: (mediaId: number) => void
  onRefreshMedia: () => void
  runtime: RuntimeStatus | null
  runtimeError: string | null
  uploads: UploadQueueItem[]
  onCancelUpload?: (id: string) => void
  onRetryUpload?: (id: string) => void
}

export function DashboardPage({
  mediaItems,
  mediaLoading,
  mediaError,
  onFilesSelected,
  onOpenMedia,
  onRefreshMedia,
  uploads,
  onCancelUpload,
  onRetryUpload,
}: DashboardPageProps) {
  return (
    <div className="flex flex-col gap-8 animate-fade-in">

      <header className="space-y-1.5">
        <div className="flex items-end gap-2">
          <h1 className="text-4xl font-bold tracking-tight text-foreground">
            <span className="gradient-text">Semantic</span> Media
          </h1>
        </div>
        <p className="text-muted-foreground leading-relaxed">
          Upload images and videos — find anything instantly with AI-powered semantic search.
        </p>
      </header>

      <section aria-label="Upload media">
        <UploadDropzone
          onFilesSelected={onFilesSelected}
          className="min-h-[200px]"
          data-upload-dropzone
        />
      </section>

      {uploads.length > 0 && (
        <section aria-label="Upload queue" className="animate-fade-in-up">
          <UploadQueuePanel
            items={uploads}
            onOpenMedia={onOpenMedia}
            onCancelUpload={onCancelUpload}
            onRetryUpload={onRetryUpload}
          />
        </section>
      )}

      <section aria-label="Recent media">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-4">
            <CardTitle>Recent Media</CardTitle>
            <div className="flex items-center gap-1.5">
              <Button
                variant="ghost"
                size="icon"
                onClick={onRefreshMedia}
                aria-label="Refresh media"
                className="h-8 w-8 text-muted-foreground"
              >
                <RefreshCw size={14} />
              </Button>
              <Button variant="link" size="sm" asChild className="text-brand h-8">
                <Link to="#/library">View All →</Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {mediaLoading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div
                    key={i}
                    className={cn("animate-fade-in", `stagger-${Math.min(i + 1, 8)}`)}
                  >
                    <Skeleton className="aspect-[16/10] w-full rounded-2xl" />
                    <div className="pt-3 px-0.5 space-y-2">
                      <Skeleton className="h-4 w-3/4 rounded-lg" />
                      <Skeleton className="h-3 w-2/5 rounded-lg" />
                    </div>
                  </div>
                ))}
              </div>
            ) : mediaError ? (
              <div className="text-center py-10 text-destructive text-sm">
                {mediaError}
              </div>
            ) : mediaItems.length === 0 ? (
              <EmptyState
                variant="empty-library"
                action={{
                  label: "Upload your first file",
                  onClick: () => {
                    const dropzone = document.querySelector('[data-upload-dropzone]') as HTMLElement
                    if (dropzone) dropzone.scrollIntoView({ behavior: 'smooth', block: 'center' })
                  }
                }}
              />
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {mediaItems.slice(0, 12).map((item, i) => (
                  <div
                    key={item.id}
                    className={cn("animate-fade-in-up", `stagger-${Math.min(i + 1, 8)}`)}
                  >
                    <MediaCard media={item} onClick={onOpenMedia} />
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  )
}
