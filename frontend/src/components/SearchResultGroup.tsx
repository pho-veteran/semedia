import { useState } from 'react'
import { Badge, Button } from '@/components/ui'
import { cn } from '@/lib/utils'
import type { SearchResult } from '../types/api'
import { formatScore, formatTimeRange, toAbsoluteUrl } from '../utils/format'
import { SearchResultCard } from './SearchResultCard'

interface SearchResultGroupProps {
  mediaId: number
  lead: SearchResult
  previews: SearchResult[]
  hidden: SearchResult[]
  onOpenMedia: (mediaId: number, startTime: number | null) => void
  className?: string
  isFocused?: boolean
}

function sceneRenderKey(scene: SearchResult): string {
  if (scene.scene_key) {
    return scene.scene_key
  }
  if (scene.scene_id !== null) {
    return `scene:${scene.scene_id}`
  }
  return `media:${scene.media_id}:start:${scene.start_time ?? 'unknown'}`
}

function CompactScenePreview({
  scene,
  mediaId,
  onOpenMedia,
}: {
  scene: SearchResult
  mediaId: number
  onOpenMedia: (mediaId: number, startTime: number | null) => void
}) {
  const thumbnailUrl = toAbsoluteUrl(scene.thumbnail_url || scene.file_url)
  const sceneLabel = scene.scene_index !== null && scene.scene_index !== undefined
    ? `Scene ${scene.scene_index + 1}`
    : scene.scene_id !== null
      ? `Scene ${scene.scene_id}`
      : 'Scene'

  const handleClick = () => {
    if (scene.start_time === null) {
      console.warn(`CompactScenePreview: ${sceneLabel} has null start_time`)
    }
    onOpenMedia(mediaId, scene.start_time)
  }

  const ariaLabel = scene.start_time !== null && scene.end_time !== null
    ? `Open ${sceneLabel} at ${formatTimeRange(scene.start_time, scene.end_time)}`
    : `Open ${sceneLabel}`

  return (
    <button
      onClick={handleClick}
      className={cn(
        'group flex flex-col gap-2 cursor-pointer transition-all duration-150',
        'hover:scale-[1.05] hover:shadow-md',
        'focus:outline-none focus:ring-2 focus:ring-ring rounded-lg',
        'p-2 bg-muted'
      )}
      aria-label={ariaLabel}
    >
      {/* Thumbnail with 16:10 aspect ratio */}
      <div className="relative aspect-[16/10] overflow-hidden rounded-md bg-muted">
        {thumbnailUrl ? (
          <img
            src={thumbnailUrl}
            alt={sceneLabel}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-muted">
            <span className="text-xs text-muted-foreground">Scene</span>
          </div>
        )}

        {/* Score badge - top left */}
        <div className="absolute top-1 left-1">
          <Badge className="bg-foreground/70 text-background text-xs px-1.5 py-0.5 rounded-full border-0">
            {formatScore(scene.score)}
          </Badge>
        </div>

        {/* Time range badge - top right */}
        {scene.start_time !== null && scene.end_time !== null && (
          <div className="absolute top-1 right-1">
            <Badge className="bg-foreground/70 text-background text-xs px-1.5 py-0.5 rounded-full border-0">
              {formatTimeRange(scene.start_time, scene.end_time)}
            </Badge>
          </div>
        )}
      </div>

      {/* Caption */}
      {scene.caption && (
        <p className="text-xs text-muted-foreground line-clamp-2 leading-tight">
          {scene.caption}
        </p>
      )}
    </button>
  )
}

export function SearchResultGroup({
  mediaId,
  lead,
  previews,
  hidden,
  onOpenMedia,
  className,
  isFocused = false,
}: SearchResultGroupProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const hasPreviewsOrHidden = previews.length > 0 || hidden.length > 0

  return (
    <div className={cn('space-y-4', className)}>
      {/* Lead scene */}
      <SearchResultCard
        item={lead}
        onOpenMedia={onOpenMedia}
        isFocused={isFocused}
      />

      {/* Preview strip and expansion control */}
      {hasPreviewsOrHidden && (
        <div className="space-y-3">
          {/* Preview scenes */}
          {previews.length > 0 && (
            <div className="grid grid-cols-2 gap-2">
              {previews.map((scene) => (
                <CompactScenePreview
                  key={sceneRenderKey(scene)}
                  scene={scene}
                  mediaId={mediaId}
                  onOpenMedia={onOpenMedia}
                />
              ))}
            </div>
          )}

          {/* Expansion button */}
          {hidden.length > 0 && (
            <div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full"
              >
                {isExpanded
                  ? 'Hide extra scenes'
                  : `Show ${hidden.length} more scene${hidden.length === 1 ? '' : 's'}`}
              </Button>

              {/* Hidden scenes */}
              {isExpanded && (
                <div className="mt-3 grid grid-cols-2 gap-2">
                  {hidden.map((scene) => (
                    <CompactScenePreview
                      key={sceneRenderKey(scene)}
                      scene={scene}
                      mediaId={mediaId}
                      onOpenMedia={onOpenMedia}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
