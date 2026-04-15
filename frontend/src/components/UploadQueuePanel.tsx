import type { UploadQueueItem } from '../types/api'
import { formatDateTime, formatStatusLabel } from '../utils/format'

interface UploadQueuePanelProps {
  items: UploadQueueItem[]
  onOpenMedia: (mediaId: number) => void
}

export function UploadQueuePanel({ items, onOpenMedia }: UploadQueuePanelProps) {
  return (
    <section className="panel">
      <header className="panel-header">
        <div>
          <p className="eyebrow">Queue</p>
          <h2>Current Upload Activity</h2>
        </div>
      </header>

      {items.length === 0 ? (
        <div className="empty-state">Nothing in the queue yet. Uploads will appear here as soon as they start.</div>
      ) : (
        <div className="queue-list">
          {items.map((item) => {
            const mediaId = item.mediaId

            return (
              <article className="queue-item" key={item.id}>
                <div className="queue-main">
                  <div>
                    <div className="queue-title-row">
                      <h3>{item.name}</h3>
                      <span className={`status-pill status-${item.status}`}>{formatStatusLabel(item.status)}</span>
                    </div>
                    <p>{item.message || 'Waiting for backend status.'}</p>
                  </div>
                  <small>{formatDateTime(item.updatedAt)}</small>
                </div>
                {mediaId !== null ? (
                  <button className="button button-secondary" onClick={() => onOpenMedia(mediaId)} type="button">
                    Open
                  </button>
                ) : null}
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}
