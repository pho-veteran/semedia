import type { SearchResult } from '../types/api'
import { formatScore, formatTimeRange, toAbsoluteUrl } from '../utils/format'

interface SearchResultCardProps {
  item: SearchResult
  onOpenMedia: (mediaId: number, startTime: number | null) => void
}

export function SearchResultCard({ item, onOpenMedia }: SearchResultCardProps) {
  const thumbnailUrl = toAbsoluteUrl(item.thumbnail_url || item.file_url)
  const hasVideoScene = item.result_type === 'video_scene'

  return (
    <button
      className="result-card"
      onClick={() => onOpenMedia(item.media_id, hasVideoScene ? item.start_time : null)}
      type="button"
    >
      <div className="result-thumb">
        {thumbnailUrl ? (
          <img alt={item.original_filename} src={thumbnailUrl} />
        ) : (
          <div className="video-placeholder">
            <span>{item.media_type}</span>
          </div>
        )}
        <span className="score-chip">{formatScore(item.score)}</span>
        {hasVideoScene ? <span className="time-chip">{formatTimeRange(item.start_time, item.end_time)}</span> : null}
      </div>
      <div className="result-copy">
        <div className="result-header">
          <h3>{item.original_filename}</h3>
          <span className="tag">{item.result_type === 'video_scene' ? 'scene' : 'image'}</span>
        </div>
        <p>{item.caption || 'No caption available.'}</p>
      </div>
    </button>
  )
}
