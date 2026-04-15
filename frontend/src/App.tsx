import { startTransition, useEffect, useRef, useState } from 'react'
import './App.css'
import {
  deleteMediaById,
  getMediaDetail,
  getMediaList,
  getRuntimeStatus,
  uploadMediaFile,
} from './api/client'
import { Sidebar } from './components/Sidebar'
import { DashboardPage } from './pages/DashboardPage'
import { MediaDetailPage } from './pages/MediaDetailPage'
import { SearchPage } from './pages/SearchPage'
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

function getInitialTheme(): 'light' | 'dark' {
  const storedTheme = window.localStorage.getItem('semedia-theme')
  if (storedTheme === 'light' || storedTheme === 'dark') {
    return storedTheme
  }

  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function App() {
  const [route, setRoute] = useState<AppRoute>(() => parseHashRoute(window.location.hash))
  const [theme, setTheme] = useState<'light' | 'dark'>(getInitialTheme)
  const [runtime, setRuntime] = useState<RuntimeStatus | null>(null)
  const [runtimeError, setRuntimeError] = useState<string | null>(null)
  const [mediaPage, setMediaPage] = useState<PaginatedResponse<MediaSummary>>(EMPTY_MEDIA_PAGE)
  const [mediaLoading, setMediaLoading] = useState(true)
  const [mediaError, setMediaError] = useState<string | null>(null)
  const [uploads, setUploads] = useState<UploadQueueItem[]>([])
  const pollRef = useRef<Set<number>>(new Set())
  const mountedRef = useRef(true)

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    window.localStorage.setItem('semedia-theme', theme)
  }, [theme])

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

  const navigate = (nextRoute: AppRoute) => {
    const nextHash = routeToHash(nextRoute)
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
      setUploads((currentUploads) => [
        {
          id: uploadId,
          name: file.name,
          mediaId: null,
          status: 'uploading',
          updatedAt: new Date().toISOString(),
          message: 'Uploading to the backend.',
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
    navigate({ page: 'dashboard' })
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
    />
  )

  if (route.page === 'search') {
    content = <SearchPage onOpenMedia={openMedia} />
  }

  if (route.page === 'media') {
    content = (
      <MediaDetailPage
        initialStartTime={route.startTime}
        mediaId={route.mediaId}
        onBack={() => navigate({ page: 'dashboard' })}
        onDeleted={handleDeletedFromDetail}
        onNavigateToMedia={openMedia}
      />
    )
  }

  return (
    <div className="app-shell">
      <Sidebar
        activeUploadCount={activeUploadCount}
        currentPage={route.page}
        onNavigate={navigate}
        onToggleTheme={() => setTheme((currentTheme) => (currentTheme === 'dark' ? 'light' : 'dark'))}
        runtime={runtime}
        runtimeError={runtimeError}
        theme={theme}
      />
      <main className="main-content">{content}</main>
    </div>
  )
}

export default App
