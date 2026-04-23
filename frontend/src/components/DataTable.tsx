import { useState } from 'react'
import { ArrowUpDown, Download, Trash2, Film } from 'lucide-react'
import { Button, Badge } from '@/components/ui'
import { cn } from '@/lib/utils'
import type { MediaSummary } from '../types/api'
import { formatFileSize, formatRelativeTime } from '../utils/format'

type SortField = 'original_filename' | 'media_type' | 'file_size' | 'status' | 'uploaded_at'
type SortDirection = 'asc' | 'desc'

interface DataTableProps {
  data: MediaSummary[]
  selectedIds: number[]
  onSelectionChange: (selectedIds: number[]) => void
  onItemClick?: (mediaId: number) => void
  onDownload?: (mediaId: number) => void
  onDelete?: (mediaId: number) => void
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

export function DataTable({
  data,
  selectedIds,
  onSelectionChange,
  onItemClick,
  onDownload,
  onDelete,
  className
}: DataTableProps) {
  const [sortField, setSortField] = useState<SortField>('uploaded_at')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const sortedData = [...data].sort((a, b) => {
    let aValue: any = a[sortField]
    let bValue: any = b[sortField]

    if (sortField === 'uploaded_at') {
      aValue = new Date(aValue).getTime()
      bValue = new Date(bValue).getTime()
    } else if (sortField === 'file_size') {
      aValue = Number(aValue)
      bValue = Number(bValue)
    } else if (typeof aValue === 'string') {
      aValue = aValue.toLowerCase()
      bValue = bValue.toLowerCase()
    }

    if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1
    if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1
    return 0
  })

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      onSelectionChange(data.map(item => item.id))
    } else {
      onSelectionChange([])
    }
  }

  const handleSelectItem = (id: number, checked: boolean) => {
    if (checked) {
      onSelectionChange([...selectedIds, id])
    } else {
      onSelectionChange(selectedIds.filter(selectedId => selectedId !== id))
    }
  }

  const isAllSelected = data.length > 0 && selectedIds.length === data.length
  const isIndeterminate = selectedIds.length > 0 && selectedIds.length < data.length

  const SortableHeader = ({ field, children }: { field: SortField; children: React.ReactNode }) => (
    <button
      className="flex items-center gap-1 hover:text-foreground transition-colors text-left font-medium"
      onClick={() => handleSort(field)}
    >
      {children}
      <ArrowUpDown 
        size={14} 
        className={cn(
          "opacity-50",
          sortField === field && "opacity-100"
        )}
      />
    </button>
  )

  return (
    <div className={cn("w-full overflow-hidden rounded-lg border border-border", className)}>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-muted/50">
            <tr className="border-b border-border">
              {/* Checkbox column */}
              <th className="w-10 p-3">
                <input
                  type="checkbox"
                  checked={isAllSelected}
                  ref={(el) => {
                    if (el) el.indeterminate = isIndeterminate
                  }}
                  onChange={(e) => handleSelectAll(e.target.checked)}
                  className="rounded border-border"
                />
              </th>
              
              {/* Thumbnail column */}
              <th className="w-20 p-3 text-left text-sm font-medium text-muted-foreground">
                Thumbnail
              </th>
              
              {/* Filename column */}
              <th className="p-3 text-left text-sm font-medium text-muted-foreground">
                <SortableHeader field="original_filename">Filename</SortableHeader>
              </th>
              
              {/* Type column - hidden on mobile */}
              <th className="hidden md:table-cell w-20 p-3 text-left text-sm font-medium text-muted-foreground">
                <SortableHeader field="media_type">Type</SortableHeader>
              </th>
              
              {/* Size column - hidden on mobile */}
              <th className="hidden md:table-cell w-24 p-3 text-left text-sm font-medium text-muted-foreground">
                <SortableHeader field="file_size">Size</SortableHeader>
              </th>
              
              {/* Status column */}
              <th className="w-28 p-3 text-left text-sm font-medium text-muted-foreground">
                <SortableHeader field="status">Status</SortableHeader>
              </th>
              
              {/* Date column - hidden on mobile */}
              <th className="hidden md:table-cell w-32 p-3 text-left text-sm font-medium text-muted-foreground">
                <SortableHeader field="uploaded_at">Date</SortableHeader>
              </th>
              
              {/* Actions column */}
              <th className="w-20 p-3 text-left text-sm font-medium text-muted-foreground">
                Actions
              </th>
            </tr>
          </thead>
          
          <tbody>
            {sortedData.map((item) => {
              const isSelected = selectedIds.includes(item.id)
              
              return (
                <tr 
                  key={item.id}
                  className={cn(
                    "border-b border-border hover:bg-muted/50 transition-colors",
                    isSelected && "bg-muted/30"
                  )}
                >
                  {/* Checkbox */}
                  <td className="p-3">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={(e) => handleSelectItem(item.id, e.target.checked)}
                      className="rounded border-border"
                    />
                  </td>
                  
                  {/* Thumbnail */}
                  <td className="p-3">
                    <div className="w-12 h-8 rounded overflow-hidden bg-muted flex items-center justify-center">
                      {item.file ? (
                        item.media_type === 'video' ? (
                          <div className="text-muted-foreground">
                            <Film size={14} />
                          </div>
                        ) : (
                          <img
                            src={item.file}
                            alt={item.original_filename}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              e.currentTarget.style.display = 'none'
                              const parent = e.currentTarget.parentElement
                              if (parent) {
                                parent.innerHTML = '<span class="text-xs text-muted-foreground">IMG</span>'
                              }
                            }}
                          />
                        )
                      ) : (
                        <span className="text-xs text-muted-foreground">
                          {item.media_type === 'video' ? 'VID' : 'IMG'}
                        </span>
                      )}
                    </div>
                  </td>
                  
                  {/* Filename */}
                  <td className="p-3">
                    <button
                      className="text-left hover:text-primary transition-colors"
                      onClick={() => onItemClick?.(item.id)}
                    >
                      <div className="font-medium text-sm truncate max-w-xs">
                        {item.original_filename}
                      </div>
                      {/* Show type and size on mobile */}
                      <div className="md:hidden text-xs text-muted-foreground mt-1">
                        {item.media_type} · {formatFileSize(item.file_size)}
                      </div>
                    </button>
                  </td>
                  
                  {/* Type - hidden on mobile */}
                  <td className="hidden md:table-cell p-3 text-sm text-muted-foreground capitalize">
                    {item.media_type}
                  </td>
                  
                  {/* Size - hidden on mobile */}
                  <td className="hidden md:table-cell p-3 text-sm text-muted-foreground">
                    {formatFileSize(item.file_size)}
                  </td>
                  
                  {/* Status */}
                  <td className="p-3">
                    <Badge className={cn("text-xs", getStatusColor(item.status))}>
                      {item.status}
                    </Badge>
                  </td>
                  
                  {/* Date - hidden on mobile */}
                  <td className="hidden md:table-cell p-3 text-sm text-muted-foreground">
                    {formatRelativeTime(item.uploaded_at)}
                  </td>
                  
                  {/* Actions */}
                  <td className="p-3">
                    <div className="flex items-center gap-1">
                      {onDownload && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onDownload(item.id)}
                          className="h-8 w-8 p-0"
                          title="Download"
                        >
                          <Download size={14} />
                        </Button>
                      )}
                      {onDelete && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onDelete(item.id)}
                          className="h-8 w-8 p-0 text-destructive hover:text-destructive"
                          title="Delete"
                        >
                          <Trash2 size={14} />
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      
      {data.length === 0 && (
        <div className="p-8 text-center text-muted-foreground">
          No data available
        </div>
      )}
    </div>
  )
}