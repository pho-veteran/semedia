import { Badge } from '@/components/ui'
import { shouldShowBoostBadge } from '@/lib/presentation'
import { cn } from '@/lib/utils'
import type { SearchResult } from '../types/api'
import { formatScore, formatTimeRange, toAbsoluteUrl } from '../utils/format'

interface SearchResultCardProps {
  item: SearchResult
  onOpenMedia: (mediaId: number, startTime: number | null) => void
  className?: string
  isFocused?: boolean
}

function formatBoost(value: number): string {
  return `+${Math.round(value * 100)}%`
}

function getExplanationSummary(item: SearchResult): string {
  const matchTypeLabel = {
    visual: 'Visual match',
    caption: 'Caption match',
    hybrid: 'Hybrid match',
  }[item.explanation.match_type]

  const reasons: string[] = []
  if (item.explanation.exact_phrase_match) {
    reasons.push('exact phrase in caption')
  }
  if (item.explanation.rich_caption) {
    reasons.push('rich caption')
  }

  return reasons.length > 0 ? `${matchTypeLabel} · ${reasons.join(' · ')}` : matchTypeLabel
}

function getIdentityBadges(item: SearchResult): string[] {
  const badges = [item.result_type === 'video_scene' ? 'Scene' : 'Image']

  const sceneLabel = item.scene_index !== null && item.scene_index !== undefined
    ? `Scene ${item.scene_index + 1}`
    : item.scene_id !== null
      ? `Scene ${item.scene_id}`
      : 'Scene'

  if (item.result_type === 'video_scene') {
    badges.push(sceneLabel)
  }

  return badges
}

function getContextBadges(item: SearchResult): string[] {
  const badges: string[] = []

  if (item.explanation.exact_phrase_match) {
    badges.push('Exact phrase')
  }
  if (item.explanation.rich_caption) {
    badges.push('Rich caption')
  }

  return badges
}

export function SearchResultCard({ item, onOpenMedia, className, isFocused = false }: SearchResultCardProps) {
  const thumbnailUrl = toAbsoluteUrl(item.thumbnail_url || item.file_url)
  const hasVideoScene = item.result_type === 'video_scene'

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
          <Badge className="bg-foreground/70 text-background text-xs px-2 py-0.5 rounded-full border-0">
            {formatScore(item.score)}
          </Badge>
        </div>
        
        {/* Time range chip - top right (for video scenes) */}
        {hasVideoScene && item.start_time !== null && item.end_time !== null && (
          <div className="absolute top-2 right-2">
            <Badge className="bg-foreground/70 text-background text-xs px-2 py-0.5 rounded-full border-0">
              {formatTimeRange(item.start_time, item.end_time)}
            </Badge>
          </div>
        )}
      </div>
      
      {/* Content */}
      <div className="space-y-3">
        <div className="space-y-2">
          <h3 className="font-medium text-foreground text-sm leading-tight line-clamp-1">
            {item.original_filename}
          </h3>

          <div className="flex flex-wrap gap-2">
            {getIdentityBadges(item).map((badge) => (
              <Badge key={badge} variant={badge === 'Scene' ? 'secondary' : 'outline'} className="text-xs">
                {badge}
              </Badge>
            ))}
            {getContextBadges(item).map((badge) => (
              <Badge key={badge} variant="outline" className="text-xs bg-accent text-accent-foreground">
                {badge}
              </Badge>
            ))}
          </div>

          <div className="flex flex-wrap gap-2">
            <Badge variant="outline" className="text-xs">
              Semantic {formatScore(item.vector_score)}
            </Badge>
            <Badge variant="outline" className="text-xs">
              Caption {formatScore(item.keyword_score)}
            </Badge>
            {shouldShowBoostBadge(item.explanation.rerank_boost) && (
              <Badge variant="outline" className="text-xs bg-success/10 border-success/20 text-foreground">
                Boost {formatBoost(item.explanation.rerank_boost)}
              </Badge>
            )}
          </div>
        </div>

        <div className="space-y-1">
          <p className="text-sm font-medium text-foreground/90 line-clamp-2">
            {getExplanationSummary(item)}
          </p>
          {item.caption && (
            <p className="text-sm text-muted-foreground line-clamp-2 leading-relaxed">
              {item.caption}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
