import { startTransition, useDeferredValue, useState, type FormEvent } from 'react'
import { searchMedia } from '../api/client'
import { SearchResultCard } from '../components/SearchResultCard'
import type { SearchResult } from '../types/api'
import { getErrorMessage } from '../utils/format'

interface SearchPageProps {
  onOpenMedia: (mediaId: number, startTime: number | null) => void
}

export function SearchPage({ onOpenMedia }: SearchPageProps) {
  const [query, setQuery] = useState('')
  const [searchedQuery, setSearchedQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const deferredResults = useDeferredValue(results)

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
        setSearchedQuery(response.query_text)
        setResults(response.results)
      })
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-stack">
      <section className="hero-card search-hero">
        <div>
          <p className="eyebrow">Search</p>
          <h1>Query the indexed library with plain language.</h1>
          <p className="hero-copy">
            Search results mix caption keywords and CLIP embeddings, then route directly to the image or
            video scene that matched.
          </p>
        </div>
      </section>

      <section className="panel">
        <form className="search-bar" onSubmit={handleSearch}>
          <input
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Try: white striped rug, red scene, outdoor portrait, dashboard screenshot"
            type="text"
            value={query}
          />
          <button className="button button-primary" disabled={loading || !query.trim()} type="submit">
            {loading ? 'Searching…' : 'Search'}
          </button>
        </form>

        {error ? <div className="error-banner">{error}</div> : null}

        {!searchedQuery && !loading ? (
          <div className="empty-state">Run a text query to inspect semantic matches across indexed media.</div>
        ) : null}

        {searchedQuery && !loading && deferredResults.length === 0 && !error ? (
          <div className="empty-state">No semantic matches found for “{searchedQuery}”.</div>
        ) : null}

        {deferredResults.length > 0 ? (
          <div className="results-grid">
            {deferredResults.map((item) => (
              <SearchResultCard
                item={item}
                key={`${item.result_type}-${item.media_id}-${item.start_time ?? 'image'}`}
                onOpenMedia={onOpenMedia}
              />
            ))}
          </div>
        ) : null}
      </section>
    </div>
  )
}
