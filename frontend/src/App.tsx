import { startTransition, useEffect, useRef, useState } from 'react'
import { toast, Toaster } from 'sonner'
import './App.css'
import {
  deleteMediaById,
  getMediaDetail,
  getMediaList,
  getRuntimeStatus,
  uploadMediaFile,
} from './api/client'
import { AppLayout } from './components/layout/AppLayout'
import { DashboardPage } from './pages/DashboardPage'
import { LibraryPage } from './pages/LibraryPage'
import { MediaDetailPage } from './pages/MediaDetailPage'
import { SearchPage } from './pages/SearchPage'
import { ShortcutsHelpDialog } from './components/ShortcutsHelpDialog'
import { useKeyboardShortcuts, KEYBOARD_SHORTCUTS } from './hooks/useKeyboardShortcuts'
import type {
  MediaSummary,
  PaginatedResponse,
  RuntimeStatus,
  UploadQueueItem,
} from './types/api'
import { getErrorMessage, isTerminalStatus } from './utils/format'

type AppRoute =
  | { page: 'dashboard' }
  | { page: 'search' }
  | { page: 'library' }
  | { page: 'media'; mediaId: number; startTime: number | null }

const EMPTY_MEDIA_PAGE: PaginatedResponse<MediaSummary> = {
  count: 0,
  next: null,
  previous: null,
  results: [],
}

function parseHashRoute(hash: string): AppRoute {
  const normalized = hash.replace(/^#/, '') || '/dashboard'
  const url = new URL(
    normalized.startsWith('/') ? normalized : `/${normalized}`,
    'http://semedia.local',
  )
  const segments = url.pathname.split('/').filter(Boolean)

  if (segments[0] === 'search') {
    return { page: 'search' }
  }

  if (segments[0] === 'library') {
    return { page: 'library' }
  }

  if (segments[0] === 'media' && segments[1]) {
    const mediaId = Number(segments[1])
    if (Number.isFinite(mediaId)) {
      const startParam = url.searchParams.get('start')
      return {
        page: 'media',
        mediaId,
        startTime: startParam ? Number(startParam) : null,
      }
    }
  }

  return { page: 'dashboard' }
}

function routeToHash(route: AppRoute): string {
  if (route.page === 'search') {
    return '#/search'
  }

  if (route.page === 'library') {
    return '#/library'
  }

  if (route.page === 'media') {
    const params = new URLSearchParams()
    if (route.startTime !== null && Number.isFinite(route.startTime)) {
      params.set('start', String(route.startTime))
    }
    const query = params.toString()
    return `#/media/${route.mediaId}${query ? `?${query}` : ''}`
  }

  return '#/dashboard'
}

function App() {
  const [route, setRoute] = useState<AppRoute>(() => parseHashRoute(window.location.hash))
  const [previousPage, setPreviousPage] = useState<'dashboard' | 'search' | 'library'>('dashboard')
  const [runtime, setRuntime] = useState<RuntimeStatus | null>(null)
  const [runtimeError, setRuntimeError] = useState<string | null>(null)
  const [mediaPage, setMediaPage] = useState<PaginatedResponse<MediaSummary>>(EMPTY_MEDIA_PAGE)
  const [mediaLoading, setMediaLoading] = useState(true)
  const [mediaError, setMediaError] = useState<string | null>(null)
  const [uploads, setUploads] = useState<UploadQueueItem[]>([])
  const [showShortcutsHelp, setShowShortcutsHelp] = useState(false)
  const pollRef = useRef<Set<number>>(new Set())
  const mountedRef = useRef(true)
  const searchInputRef = useRef<HTMLInputElement>(null!)

  useEffect(() => {
    if (!window.location.hash) {
      window.location.hash = routeToHash({ page: 'dashboard' })
    }

    const handleHashChange = () => {
      startTransition(() => {
        setRoute(parseHashRoute(window.location.hash))
      })
    }

    window.addEventListener('hashchange', handleHashChange)
    return () => {
      window.removeEventListener('hashchange', handleHashChange)
    }
  }, [])

  useEffect(() => {
    return () => {
      mountedRef.current = false
    }
  }, [])

  // Register global keyboard shortcuts
  useKeyboardShortcuts({
    shortcuts: [
      {
        key: KEYBOARD_SHORTCUTS.FOCUS_SEARCH,
        description: 'Focus search input',
        handler: () => {
          // Navigate to search page if not already there
          if (route.page !== 'search') {
            navigate({ page: 'search' })
          }
          // Focus will be handled by SearchPage component
          searchInputRef.current?.focus()
        },
      },
      {
        key: KEYBOARD_SHORTCUTS.OPEN_UPLOAD,
        description: 'Open upload dialog',
        handler: () => {
          // Navigate to dashboard
          if (route.page !== 'dashboard') {
            navigate({ page: 'dashboard' })
          }
          // Focus on upload dropzone
          const dropzone = document.querySelector('[data-upload-dropzone]') as HTMLElement
          if (dropzone) {
            dropzone.focus()
          }
        },
      },
      {
        key: KEYBOARD_SHORTCUTS.SHOW_HELP,
        description: 'Show keyboard shortcuts',
        handler: () => {
          setShowShortcutsHelp(true)
        },
      },
    ],
    enabled: true,
  })

  const navigate = (nextRoute: AppRoute) => {
    const nextHash = routeToHash(nextRoute)
    
    // Save previous page before navigating to media detail
    if (nextRoute.page === 'media' && route.page !== 'media') {
      setPreviousPage(route.page)
    }
    
    startTransition(() => {
      setRoute(nextRoute)
      window.location.hash = nextHash
    })
  }

  const refreshMediaList = async () => {
    try {
      setMediaLoading(true)
      const nextPage = await getMediaList()
      if (!mountedRef.current) {
        return
      }
      setMediaPage(nextPage)
      setMediaError(null)
    } catch (error) {
      if (!mountedRef.current) {
        return
      }
      setMediaError(getErrorMessage(error))
    } finally {
      if (mountedRef.current) {
        setMediaLoading(false)
      }
    }
  }

  useEffect(() => {
    let active = true
    const loadRuntime = async () => {
      try {
        const nextRuntime = await getRuntimeStatus()
        if (!mountedRef.current || !active) {
          return
        }
        setRuntime(nextRuntime)
        setRuntimeError(null)
      } catch (error) {
        if (!mountedRef.current || !active) {
          return
        }
        setRuntimeError(getErrorMessage(error))
      }
    }

    void loadRuntime()
    const runtimeInterval = window.setInterval(() => {
      void loadRuntime()
    }, 30000)

    return () => {
      active = false
      window.clearInterval(runtimeInterval)
    }
  }, [])

  useEffect(() => {
    let active = true
    const loadMedia = async () => {
      try {
        setMediaLoading(true)
        const nextPage = await getMediaList()
        if (!mountedRef.current || !active) {
          return
        }
        setMediaPage(nextPage)
        setMediaError(null)
      } catch (error) {
        if (!mountedRef.current || !active) {
          return
        }
        setMediaError(getErrorMessage(error))
      } finally {
        if (mountedRef.current && active) {
          setMediaLoading(false)
        }
      }
    }

    void loadMedia()
    return () => {
      active = false
    }
  }, [])

  const pollMediaUntilSettled = async (mediaId: number, uploadId: string) => {
    if (pollRef.current.has(mediaId)) {
      return
    }

    pollRef.current.add(mediaId)
    try {
      for (let attempt = 0; attempt < 120; attempt += 1) {
        const detail = await getMediaDetail(mediaId)
        if (!mountedRef.current) {
          return
        }

        setUploads((currentUploads) =>
          currentUploads.map((item) =>
            item.id === uploadId
              ? {
                  ...item,
                  mediaId: detail.id,
                  status: detail.status,
                  message: detail.error_message || detail.caption || item.message,
                  updatedAt: detail.updated_at,
                }
              : item,
          ),
        )

        await refreshMediaList()
        if (isTerminalStatus(detail.status)) {
          if (detail.status === 'completed') {
            toast.success(`Processing completed: ${detail.original_filename}`, {
              duration: 5000,
            })
          } else if (detail.status === 'failed') {
            toast.error(`Processing failed: ${detail.original_filename}`, {
              description: detail.error_message || 'Unknown error',
              duration: 10000,
            })
          }
          return
        }

        await new Promise((resolve) => {
          window.setTimeout(resolve, 3000)
        })
      }
    } catch (error) {
      if (!mountedRef.current) {
        return
      }

      setUploads((currentUploads) =>
        currentUploads.map((item) =>
          item.id === uploadId
            ? {
                ...item,
                status: 'failed',
                message: getErrorMessage(error),
              }
            : item,
        ),
      )
    } finally {
      pollRef.current.delete(mediaId)
    }
  }

  const handleFilesSelected = async (files: File[]) => {
    for (const file of files) {
      const uploadId = crypto.randomUUID()
      
      // Create preview URL for images and videos
      const previewUrl = URL.createObjectURL(file)
      const mediaType = file.type.startsWith('image/') ? 'image' : 'video'
      
      setUploads((currentUploads) => [
        {
          id: uploadId,
          name: file.name,
          mediaId: null,
          status: 'uploading',
          updatedAt: new Date().toISOString(),
          message: 'Uploading to the backend.',
          previewUrl,
          mediaType,
        },
        ...currentUploads,
      ])

      try {
        const response = await uploadMediaFile(file)
        const summary = response.data
        if (!mountedRef.current) {
          return
        }

        setUploads((currentUploads) =>
          currentUploads.map((item) =>
            item.id === uploadId
              ? {
                  ...item,
                  mediaId: summary.id,
                  status: summary.status,
                  updatedAt: summary.updated_at,
                  message: response.message || summary.caption || 'Upload completed.',
                }
              : item,
          ),
        )

        await refreshMediaList()

        if (!isTerminalStatus(summary.status)) {
          void pollMediaUntilSettled(summary.id, uploadId)
        } else if (summary.status === 'completed') {
          toast.success(`Upload completed: ${file.name}`, {
            duration: 5000,
          })
        }
      } catch (error) {
        if (!mountedRef.current) {
          return
        }

        const errorMessage = getErrorMessage(error)
        toast.error(`Upload failed: ${file.name}`, {
          description: errorMessage,
          duration: 10000,
          action: {
            label: 'Retry',
            onClick: () => handleFilesSelected([file]),
          },
        })

        setUploads((currentUploads) =>
          currentUploads.map((item) =>
            item.id === uploadId
              ? {
                  ...item,
                  status: 'failed',
                  message: errorMessage,
                }
              : item,
          ),
        )
      }
    }
  }

  const handleDeleteMedia = async (mediaId: number) => {
    await deleteMediaById(mediaId)
    setUploads((currentUploads) => currentUploads.filter((item) => item.mediaId !== mediaId))
    await refreshMediaList()
  }

  const openMedia = (mediaId: number, startTime: number | null = null) => {
    navigate({ page: 'media', mediaId, startTime })
  }

  const handleDeletedFromDetail = async (mediaId: number) => {
    await handleDeleteMedia(mediaId)
    navigate({ page: previousPage })
  }

  const handleCancelUpload = (uploadId: string) => {
    setUploads((currentUploads) =>
      currentUploads.map((item) =>
        item.id === uploadId
          ? {
              ...item,
              status: 'failed',
              message: 'Upload cancelled by user',
            }
          : item,
      ),
    )
    toast.info('Upload cancelled')
  }

  const handleRetryUpload = async (uploadId: string) => {
    const uploadItem = uploads.find((item) => item.id === uploadId)
    if (!uploadItem) {
      return
    }

    // Reset the upload status to uploading
    setUploads((currentUploads) =>
      currentUploads.map((item) =>
        item.id === uploadId
          ? {
              ...item,
              status: 'uploading',
              message: 'Retrying upload...',
              updatedAt: new Date().toISOString(),
            }
          : item,
      ),
    )

    // Note: In a real implementation, we would need to store the original file
    // and re-upload it. For now, we'll just show a message that retry is not fully implemented.
    toast.error('Retry functionality requires storing original files - not fully implemented yet')
    
    // Reset back to failed after a short delay
    setTimeout(() => {
      setUploads((currentUploads) =>
        currentUploads.map((item) =>
          item.id === uploadId
            ? {
                ...item,
                status: 'failed',
                message: 'Retry not available - original file not stored',
              }
            : item,
        ),
      )
    }, 2000)
  }

  const activeUploadCount = uploads.filter((item) => !isTerminalStatus(item.status)).length
  const latestMedia = mediaPage.results.slice(0, 12)

  let content = (
    <DashboardPage
      mediaError={mediaError}
      mediaItems={latestMedia}
      mediaLoading={mediaLoading}
      onFilesSelected={handleFilesSelected}
      onOpenMedia={openMedia}
      onRefreshMedia={() => void refreshMediaList()}
      runtime={runtime}
      runtimeError={runtimeError}
      uploads={uploads}
      onCancelUpload={handleCancelUpload}
      onRetryUpload={handleRetryUpload}
    />
  )

  if (route.page === 'search') {
    content = <SearchPage onOpenMedia={openMedia} searchInputRef={searchInputRef} />
  }

  if (route.page === 'library') {
    content = <LibraryPage onOpenMedia={openMedia} onDeleteMedia={handleDeleteMedia} />
  }

  if (route.page === 'media') {
    content = (
      <MediaDetailPage
        initialStartTime={route.startTime}
        mediaId={route.mediaId}
        onBack={() => navigate({ page: previousPage })}
        onDeleted={handleDeletedFromDetail}
        onNavigateToMedia={openMedia}
      />
    )
  }

  return (
    <AppLayout
      activeUploadCount={activeUploadCount}
      currentPage={route.page}
      onNavigate={navigate}
      runtime={runtime}
      runtimeError={runtimeError}
    >
      {content}
      <ShortcutsHelpDialog open={showShortcutsHelp} onOpenChange={setShowShortcutsHelp} />
      <Toaster 
        position="bottom-right" 
        closeButton 
        richColors
      />
    </AppLayout>
  )
}

export default App
