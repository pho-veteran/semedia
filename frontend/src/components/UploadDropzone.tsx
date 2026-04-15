import { useState } from 'react'

interface UploadDropzoneProps {
  onFilesSelected: (files: File[]) => void
}

export function UploadDropzone({ onFilesSelected }: UploadDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false)

  const handleFiles = (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) {
      return
    }
    onFilesSelected(Array.from(fileList))
  }

  return (
    <section className="panel">
      <header className="panel-header">
        <div>
          <p className="eyebrow">Ingestion</p>
          <h2>Upload Images and Videos</h2>
        </div>
      </header>

      <label
        className={`dropzone ${isDragging ? 'active' : ''}`}
        onDragLeave={() => setIsDragging(false)}
        onDragOver={(event) => {
          event.preventDefault()
          setIsDragging(true)
        }}
        onDrop={(event) => {
          event.preventDefault()
          setIsDragging(false)
          handleFiles(event.dataTransfer.files)
        }}
      >
        <input
          accept="image/*,video/*"
          className="visually-hidden"
          multiple
          onChange={(event) => {
            handleFiles(event.target.files)
            event.target.value = ''
          }}
          type="file"
        />
        <div className="dropzone-copy">
          <span className="dropzone-icon">⇪</span>
          <strong>Drop media files here or browse from disk.</strong>
          <p>
            The current backend processes synchronously, so large videos can block until indexing finishes.
          </p>
        </div>
      </label>
    </section>
  )
}
