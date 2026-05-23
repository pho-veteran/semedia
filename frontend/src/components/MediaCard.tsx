import { Film, Play, ImageIcon } from 'lucide-react'
import { Badge } from '@/components/ui'
import { cn } from '@/lib/utils'
import type { MediaSummary } from '../types/api'
import { formatFileSize, formatRelativeTime, toAbsoluteUrl } from '../utils/format'

interface MediaCardProps {
  media: MediaSummary
  onClick?: (mediaId: number) => void
  className?: string
}

const statusConfig: Record<MediaSummary['status'], { variant: 'completed' | 'processing' | 'failed' | 'uploading'; label: string }> = {
  completed:  { variant: 'completed',  label: 'complete' },
  processing: { variant: 'processing', label: 'Processing' },
  failed:     { variant: 'failed',     label: 'Failed' },
  pending:    { variant: 'uploading',  label: 'Pending' },
}

export function MediaCard({ media, onClick, className }: MediaCardProps) {
  const isVideo = media.media_type === 'video'

  const thumbnailUrl = toAbsoluteUrl(media.thumbnail ?? (isVideo ? null : media.file))
  const hasValidThumbnail = thumbnailUrl && !thumbnailUrl.includes('placeholder')

  const status = statusConfig[media.status] ?? statusConfig.pending
  const handleClick = () => onClick?.(media.id)

  return (
    <article
      className={cn(
        "group relative overflow-hidden rounded-2xl",
        "bg-card border border-border/60",
        "shadow-sm",
        "transition-all duration-200 ease-smooth",
        "hover:shadow-lg hover:-translate-y-0.5 hover:border-border",
        onClick && "cursor-pointer",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        className
      )}
      onClick={handleClick}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={(e) => {
        if (onClick && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault()
          handleClick()
        }
      }}
      role={onClick ? "button" : undefined}
      aria-label={onClick ? `Open ${media.original_filename}` : undefined}
    >
      <div className="relative aspect-[16/10] overflow-hidden bg-muted">
        {hasValidThumbnail ? (
          <img
            src={thumbnailUrl}
            alt={media.original_filename}
            className={cn(
              "w-full h-full object-cover",
              "transition-transform duration-500 ease-smooth",
              "group-hover:scale-[1.04]",
            )}
            loading="lazy"
            onError={(e) => { e.currentTarget.style.display = 'none' }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-muted">
            {isVideo ? (
              <Film size={28} className="text-muted-foreground/50" />
            ) : (
              <ImageIcon size={28} className="text-muted-foreground/50" />
            )}
          </div>
        )}

        {isVideo && onClick && (
          <div className={cn(
            "absolute inset-0 flex items-center justify-center",
            "bg-black/0 group-hover:bg-black/30",
            "transition-all duration-200",
          )}>
            <div className={cn(
              "flex items-center justify-center",
              "w-10 h-10 rounded-full bg-white/90 shadow-lg",
              "opacity-0 scale-75 group-hover:opacity-100 group-hover:scale-100",
              "transition-all duration-200 ease-spring",
            )}>
              <Play size={16} className="text-foreground ml-0.5" fill="currentColor" />
            </div>
          </div>
        )}

        {isVideo && media.scene_count > 0 && (
          <div className="absolute bottom-2 left-2">
            <span className="inline-flex items-center gap-1 rounded-lg bg-black/70 backdrop-blur-sm px-2 py-0.5 text-[10px] font-medium text-white">
              <Film size={9} />
              {media.scene_count} scenes
            </span>
          </div>
        )}
      </div>

      <div className="p-3.5 space-y-1.5">
        <div className="flex items-center gap-2">
          <h3 className="min-w-0 flex-1 font-medium text-[13px] leading-snug text-foreground truncate">
            {media.original_filename}
          </h3>
          <Badge variant={status.variant} className="shrink-0 text-[10px] px-2 py-0 h-5">
            {status.label}
          </Badge>
        </div>

        <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground num-tabular">
          <span className="capitalize">{media.media_type}</span>
          <span className="text-border">·</span>
          <span>{formatFileSize(media.file_size)}</span>
          <span className="text-border">·</span>
          <span>{formatRelativeTime(media.uploaded_at)}</span>
        </div>

        {media.caption && (
          <p className="text-[12px] text-muted-foreground line-clamp-2 leading-relaxed">
            {media.caption}
          </p>
        )}
      </div>
    </article>
  )
}
