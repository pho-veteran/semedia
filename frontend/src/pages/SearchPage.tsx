import {
  startTransition,
  useDeferredValue,
  useEffect,
  useRef,
  useState,
  useCallback,
  type ChangeEvent,
  type DragEvent,
  type KeyboardEvent,
} from 'react'
import { Search, CloudUpload, X } from 'lucide-react'
import { searchMedia, searchMediaByImage } from '../api/client'
import { SearchResultCard } from '../components/SearchResultCard'
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle,
  Button,
  Input,
  Badge,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
  Select,
  SimpleSelectItem,
  EmptyState,
  ErrorState,
  SkeletonSearchResult
} from '../components/ui'
import type { SearchResult } from '../types/api'
import { getErrorMessage } from '../utils/format'
import { cn } from '../lib/utils'

interface SearchPageProps {
  onOpenMedia: (mediaId: number, startTime: number | null) => void
  searchInputRef?: React.RefObject<HTMLInputElement>
}

export function SearchPage({ onOpenMedia, searchInputRef }: SearchPageProps) {
  // Search state
  const [activeTab, setActiveTab] = useState<'text' | 'image'>('text')
  const [query, setQuery] = useState('')
  const [searchedLabel, setSearchedLabel] = useState('')
  const [searchedMode, setSearchedMode] = useState<'text' | 'image' | null>(null)
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [focusedResultIndex, setFocusedResultIndex] = useState(-1)
  const deferredResults = useDeferredValue(results)
  const [queryImage, setQueryImage] = useState<File | null>(null)
  const [queryImagePreviewUrl, setQueryImagePreviewUrl] = useState<string | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const [typeFilter, setTypeFilter] = useState('all')
  const [scoreFilter, setScoreFilter] = useState('0.5')
  const [sortBy, setSortBy] = useState('relevance')
  const debounceTimerRef = useRef<number | null>(null)

  // Recent searches from localStorage
  const [recentSearches, setRecentSearches] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem('recentSearches')
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  })

  const addRecentSearch = useCallback((searchTerm: string) => {
    if (!searchTerm.trim()) return
    
    setRecentSearches(prev => {
      const filtered = prev.filter(term => term !== searchTerm)
      const updated = [searchTerm, ...filtered].slice(0, 5) 
      
      try {
        localStorage.setItem('recentSearches', JSON.stringify(updated))
      } catch {
      }
      
      return updated
    })
  }, [])

  const filteredAndSortedResults = deferredResults
    .filter(result => {
      if (typeFilter === 'all') return true
      if (typeFilter === 'images') return result.media_type === 'image'
      if (typeFilter === 'videos') return result.media_type === 'video'
      return true
    })
    .filter(result => {
      const threshold = parseFloat(scoreFilter)
      return result.score >= threshold
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'relevance':
          return b.score - a.score
        case 'date':
          return b.original_filename.localeCompare(a.original_filename)
        case 'size':
          return a.original_filename.localeCompare(b.original_filename)
        default:
          return b.score - a.score
      }
    })

  useEffect(() => {
    const handleKeyDown = (event: globalThis.KeyboardEvent) => {
      if (filteredAndSortedResults.length === 0) return
      
      const activeElement = document.activeElement
      const isTyping = activeElement?.tagName === 'INPUT' || 
                       activeElement?.tagName === 'TEXTAREA' ||
                       activeElement?.getAttribute('contenteditable') === 'true'
      
      if (isTyping) return

      if (event.key === 'ArrowDown') {
        event.preventDefault()
        setFocusedResultIndex((prev) => 
          prev < filteredAndSortedResults.length - 1 ? prev + 1 : prev
        )
      } else if (event.key === 'ArrowUp') {
        event.preventDefault()
        setFocusedResultIndex((prev) => (prev > 0 ? prev - 1 : -1))
      } else if (event.key === 'Enter' && focusedResultIndex >= 0) {
        event.preventDefault()
        const result = filteredAndSortedResults[focusedResultIndex]
        if (result) {
          onOpenMedia(result.media_id, result.start_time)
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [filteredAndSortedResults, focusedResultIndex, onOpenMedia])

  useEffect(() => {
    setFocusedResultIndex(-1)
  }, [results])

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

  const debouncedSearch = useCallback((searchQuery: string) => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    debounceTimerRef.current = setTimeout(() => {
      if (searchQuery.trim()) {
        handleTextSearch(searchQuery.trim())
      }
    }, 300)
  }, [])

  const handleQueryChange = (event: ChangeEvent<HTMLInputElement>) => {
    const newQuery = event.target.value
    setQuery(newQuery)
    
    if (newQuery.trim()) {
      debouncedSearch(newQuery)
    }
  }
  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      event.preventDefault()
      const trimmed = query.trim()
      if (trimmed) {
        if (debounceTimerRef.current) {
          clearTimeout(debounceTimerRef.current)
        }
        handleTextSearch(trimmed)
      }
    }
  }

  const handleTextSearch = async (searchQuery: string) => {
    setLoading(true)
    setError(null)
    try {
      const response = await searchMedia(searchQuery)
      startTransition(() => {
        setSearchedMode('text')
        setSearchedLabel(response.query_text)
        setResults(response.results)
      })
      // Save to recent searches
      addRecentSearch(searchQuery)
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    } finally {
      setLoading(false)
    }
  }

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

  const activeFilters = []
  if (typeFilter !== 'all') {
    activeFilters.push({
      key: 'type',
      label: `Type: ${typeFilter === 'images' ? 'Images' : 'Videos'}`,
      remove: () => setTypeFilter('all')
    })
  }
  if (scoreFilter !== '0.5') {
    activeFilters.push({
      key: 'score',
      label: `Score: ≥${scoreFilter}`,
      remove: () => setScoreFilter('0.5')
    })
  }
  if (sortBy !== 'relevance') {
    activeFilters.push({
      key: 'sort',
      label: `Sort: ${sortBy}`,
      remove: () => setSortBy('relevance')
    })
  }

  const emptyStateLabel =
    searchedMode === 'image' ? `the image query "${searchedLabel}"` : `"${searchedLabel}"`

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      {/* Page Header */}
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">Search Media</h1>
        <p className="text-muted-foreground">Find images and videos using text or image queries</p>
      </header>

      {/* Search Interface */}
      <section aria-label="Search interface">
        <Card className="mb-6">
        <CardHeader>
          <CardTitle>Search</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="text" value={activeTab} onValueChange={(value) => setActiveTab(value as 'text' | 'image')} className="w-full">
            <TabsList className="grid w-full grid-cols-2 mb-4">
              <TabsTrigger value="text">Text Search</TabsTrigger>
              <TabsTrigger value="image">Image Search</TabsTrigger>
            </TabsList>
            
            <TabsContent value="text" className="space-y-3">
              <div className="flex gap-2">
                <Input
                  ref={searchInputRef}
                  placeholder="Search for images and videos..."
                  value={query}
                  onChange={handleQueryChange}
                  onKeyDown={handleKeyDown}
                  className="flex-1"
                  aria-label="Search query"
                />
                <Button 
                  onClick={() => {
                    const trimmed = query.trim()
                    if (trimmed) {
                      if (debounceTimerRef.current) {
                        clearTimeout(debounceTimerRef.current)
                      }
                      handleTextSearch(trimmed)
                    }
                  }}
                  disabled={loading || !query.trim()}
                  aria-label="Search"
                >
                  <Search className="w-4 h-4 mr-2" />
                  Search
                </Button>
              </div>
              {recentSearches.length > 0 && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span>Recent:</span>
                  {recentSearches.map(term => (
                    <Button
                      key={term}
                      variant="link"
                      size="sm"
                      onClick={() => {
                        setQuery(term)
                        handleTextSearch(term)
                      }}
                      className="h-auto p-0 text-sm"
                    >
                      {term}
                    </Button>
                  ))}
                </div>
              )}
            </TabsContent>
            
            <TabsContent value="image" className="space-y-3">
              <div
                className={cn(
                  "border-2 border-dashed rounded-lg p-6 text-center transition-colors",
                  dragActive ? "border-primary bg-primary/5" : "border-border",
                  "hover:border-border/80"
                )}
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
                {queryImagePreviewUrl ? (
                  <div className="space-y-4">
                    <div className="relative inline-block">
                      <img 
                        src={queryImagePreviewUrl} 
                        alt={queryImage?.name || 'query image preview'} 
                        className="max-h-48 rounded-md"
                      />
                    </div>
                    <div className="text-sm text-muted-foreground">
                      <div className="font-medium">{queryImage?.name}</div>
                      <div>{queryImage ? `${Math.round(queryImage.size / 1024)} KB` : ''}</div>
                    </div>
                    <div className="flex gap-2 justify-center">
                      <Button variant="outline" onClick={clearQueryImage}>
                        Clear
                      </Button>
                      <Button onClick={handleImageSearch} disabled={loading}>
                        <Search className="w-4 h-4 mr-2" />
                        {loading ? 'Searching...' : 'Search Image'}
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <CloudUpload className="w-12 h-12 mx-auto text-muted-foreground" />
                    <div>
                      <p className="text-lg font-medium">Drop an image here or click to browse</p>
                      <p className="text-sm text-muted-foreground mt-1">PNG, JPG, WEBP, GIF, BMP</p>
                    </div>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handleQueryImageInputChange}
                      className="hidden"
                    />
                    <Button onClick={() => fileInputRef.current?.click()}>
                      Choose Image
                    </Button>
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
      </section>

      {/* Filters and Sort Controls */}
      <section aria-label="Filters and sorting">
        <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-center gap-3 mb-3">
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SimpleSelectItem value="all">All Types</SimpleSelectItem>
              <SimpleSelectItem value="images">Images</SimpleSelectItem>
              <SimpleSelectItem value="videos">Videos</SimpleSelectItem>
            </Select>
            
            <Select value={scoreFilter} onValueChange={setScoreFilter}>
              <SimpleSelectItem value="0.5">≥ 0.5</SimpleSelectItem>
              <SimpleSelectItem value="0.7">≥ 0.7</SimpleSelectItem>
              <SimpleSelectItem value="0.9">≥ 0.9</SimpleSelectItem>
            </Select>
            
            <Select value={sortBy} onValueChange={setSortBy}>
              <SimpleSelectItem value="relevance">Relevance</SimpleSelectItem>
              <SimpleSelectItem value="date">Date</SimpleSelectItem>
              <SimpleSelectItem value="size">Size</SimpleSelectItem>
            </Select>
          </div>
          
          {/* Active filter chips */}
          {activeFilters.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {activeFilters.map(filter => (
                <Badge key={filter.key} variant="secondary" className="gap-1">
                  {filter.label}
                  <button onClick={filter.remove} className="hover:bg-destructive/20 rounded-full">
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      </section>

      {/* Error State */}
      {error && (
        <div className="mb-6">
          <ErrorState
            variant="banner"
            title="Search failed"
            description={error}
            onRetry={() => {
              setError(null)
              if (searchedMode === 'text' && searchedLabel) {
                handleTextSearch(searchedLabel)
              } else if (searchedMode === 'image' && queryImage) {
                handleImageSearch()
              }
            }}
          />
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="animate-in fade-in-0 duration-150" style={{ animationDelay: `${i * 30}ms` }}>
              <SkeletonSearchResult />
            </div>
          ))}
        </div>
      )}

      {/* Empty State - No search performed */}
      {!searchedLabel && !loading && (
        <EmptyState
          variant="no-search"
          title="Start searching"
          description="Run a text query or submit a reference image to find semantic matches across your media library."
        />
      )}

      {/* Empty State - No results */}
      {searchedLabel && !loading && filteredAndSortedResults.length === 0 && !error && (
        <EmptyState
          variant="no-results"
          title="No results found"
          description={`No semantic matches found for ${emptyStateLabel}. Try different search terms or adjust your filters.`}
        />
      )}

      {/* Search Results */}
      {filteredAndSortedResults.length > 0 && !loading && (
        <section aria-label="Search results">
          <div className="space-y-6">
          {/* Results Summary */}
          <div aria-live="polite" aria-atomic="true">
            <p className="text-sm text-muted-foreground">
              {searchedMode === 'image' ? 'Image Results' : 'Text Results'}
            </p>
            <h2 className="text-lg font-semibold">
              {filteredAndSortedResults.length} result{filteredAndSortedResults.length === 1 ? '' : 's'} for {emptyStateLabel}
            </h2>
          </div>

          {/* Results Grid with Staggered Animation */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {filteredAndSortedResults.map((item, index) => (
              <div
                key={`${item.result_type}-${item.media_id}-${item.start_time ?? 'image'}`}
                className="animate-in fade-in-0 duration-150"
                style={{ animationDelay: `${index * 30}ms` }}
              >
                <SearchResultCard
                  item={item}
                  onOpenMedia={onOpenMedia}
                  isFocused={index === focusedResultIndex}
                />
              </div>
            ))}
          </div>
        </div>
        </section>
      )}
    </div>
  )
}