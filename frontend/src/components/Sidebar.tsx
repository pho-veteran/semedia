import type { RuntimeStatus } from '../types/api'
import { RuntimeBadge } from './RuntimeBadge'
import { ThemeToggle } from './ThemeToggle'

type SidebarRoute =
  | { page: 'dashboard' }
  | { page: 'search' }
  | { page: 'media'; mediaId: number; startTime: number | null }
  | { page: 'demo' }

interface SidebarProps {
  activeUploadCount: number
  currentPage: SidebarRoute['page']
  onNavigate: (route: SidebarRoute) => void
  runtime: RuntimeStatus | null
  runtimeError: string | null
}

export function Sidebar({
  activeUploadCount,
  currentPage,
  onNavigate,
  runtime,
  runtimeError,
}: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <button className="brand" onClick={() => onNavigate({ page: 'dashboard' })} type="button">
          <span className="brand-mark">S</span>
          <span className="brand-copy">
            <strong>Semedia</strong>
            <small>Semantic media search</small>
          </span>
        </button>

        <nav className="nav-menu">
          <button
            className={`nav-item ${currentPage === 'dashboard' ? 'active' : ''}`}
            onClick={() => onNavigate({ page: 'dashboard' })}
            type="button"
          >
            <span className="nav-icon">↑</span>
            <span>Upload Desk</span>
            {activeUploadCount > 0 ? <span className="queue-badge">{activeUploadCount}</span> : null}
          </button>

          <button
            className={`nav-item ${currentPage === 'search' ? 'active' : ''}`}
            onClick={() => onNavigate({ page: 'search' })}
            type="button"
          >
            <span className="nav-icon">⌕</span>
            <span>Search</span>
          </button>

          <button
            className={`nav-item ${currentPage === 'demo' ? 'active' : ''}`}
            onClick={() => onNavigate({ page: 'demo' })}
            type="button"
          >
            <span className="nav-icon">🎨</span>
            <span>Component Demo</span>
          </button>
        </nav>
      </div>

      <div className="sidebar-bottom">
        <RuntimeBadge error={runtimeError} runtime={runtime} />
        <ThemeToggle />
      </div>
    </aside>
  )
}
