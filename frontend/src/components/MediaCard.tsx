import { Film } from 'lucide-react'
import { Card, CardContent, Badge } from '@/components/ui'
import { cn } from '@/lib/utils'
import type { MediaSummary } from '../types/api'
import { formatFileSize, formatRelativeTime, toAbsoluteUrl } from '../utils/format'

interface MediaCardProps {
  media: MediaSummary
  onClick?: (mediaId: number) => void
  className?: string
}

const getStatusColor = (status: MediaSummary['status']) => {
  switch (status) {
    case 'completed':
      return 'bg-green-100 text-green-700'
    case 'processing':
      return 'bg-orange-100 text-orange-700'
    case 'failed':
      return 'bg-red-100 text-red-700'
    case 'pending':
      return 'bg-gray-100 text-gray-700'
    default:
      return 'bg-gray-100 text-gray-700'
  }
}

export function MediaCard({ media, onClick, className }: MediaCardProps) {
  const isVideo = media.media_type === 'video'
  const mediaUrl = toAbsoluteUrl(media.file)
  const hasValidThumbnail = mediaUrl && !mediaUrl.includes('placeholder')
  
  const handleClick = () => {
    if (onClick) {
      onClick(media.id)
    }
  }

  return (
    <Card 
      className={cn(
        "group cursor-pointer transition-all duration-150",
        "hover:shadow-md hover:scale-[1.02]",
        onClick && "focus:outline-none focus:ring-2 focus:ring-ring",
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
    >
      <CardContent className="p-0">
        {/* Thumbnail with 16:10 aspect ratio */}
        <div className="relative aspect-[16/10] overflow-hidden rounded-t-lg bg-muted">
          {hasValidThumbnail ? (
            <img
              src={mediaUrl}
              alt={media.original_filename}
              className="w-full h-full object-cover"
              loading="lazy"
              onError={(e) => {
                // Hide broken image on error
                e.currentTarget.style.display = 'none'
              }}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-muted">
              {isVideo ? (
                <div className="flex flex-col items-center gap-2 text-muted-foreground">
                  <Film size={32} />
                  {media.scene_count > 0 && (
                    <Badge variant="secondary" className="text-xs">
                      {media.scene_count} scenes
                    </Badge>
                  )}
                </div>
              ) : (
                <div className="text-muted-foreground text-sm">
                  No preview
                </div>
              )}
            </div>
          )}
        </div>
        
        {/* Content */}
        <div className="p-4 space-y-3">
          {/* Header with filename and status */}
          <div className="space-y-2">
            <div className="flex items-start justify-between gap-2">
              <h3 className="font-medium text-foreground text-sm leading-tight line-clamp-1">
                {media.original_filename}
              </h3>
              <Badge className={cn("text-xs flex-shrink-0", getStatusColor(media.status))}>
                {media.status}
              </Badge>
            </div>
            
            {/* Metadata */}
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span className="capitalize">{media.media_type}</span>
              <span>·</span>
              <span>{formatFileSize(media.file_size)}</span>
              <span>·</span>
              <span>{formatRelativeTime(media.uploaded_at)}</span>
            </div>
          </div>
          
          {/* Caption excerpt */}
          {media.caption && (
            <p className="text-sm text-muted-foreground line-clamp-2 leading-relaxed">
              {media.caption}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}