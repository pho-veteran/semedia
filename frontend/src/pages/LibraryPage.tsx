import { useState, useEffect, useMemo } from 'react'
import { LayoutGrid, List, Download, Trash2, X, ImageOff } from 'lucide-react'
import { toast } from 'sonner'
import { 
  Card, 
  CardContent, 
  Button, 
  Input, 
  Badge,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  EmptyState,
  ErrorState,
  Skeleton
} from '@/components/ui'
import { Select, SimpleSelectItem } from '@/components/ui/Select'
import { MediaCard } from '@/components/MediaCard'
import { DataTable } from '@/components/DataTable'
import { cn } from '@/lib/utils'
import { getMediaList, deleteMediaById } from '@/api/client'
import type { MediaSummary, PaginatedResponse } from '@/types/api'
import { getErrorMessage } from '@/utils/format'

interface LibraryPageProps {
  onOpenMedia: (mediaId: number) => void
  onDeleteMedia?: (mediaId: number) => void
}

type ViewMode = 'grid' | 'list'
type SortOption = 'newest' | 'oldest' | 'name' | 'size'
type TypeFilter = 'all' | 'image' | 'video'
type StatusFilter = 'all' | 'completed' | 'processing' | 'failed'
type ItemsPerPage = 24 | 48 | 96

interface FilterState {
  search: string
  type: TypeFilter
  status: StatusFilter
  sort: SortOption
}

interface PaginationState {
  currentPage: number
  itemsPerPage: ItemsPerPage
  totalPages: number
}

const INITIAL_FILTER_STATE: FilterState = {
  search: '',
  type: 'all',
  status: 'all',
  sort: 'newest'
}

const INITIAL_PAGINATION_STATE: PaginationState = {
  currentPage: 1,
  itemsPerPage: 24,
  totalPages: 1
}

export function LibraryPage({ onOpenMedia, onDeleteMedia }: LibraryPageProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [filters, setFilters] = useState<FilterState>(INITIAL_FILTER_STATE)
  const [pagination, setPagination] = useState<PaginationState>(INITIAL_PAGINATION_STATE)
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [mediaData, setMediaData] = useState<PaginatedResponse<MediaSummary> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [bulkDeleteDialogOpen, setBulkDeleteDialogOpen] = useState(false)

  const filteredAndSortedMedia = useMemo(() => {
    if (!mediaData?.results) return []

    let filtered = mediaData.results.filter(item => {
      if (filters.search && !item.original_filename.toLowerCase().includes(filters.search.toLowerCase()) &&
          !item.caption.toLowerCase().includes(filters.search.toLowerCase())) {
        return false
      }

      if (filters.type !== 'all' && item.media_type !== filters.type) {
        return false
      }

      if (filters.status !== 'all' && item.status !== filters.status) {
        return false
      }

      return true
    })


    filtered.sort((a, b) => {
      switch (filters.sort) {
        case 'newest':
          return new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime()
        case 'oldest':
          return new Date(a.uploaded_at).getTime() - new Date(b.uploaded_at).getTime()
        case 'name':
          return a.original_filename.localeCompare(b.original_filename)
        case 'size':
          return b.file_size - a.file_size
        default:
          return 0
      }
    })

    return filtered
  }, [mediaData?.results, filters])

  const paginatedMedia = useMemo(() => {
    const startIndex = (pagination.currentPage - 1) * pagination.itemsPerPage
    const endIndex = startIndex + pagination.itemsPerPage
    return filteredAndSortedMedia.slice(startIndex, endIndex)
  }, [filteredAndSortedMedia, pagination.currentPage, pagination.itemsPerPage])

  useEffect(() => {
    const totalPages = Math.ceil(filteredAndSortedMedia.length / pagination.itemsPerPage)
    setPagination(prev => ({ ...prev, totalPages }))
  }, [filteredAndSortedMedia.length, pagination.itemsPerPage])

  const loadMediaData = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await getMediaList()
      setMediaData(response)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadMediaData()
  }, [])

  const handleSearchChange = (value: string) => {
    setFilters(prev => ({ ...prev, search: value }))
    setPagination(prev => ({ ...prev, currentPage: 1 })) 
  }

  const handleTypeFilterChange = (value: string) => {
    setFilters(prev => ({ ...prev, type: value as TypeFilter }))
    setPagination(prev => ({ ...prev, currentPage: 1 }))
  }

  const handleStatusFilterChange = (value: string) => {
    setFilters(prev => ({ ...prev, status: value as StatusFilter }))
    setPagination(prev => ({ ...prev, currentPage: 1 }))
  }

  const handleSortChange = (value: string) => {
    setFilters(prev => ({ ...prev, sort: value as SortOption }))
  }

  const removeFilter = (filterKey: keyof FilterState) => {
    setFilters(prev => ({ ...prev, [filterKey]: INITIAL_FILTER_STATE[filterKey] }))
    setPagination(prev => ({ ...prev, currentPage: 1 }))
  }

  const handlePageChange = (page: number) => {
    setPagination(prev => ({ ...prev, currentPage: page }))
  }

  const handleItemsPerPageChange = (value: string) => {
    const itemsPerPage = parseInt(value) as ItemsPerPage
    setPagination(prev => ({ 
      ...prev, 
      itemsPerPage, 
      currentPage: 1 
    }))
  }

  const handleSelectionChange = (newSelectedIds: number[]) => {
    setSelectedIds(newSelectedIds)
  }

  const clearSelection = () => {
    setSelectedIds([])
  }

  const handleBulkDownload = () => {
    toast.info(`Bulk download of ${selectedIds.length} items - feature coming soon`)
  }

  const handleBulkDelete = () => {
    setBulkDeleteDialogOpen(true)
  }

  const confirmBulkDelete = async () => {
    try {
      const deletedCount = selectedIds.length
      
      await Promise.all(selectedIds.map(id => deleteMediaById(id)))
      
      if (onDeleteMedia) {
        selectedIds.forEach(id => onDeleteMedia(id))
      }

      await loadMediaData()
      clearSelection()
      setBulkDeleteDialogOpen(false)
      
      toast.success(`Deleted ${deletedCount} items`, {
        duration: 5000,
        action: {
          label: 'Undo',
          onClick: () => {
            toast.info('Undo functionality requires backend support - not yet implemented')
          },
        },
      })
    } catch (err) {
      toast.error('Failed to delete items', {
        description: getErrorMessage(err),
        duration: 10000,
      })
    }
  }

  const handleItemClick = (mediaId: number) => {
    onOpenMedia(mediaId)
  }

  const handleDownload = (_mediaId: number) => {
    toast.info('Download feature coming soon')
  }

  const handleDelete = async (mediaId: number) => {
    try {
      await deleteMediaById(mediaId)
      if (onDeleteMedia) {
        onDeleteMedia(mediaId)
      }
      await loadMediaData()
      toast.success('Media deleted', {
        duration: 5000,
        action: {
          label: 'Undo',
          onClick: () => {
            toast.info('Undo functionality requires backend support - not yet implemented')
          },
        },
      })
    } catch (err) {
      toast.error('Failed to delete media', {
        description: getErrorMessage(err),
        duration: 10000,
      })
    }
  }

  const activeFilters = useMemo(() => {
    const active = []
    if (filters.search) active.push({ key: 'search', label: `Search: "${filters.search}"` })
    if (filters.type !== 'all') active.push({ key: 'type', label: `Type: ${filters.type}` })
    if (filters.status !== 'all') active.push({ key: 'status', label: `Status: ${filters.status}` })
    return active
  }, [filters])

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-3">
                <Skeleton className="h-10 flex-1 min-w-[200px]" />
                <Skeleton className="h-10 w-[120px]" />
                <Skeleton className="h-10 w-[140px]" />
                <Skeleton className="h-10 w-[140px]" />
                <Skeleton className="h-10 w-[100px]" />
              </div>
            </div>
          </CardContent>
        </Card>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {Array.from({ length: 12 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-0">
                <Skeleton className="aspect-[16/10] w-full rounded-t-lg" />
                <div className="p-4 space-y-3">
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-1/2" />
                  </div>
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-2/3" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <ErrorState
        title="Failed to load library"
        description={error}
        onRetry={loadMediaData}
      />
    )
  }

  const totalItems = filteredAndSortedMedia.length

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold text-foreground">Media Library</h1>
        <p className="text-muted-foreground">
          {totalItems} {totalItems === 1 ? 'item' : 'items'}
        </p>
      </div>

      {/* Filter Toolbar */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4">
            {/* Top row: Search + Filters + View toggle */}
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex-1 min-w-[200px]">
                <Input
                  placeholder="Search library..."
                  value={filters.search}
                  onChange={(e) => handleSearchChange(e.target.value)}
                  className="w-full"
                />
              </div>
              
              <Select value={filters.type} onValueChange={handleTypeFilterChange}>
                <SimpleSelectItem value="all">All Types</SimpleSelectItem>
                <SimpleSelectItem value="image">Images</SimpleSelectItem>
                <SimpleSelectItem value="video">Videos</SimpleSelectItem>
              </Select>
              
              <Select value={filters.status} onValueChange={handleStatusFilterChange}>
                <SimpleSelectItem value="all">All Status</SimpleSelectItem>
                <SimpleSelectItem value="completed">Completed</SimpleSelectItem>
                <SimpleSelectItem value="processing">Processing</SimpleSelectItem>
                <SimpleSelectItem value="failed">Failed</SimpleSelectItem>
              </Select>
              
              <Select value={filters.sort} onValueChange={handleSortChange}>
                <SimpleSelectItem value="newest">Newest</SimpleSelectItem>
                <SimpleSelectItem value="oldest">Oldest</SimpleSelectItem>
                <SimpleSelectItem value="name">Name A-Z</SimpleSelectItem>
                <SimpleSelectItem value="size">Size</SimpleSelectItem>
              </Select>
              
              <div className="flex items-center gap-1 border rounded-md">
                <Button
                  variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('grid')}
                  className="h-10 px-3"
                  aria-label="Grid view"
                >
                  <LayoutGrid size={16} />
                </Button>
                <Button
                  variant={viewMode === 'list' ? 'secondary' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('list')}
                  className="h-10 px-3"
                  aria-label="List view"
                >
                  <List size={16} />
                </Button>
              </div>
            </div>
            
            {/* Bottom row: Active filter chips */}
            {activeFilters.length > 0 && (
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm text-muted-foreground">Active:</span>
                {activeFilters.map(filter => (
                  <Badge key={filter.key} variant="secondary" className="gap-1">
                    {filter.label}
                    <button onClick={() => removeFilter(filter.key as keyof FilterState)}>
                      <X size={12} />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Bulk Actions Toolbar */}
      {selectedIds.length > 0 && (
        <Card className="border-primary">
          <CardContent className="py-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">
                {selectedIds.length} item{selectedIds.length > 1 ? 's' : ''} selected
              </span>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={handleBulkDownload}>
                  <Download size={16} className="mr-1" />
                  Download
                </Button>
                <Button variant="destructive" size="sm" onClick={handleBulkDelete}>
                  <Trash2 size={16} className="mr-1" />
                  Delete
                </Button>
                <Button variant="ghost" size="sm" onClick={clearSelection}>
                  Cancel
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Content Area */}
      {totalItems === 0 ? (
        <EmptyState
          variant="custom"
          icon={ImageOff}
          title="No media found"
          description={
            activeFilters.length > 0 
              ? "No media matches your current filters. Try adjusting your search criteria."
              : "Upload your first image or video to get started."
          }
          action={
            activeFilters.length > 0 ? {
              label: "Clear Filters",
              onClick: () => setFilters(INITIAL_FILTER_STATE)
            } : undefined
          }
        />
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {paginatedMedia.map((item) => (
            <div key={item.id} className="relative">
              {/* Selection checkbox overlay */}
              <div className="absolute top-2 left-2 z-10">
                <input
                  type="checkbox"
                  checked={selectedIds.includes(item.id)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedIds(prev => [...prev, item.id])
                    } else {
                      setSelectedIds(prev => prev.filter(id => id !== item.id))
                    }
                  }}
                  className="rounded border-border bg-background/80 backdrop-blur-sm"
                />
              </div>
              <MediaCard
                media={item}
                onClick={handleItemClick}
                className={cn(
                  selectedIds.includes(item.id) && "ring-2 ring-primary"
                )}
              />
            </div>
          ))}
        </div>
      ) : (
        <DataTable
          data={paginatedMedia}
          selectedIds={selectedIds}
          onSelectionChange={handleSelectionChange}
          onItemClick={handleItemClick}
          onDownload={handleDownload}
          onDelete={handleDelete}
        />
      )}

      {/* Pagination Controls */}
      {totalItems > 0 && (
        <Card>
          <CardContent className="py-4">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="text-sm text-muted-foreground">
                Showing {((pagination.currentPage - 1) * pagination.itemsPerPage) + 1}-{Math.min(pagination.currentPage * pagination.itemsPerPage, totalItems)} of {totalItems}
              </div>
              
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(pagination.currentPage - 1)}
                    disabled={pagination.currentPage <= 1}
                  >
                    Previous
                  </Button>
                  
                  <span className="text-sm">
                    Page {pagination.currentPage} of {pagination.totalPages}
                  </span>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(pagination.currentPage + 1)}
                    disabled={pagination.currentPage >= pagination.totalPages}
                  >
                    Next
                  </Button>
                </div>
                
                <Select value={pagination.itemsPerPage.toString()} onValueChange={handleItemsPerPageChange}>
                  <SimpleSelectItem value="24">24 per page</SimpleSelectItem>
                  <SimpleSelectItem value="48">48 per page</SimpleSelectItem>
                  <SimpleSelectItem value="96">96 per page</SimpleSelectItem>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Bulk Delete Confirmation Dialog */}
      <Dialog open={bulkDeleteDialogOpen} onOpenChange={setBulkDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete {selectedIds.length} items?</DialogTitle>
            <DialogDescription>
              This action cannot be undone. The selected media files will be permanently deleted from your library.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setBulkDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={confirmBulkDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}