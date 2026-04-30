import { RefreshCw } from 'lucide-react'
import { Link } from '../components/Link'
import { MediaCard } from '../components/MediaCard'
import { UploadDropzone } from '../components/UploadDropzone'
import { UploadQueuePanel } from '../components/UploadQueuePanel'
import { Button, Card, CardContent, CardHeader, CardTitle, Skeleton, EmptyState } from '../components/ui'
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
    <div className="flex flex-col gap-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Semedia</h1>
          <p className="text-muted-foreground mt-1">
            Upload and manage your semantic media library
          </p>
        </div>
      </header>
      <section aria-label="Upload media">
        <UploadDropzone 
          onFilesSelected={onFilesSelected} 
          className="min-h-[180px]" 
          data-upload-dropzone
        />
      </section>
      {uploads.length > 0 && (
        <section aria-label="Upload queue">
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
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Recent Media</CardTitle>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" onClick={onRefreshMedia} aria-label="Refresh media">
              <RefreshCw size={16} />
            </Button>
            <Button variant="link" asChild>
              <Link to="#/library">View All →</Link>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {mediaLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {Array.from({ length: 12 }).map((_, i) => (
                <div key={i} className="space-y-3">
                  <Skeleton className="aspect-[16/10] w-full rounded-lg" />
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-1/2" />
                </div>
              ))}
            </div>
          ) : mediaError ? (
            <div className="text-center py-8 text-destructive">{mediaError}</div>
          ) : mediaItems.length === 0 ? (
            <EmptyState
              variant="empty-library"
              action={{
                label: "Upload media",
                onClick: () => {
                  const dropzone = document.querySelector('[data-upload-dropzone]')
                  if (dropzone) {
                    dropzone.scrollIntoView({ behavior: 'smooth', block: 'center' })
                  }
                }
              }}
            />
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {mediaItems.slice(0, 12).map((item) => (
                <MediaCard key={item.id} media={item} onClick={onOpenMedia} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      </section>
    </div>
  )
}
