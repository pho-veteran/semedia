import { useState } from 'react'
import { CloudUpload } from 'lucide-react'
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
        toast.warning(`File exceeds 100MB - upload may be slow: ${file.name}`)
      }
      
      validFiles.push(file)
    }
    
    return validFiles
  }

  const handleFiles = (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) {
      return
    }
    
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
        "relative min-h-[200px] rounded-lg border-2 border-dashed border-border bg-background",
        "flex flex-col items-center justify-center p-8 text-center cursor-pointer",
        "transition-colors duration-150",
        isDragging && "border-primary bg-primary/5",
        className
      )}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
      {...props}
    >
      <CloudUpload 
        size={48} 
        className={cn(
          "text-muted-foreground mb-4",
          isDragging && "text-primary"
        )} 
      />
      
      <div className="space-y-2">
        <p className="text-lg font-medium text-foreground">
          Drop files here or click to browse
        </p>
        <p className="text-sm text-muted-foreground">
          PNG, JPG, WEBP, GIF, BMP · MP4, WebM, MOV
        </p>
      </div>
      
      <Button 
        variant="outline" 
        className="mt-4"
        onClick={(e) => {
          e.stopPropagation()
          handleClick()
        }}
      >
        Browse Files
      </Button>
    </div>
  )
}
