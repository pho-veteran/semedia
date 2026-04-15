import { useEffect, useRef, useState } from 'react'
import { getMediaDetail } from '../api/client'
import type { MediaDetail } from '../types/api'
import {
  formatDateTime,
  formatFileSize,
  formatStatusLabel,
  formatTimeRange,
  toAbsoluteUrl,
} from '../utils/format'

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
  const [seekTarget, setSeekTarget] = useState<number | null>(initialStartTime)
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
      await onDeleted(mediaId)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Delete failed.')
    } finally {
      setDeleting(false)
    }
  }

  if (loading) {
    return <div className="panel empty-state">Loading media detail…</div>
  }

  if (error) {
    return (
      <div className="page-stack">
        <button className="button button-secondary" onClick={onBack} type="button">
          Back
        </button>
        <div className="error-banner">{error}</div>
      </div>
    )
  }

  if (!detail) {
    return (
      <div className="page-stack">
        <button className="button button-secondary" onClick={onBack} type="button">
          Back
        </button>
        <div className="empty-state">The requested media item does not exist.</div>
      </div>
    )
  }

  return (
    <div className="page-stack">
      <div className="page-toolbar">
        <button className="button button-secondary" onClick={onBack} type="button">
          Back
        </button>
        <div className="toolbar-actions">
          <a
            className="button button-secondary"
            href={toAbsoluteUrl(detail.file)}
            rel="noreferrer"
            target="_blank"
          >
            Open asset
          </a>
          <button className="button button-danger" disabled={deleting} onClick={handleDelete} type="button">
            {deleting ? 'Deleting…' : 'Delete'}
          </button>
        </div>
      </div>

      <section className="detail-layout">
        <div className="panel detail-preview-panel">
          <header className="panel-header">
            <div>
              <p className="eyebrow">Detail</p>
              <h1>{detail.original_filename}</h1>
            </div>
            <span className={`status-pill status-${detail.status}`}>{formatStatusLabel(detail.status)}</span>
          </header>

          {detail.media_type === 'image' ? (
            <img
              alt={detail.original_filename}
              className="detail-preview"
              src={toAbsoluteUrl(detail.file)}
            />
          ) : (
            <video
              className="detail-video"
              controls
              preload="metadata"
              ref={videoRef}
              src={toAbsoluteUrl(detail.file)}
            />
          )}

          <p className="detail-caption">{detail.caption || detail.error_message || 'No caption available.'}</p>

          <dl className="detail-grid">
            <div>
              <dt>Type</dt>
              <dd>{detail.media_type}</dd>
            </div>
            <div>
              <dt>Size</dt>
              <dd>{formatFileSize(detail.file_size)}</dd>
            </div>
            <div>
              <dt>Uploaded</dt>
              <dd>{formatDateTime(detail.uploaded_at)}</dd>
            </div>
            <div>
              <dt>Processed</dt>
              <dd>{detail.processed_at ? formatDateTime(detail.processed_at) : 'Not finished'}</dd>
            </div>
            <div>
              <dt>Duration</dt>
              <dd>{detail.duration !== null ? `${detail.duration.toFixed(2)}s` : 'N/A'}</dd>
            </div>
            <div>
              <dt>Index key</dt>
              <dd>{detail.index_key || 'Pending'}</dd>
            </div>
          </dl>
        </div>

        <aside className="panel detail-scenes-panel">
          <header className="panel-header">
            <div>
              <p className="eyebrow">Scenes</p>
              <h2>Video breakdown</h2>
            </div>
          </header>

          {detail.media_type !== 'video' ? (
            <div className="empty-state">Images do not have scene segments.</div>
          ) : detail.scenes.length === 0 ? (
            <div className="empty-state">No scenes were generated for this video.</div>
          ) : (
            <div className="scene-list">
              {detail.scenes.map((scene) => (
                <button
                  className="scene-item"
                  key={scene.id}
                  onClick={() => {
                    setSeekTarget(scene.start_time)
                    onNavigateToMedia(detail.id, scene.start_time)
                  }}
                  type="button"
                >
                  <img
                    alt={`Scene ${scene.scene_index}`}
                    className="scene-thumb"
                    src={toAbsoluteUrl(scene.thumbnail_image || scene.keyframe_image)}
                  />
                  <div className="scene-copy">
                    <div className="scene-row">
                      <strong>Scene {scene.scene_index + 1}</strong>
                      <span className="tag">{formatTimeRange(scene.start_time, scene.end_time)}</span>
                    </div>
                    <p>{scene.caption || 'No scene caption available.'}</p>
                  </div>
                </button>
              ))}
            </div>
          )}
        </aside>
      </section>
    </div>
  )
}
