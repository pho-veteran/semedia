import {
  startTransition,
  useDeferredValue,
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
  type DragEvent,
  type FormEvent,
} from 'react'
import { searchMedia, searchMediaByImage } from '../api/client'
import { SearchResultCard } from '../components/SearchResultCard'
import type { SearchResult } from '../types/api'
import { getErrorMessage } from '../utils/format'

interface SearchPageProps {
  onOpenMedia: (mediaId: number, startTime: number | null) => void
}

export function SearchPage({ onOpenMedia }: SearchPageProps) {
  const [query, setQuery] = useState('')
  const [searchedLabel, setSearchedLabel] = useState('')
  const [searchedMode, setSearchedMode] = useState<'text' | 'image' | null>(null)
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [queryImage, setQueryImage] = useState<File | null>(null)
  const [queryImagePreviewUrl, setQueryImagePreviewUrl] = useState<string | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const deferredResults = useDeferredValue(results)

  useEffect(() => {
    if (!queryImage) {
      setQueryImagePreviewUrl(null)
      return undefined
    }

    const nextPreviewUrl = URL.createObjectURL(queryImage)
    setQueryImagePreviewUrl(nextPreviewUrl)

    return () => {
      URL.revokeObjectURL(nextPreviewUrl)
    }
  }, [queryImage])

  const handleQueryImageSelected = (file: File | null) => {
    if (!file) {
      return
    }

    if (!file.type.startsWith('image/')) {
      setError('Choose an image file for media-based search.')
      return
    }

    setQueryImage(file)
    setError(null)
  }

  const handleQueryImageInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    handleQueryImageSelected(event.target.files?.[0] ?? null)
  }

  const handleImageDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setDragActive(false)
    handleQueryImageSelected(event.dataTransfer.files?.[0] ?? null)
  }

  const handleSearch = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmed = query.trim()
    if (!trimmed) {
      return
    }

    setLoading(true)
    setError(null)
    try {
      const response = await searchMedia(trimmed)
      startTransition(() => {
        setSearchedMode('text')
        setSearchedLabel(response.query_text)
        setResults(response.results)
      })
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    } finally {
      setLoading(false)
    }
  }

  const handleImageSearch = async () => {
    if (!queryImage) {
      return
    }

    setLoading(true)
    setError(null)
    try {
      const response = await searchMediaByImage(queryImage)
      startTransition(() => {
        setSearchedMode('image')
        setSearchedLabel(response.query_image_name || queryImage.name)
        setResults(response.results)
      })
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    } finally {
      setLoading(false)
    }
  }

  const clearQueryImage = () => {
    setQueryImage(null)
    setQueryImagePreviewUrl(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const emptyStateLabel =
    searchedMode === 'image' ? `the image query “${searchedLabel}”` : `“${searchedLabel}”`

  return (
    <div className="page-stack">
      <section className="hero-card search-hero">
        <div>
          <p className="eyebrow">Search</p>
          <h1>Query the indexed library with text or a reference image.</h1>
          <p className="hero-copy">
            Text search still mixes captions and CLIP embeddings. Image search uses the query image embedding
            directly to find matching images and video scenes.
          </p>
        </div>
      </section>

      <section className="panel">
        <div className="search-tools">
          <form className="search-bar" onSubmit={handleSearch}>
            <input
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Try: white striped rug, red scene, outdoor portrait, dashboard screenshot"
              type="text"
              value={query}
            />
            <button className="button button-primary" disabled={loading || !query.trim()} type="submit">
              {loading ? 'Searching…' : 'Search text'}
            </button>
          </form>

          <div
            className={`query-image-panel ${dragActive ? 'active' : ''}`}
            onDragEnter={(event) => {
              event.preventDefault()
              setDragActive(true)
            }}
            onDragLeave={(event) => {
              event.preventDefault()
              setDragActive(false)
            }}
            onDragOver={(event) => {
              event.preventDefault()
              setDragActive(true)
            }}
            onDrop={handleImageDrop}
          >
            <div className="query-image-header">
              <div>
                <p className="eyebrow">Image Query</p>
                <strong>Drop an image or choose one from disk.</strong>
              </div>
              <input
                accept="image/*"
                className="visually-hidden"
                onChange={handleQueryImageInputChange}
                ref={fileInputRef}
                type="file"
              />
              <button
                className="button button-secondary"
                onClick={() => fileInputRef.current?.click()}
                type="button"
              >
                Choose image
              </button>
            </div>

            {queryImagePreviewUrl ? (
              <div className="query-image-preview">
                <img alt={queryImage?.name || 'query image preview'} src={queryImagePreviewUrl} />
              </div>
            ) : (
              <div className="query-image-empty">
                Use an indexed-looking frame, screenshot, product shot, or photo to find visually similar media.
              </div>
            )}

            <div className="query-image-actions">
              <div className="query-image-meta">
                <strong>{queryImage?.name || 'No image selected'}</strong>
                <span>{queryImage ? `${Math.round(queryImage.size / 1024)} KB` : 'PNG, JPG, WEBP, GIF, BMP'}</span>
              </div>
              <div className="query-image-buttons">
                {queryImage ? (
                  <button className="button button-secondary" onClick={clearQueryImage} type="button">
                    Clear
                  </button>
                ) : null}
                <button
                  className="button button-primary"
                  disabled={loading || !queryImage}
                  onClick={handleImageSearch}
                  type="button"
                >
                  {loading ? 'Searching…' : 'Search image'}
                </button>
              </div>
            </div>
          </div>
        </div>

        {error ? <div className="error-banner">{error}</div> : null}

        {!searchedLabel && !loading ? (
          <div className="empty-state">
            Run a text query or submit a reference image to inspect semantic matches across indexed media.
          </div>
        ) : null}

        {searchedLabel && !loading && deferredResults.length === 0 && !error ? (
          <div className="empty-state">No semantic matches found for {emptyStateLabel}.</div>
        ) : null}

        {deferredResults.length > 0 ? (
          <>
            <div className="results-heading">
              <p className="eyebrow">{searchedMode === 'image' ? 'Image Results' : 'Text Results'}</p>
              <strong>
                {deferredResults.length} match{deferredResults.length === 1 ? '' : 'es'} for {emptyStateLabel}
              </strong>
            </div>
            <div className="results-grid">
              {deferredResults.map((item) => (
                <SearchResultCard
                  item={item}
                  key={`${item.result_type}-${item.media_id}-${item.start_time ?? 'image'}`}
                  onOpenMedia={onOpenMedia}
                />
              ))}
            </div>
          </>
        ) : null}
      </section>
    </div>
  )
}
