import type { MediaSummary } from '../types/api'
import { formatDateTime, formatFileSize, formatStatusLabel, toAbsoluteUrl } from '../utils/format'

interface MediaListPanelProps {
  items: MediaSummary[]
  loading: boolean
  error: string | null
  onOpenMedia: (mediaId: number) => void
  onRefreshMedia: () => void
}

export function MediaListPanel({
  items,
  loading,
  error,
  onOpenMedia,
  onRefreshMedia,
}: MediaListPanelProps) {
  return (
    <section className="panel">
      <header className="panel-header">
        <div>
          <p className="eyebrow">Library</p>
          <h2>Recent Media</h2>
        </div>
        <button className="button button-secondary" onClick={onRefreshMedia} type="button">
          Refresh
        </button>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}

      {loading ? <div className="empty-state">Loading media from the backend…</div> : null}

      {!loading && items.length === 0 ? (
        <div className="empty-state">No media indexed yet. Upload an image or video to populate the library.</div>
      ) : null}

      <div className="media-history-list">
        {items.map((item) => {
          const previewUrl = item.media_type === 'image' ? toAbsoluteUrl(item.file) : ''

          return (
            <button
              className="media-history-card"
              key={item.id}
              onClick={() => onOpenMedia(item.id)}
              type="button"
            >
              <div className="media-history-preview">
                {previewUrl ? (
                  <img alt={item.original_filename} src={previewUrl} />
                ) : (
                  <div className="video-placeholder">
                    <span>Video</span>
                    <strong>{item.scene_count} scenes</strong>
                  </div>
                )}
              </div>
              <div className="media-history-copy">
                <div className="media-history-row">
                  <h3>{item.original_filename}</h3>
                  <span className={`status-pill status-${item.status}`}>{formatStatusLabel(item.status)}</span>
                </div>
                <p className="media-history-caption">{item.caption || 'No caption yet.'}</p>
                <dl className="detail-grid compact-grid">
                  <div>
                    <dt>Type</dt>
                    <dd>{item.media_type}</dd>
                  </div>
                  <div>
                    <dt>Size</dt>
                    <dd>{formatFileSize(item.file_size)}</dd>
                  </div>
                  <div>
                    <dt>Updated</dt>
                    <dd>{formatDateTime(item.updated_at)}</dd>
                  </div>
                  <div>
                    <dt>Scenes</dt>
                    <dd>{item.scene_count}</dd>
                  </div>
                </dl>
              </div>
            </button>
          )
        })}
      </div>
    </section>
  )
}
