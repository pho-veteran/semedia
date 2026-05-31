import { useState } from 'react'
import { CloudUpload, ImageIcon, Film } from 'lucide-react'
import { Button } from '@/components/ui'
import { cn } from '@/lib/utils'
import { toast } from 'sonner'

interface UploadDropzoneProps {
  onFilesSelected: (files: File[]) => void
  className?: string
  'data-upload-dropzone'?: boolean
}

const SUPPORTED_IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/webp', 'image/gif', 'image/bmp']
const SUPPORTED_VIDEO_TYPES = ['video/mp4', 'video/webm', 'video/quicktime']
const SUPPORTED_TYPES = [...SUPPORTED_IMAGE_TYPES, ...SUPPORTED_VIDEO_TYPES]
const MAX_FILE_SIZE = 100 * 1024 * 1024 // 100MB

export function UploadDropzone({ onFilesSelected, className, ...props }: UploadDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false)

  const validateFiles = (files: File[]): File[] => {
    const validFiles: File[] = []
    for (const file of files) {
      if (!SUPPORTED_TYPES.includes(file.type)) {
        toast.error(`File type not supported: ${file.name}`)
        continue
      }
      if (file.size > MAX_FILE_SIZE) {
        toast.warning(`File exceeds 100MB – upload may be slow: ${file.name}`)
      }
      validFiles.push(file)
    }
    return validFiles
  }

  const handleFiles = (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return
    const files = Array.from(fileList)
    const validFiles = validateFiles(files)
    if (validFiles.length > 0) {
      onFilesSelected(validFiles)
    }
  }

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (event: React.DragEvent) => {
    event.preventDefault()
    if (!event.currentTarget.contains(event.relatedTarget as Node)) {
      setIsDragging(false)
    }
  }

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault()
    setIsDragging(false)
    handleFiles(event.dataTransfer.files)
  }

  const handleClick = () => {
    const input = document.createElement('input')
    input.type = 'file'
    input.multiple = true
    input.accept = 'image/*,video/*'
    input.onchange = (e) => {
      const target = e.target as HTMLInputElement
      handleFiles(target.files)
    }
    input.click()
  }

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-2xl",
        "flex flex-col items-center justify-center gap-5",
        "min-h-[200px] p-8 text-center",
        "cursor-pointer select-none",
        "border-2 border-dashed",
        "transition-all duration-200 ease-smooth",
        isDragging
          ? [
              "border-brand bg-brand/5",
              "shadow-glow-sm animate-pulse-glow",
              "scale-[1.01]",
            ].join(" ")
          : "border-border/60 bg-muted/30 hover:border-brand/40 hover:bg-brand/[0.02]",
        className
      )}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      aria-label="Upload files: click or drag and drop"
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          handleClick()
        }
      }}
      {...props}
    >
      <div
        aria-hidden="true"
        className={cn(
          "absolute inset-0 -z-10 transition-opacity duration-300",
          isDragging ? "opacity-100" : "opacity-0",
        )}
        style={{
          background: "radial-gradient(ellipse at center, hsl(var(--brand) / 0.08) 0%, transparent 70%)",
        }}
      />

      <div className={cn(
        "flex items-center justify-center w-14 h-14 rounded-2xl",
        "transition-all duration-200 ease-spring",
        isDragging
          ? "bg-brand/15 text-brand scale-110"
          : "bg-muted text-muted-foreground",
      )}>
        <CloudUpload size={28} strokeWidth={1.5} />
      </div>

      <div className="space-y-1.5 max-w-xs">
        <p className={cn(
          "text-base font-semibold transition-colors duration-150",
          isDragging ? "text-brand" : "text-foreground",
        )}>
          {isDragging ? "Drop to upload" : "Drop files here"}
        </p>
        <p className="text-sm text-muted-foreground leading-relaxed">
          or click to browse your device
        </p>

        <div className="flex flex-wrap justify-center gap-1.5 pt-1">
          <span className="inline-flex items-center gap-1 rounded-lg bg-muted px-2 py-0.5 text-[11px] text-muted-foreground">
            <ImageIcon size={10} />
            PNG, JPG, WEBP, GIF
          </span>
          <span className="inline-flex items-center gap-1 rounded-lg bg-muted px-2 py-0.5 text-[11px] text-muted-foreground">
            <Film size={10} />
            MP4, WebM, MOV
          </span>
        </div>
      </div>

      <Button
        variant="outline"
        size="sm"
        className="mt-1 pointer-events-none"
        tabIndex={-1}
        aria-hidden="true"
      >
        Browse Files
      </Button>
    </div>
  )
}
