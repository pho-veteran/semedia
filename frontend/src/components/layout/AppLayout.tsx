import { Sidebar } from './Sidebar'
import type { RuntimeStatus } from '@/types/api'

type SidebarRoute =
  | { page: 'dashboard' }
  | { page: 'search' }
  | { page: 'library' }
  | { page: 'evaluation' }
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
        className="skip-nav"
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

      <main
        id="main-content"
        className="flex-1 overflow-y-auto overflow-x-hidden"
      >
        <div className="max-w-[1440px] mx-auto px-4 py-6 md:px-6 md:py-8 lg:px-10 lg:py-10">
          {children}
        </div>
      </main>
    </div>
  )
}
