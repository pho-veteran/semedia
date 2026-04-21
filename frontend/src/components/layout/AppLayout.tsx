import { Sidebar } from './Sidebar'
import type { RuntimeStatus } from '@/types/api'

type SidebarRoute =
  | { page: 'dashboard' }
  | { page: 'search' }
  | { page: 'library' }
  | { page: 'media'; mediaId: number; startTime: number | null }

interface AppLayoutProps {
  activeUploadCount: number
  currentPage: SidebarRoute['page']
  onNavigate: (route: SidebarRoute) => void
  runtime: RuntimeStatus | null
  runtimeError: string | null
  children: React.ReactNode
}

export function AppLayout({
  activeUploadCount,
  currentPage,
  onNavigate,
  runtime,
  runtimeError,
  children,
}: AppLayoutProps) {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-md focus:shadow-lg"
      >
        Skip to main content
      </a>
      
      <Sidebar
        activeUploadCount={activeUploadCount}
        currentPage={currentPage}
        onNavigate={onNavigate}
        runtime={runtime}
        runtimeError={runtimeError}
      />
      <main id="main-content" className="flex-1 overflow-y-auto">
        <div className="max-w-[1400px] mx-auto px-3 py-4 md:px-4 md:py-6 lg:px-6 lg:py-8">
          {children}
        </div>
      </main>
    </div>
  )
}