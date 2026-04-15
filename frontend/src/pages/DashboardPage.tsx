import { MediaListPanel } from '../components/MediaListPanel'
import { RuntimeBadge } from '../components/RuntimeBadge'
import { UploadDropzone } from '../components/UploadDropzone'
import { UploadQueuePanel } from '../components/UploadQueuePanel'
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
}

export function DashboardPage({
  mediaItems,
  mediaLoading,
  mediaError,
  onFilesSelected,
  onOpenMedia,
  onRefreshMedia,
  runtime,
  runtimeError,
  uploads,
}: DashboardPageProps) {
  return (
    <div className="page-stack">
      <section className="hero-card">
        <div>
          <p className="eyebrow">Phase 4</p>
          <h1>Build the media library first, then search it semantically.</h1>
          <p className="hero-copy">
            This frontend targets the strict CUDA service stack, so uploads reflect the real GPU-backed indexing
            path instead of the old boilerplate flow.
          </p>
        </div>
        <RuntimeBadge error={runtimeError} runtime={runtime} />
      </section>

      <div className="dashboard-grid">
        <div className="dashboard-primary">
          <UploadDropzone onFilesSelected={onFilesSelected} />
          <UploadQueuePanel items={uploads} onOpenMedia={onOpenMedia} />
        </div>
        <div className="dashboard-secondary">
          <MediaListPanel
            error={mediaError}
            items={mediaItems}
            loading={mediaLoading}
            onOpenMedia={onOpenMedia}
            onRefreshMedia={onRefreshMedia}
          />
        </div>
      </div>
    </div>
  )
}
