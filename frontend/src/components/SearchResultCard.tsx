import { Badge } from '@/components/ui'
import { cn } from '@/lib/utils'
import type { SearchResult } from '../types/api'
import { formatScore, formatTimeRange, toAbsoluteUrl } from '../utils/format'

interface SearchResultCardProps {
  item: SearchResult
  onOpenMedia: (mediaId: number, startTime: number | null) => void
  className?: string
  isFocused?: boolean
}

export function SearchResultCard({ item, onOpenMedia, className, isFocused = false }: SearchResultCardProps) {
  const thumbnailUrl = toAbsoluteUrl(item.thumbnail_url || item.file_url)
  const hasVideoScene = item.result_type === 'video_scene'
  const isScene = item.result_type === 'video_scene'

  const handleClick = () => {
    onOpenMedia(item.media_id, hasVideoScene ? item.start_time : null)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      handleClick()
    }
  }

  return (
    <div
      className={cn(
        "group cursor-pointer transition-all duration-150",
        "hover:scale-[1.02] hover:shadow-md",
        "focus:outline-none focus:ring-2 focus:ring-ring rounded-lg",
        isFocused && "ring-2 ring-primary scale-[1.02] shadow-md",
        className
      )}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="button"
      aria-label={`Open ${item.original_filename}`}
    >
      {/* Thumbnail with 16:10 aspect ratio */}
      <div className="relative aspect-[16/10] overflow-hidden rounded-lg bg-muted mb-3">
        {thumbnailUrl ? (
          <img 
            src={thumbnailUrl} 
            alt={item.original_filename}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-muted">
            <span className="text-sm text-muted-foreground capitalize">
              {item.media_type}
            </span>
          </div>
        )}
        
        {/* Relevance score chip - top left */}
        <div className="absolute top-2 left-2">
          <Badge className="bg-black/60 text-white text-xs px-2 py-0.5 rounded-full border-0">
            {formatScore(item.score)}
          </Badge>
        </div>
        
        {/* Time range chip - top right (for video scenes) */}
        {hasVideoScene && item.start_time !== null && item.end_time !== null && (
          <div className="absolute top-2 right-2">
            <Badge className="bg-black/60 text-white text-xs px-2 py-0.5 rounded-full border-0">
              {formatTimeRange(item.start_time, item.end_time)}
            </Badge>
          </div>
        )}
      </div>
      
      {/* Content */}
      <div className="space-y-2">
        {/* Filename and scene badge */}
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-medium text-foreground text-sm leading-tight line-clamp-1">
            {item.original_filename}
          </h3>
          {isScene && (
            <Badge variant="secondary" className="text-xs flex-shrink-0">
              Scene
            </Badge>
          )}
        </div>
        
        {/* Caption excerpt */}
        {item.caption && (
          <p className="text-sm text-muted-foreground line-clamp-2 leading-relaxed">
            {item.caption}
          </p>
        )}
      </div>
    </div>
  )
}
