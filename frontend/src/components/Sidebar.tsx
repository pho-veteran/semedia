import type { RuntimeStatus } from '../types/api'
import { RuntimeBadge } from './RuntimeBadge'

type SidebarRoute =
  | { page: 'dashboard' }
  | { page: 'search' }
  | { page: 'media'; mediaId: number; startTime: number | null }

interface SidebarProps {
  activeUploadCount: number
  currentPage: SidebarRoute['page']
  onNavigate: (route: SidebarRoute) => void
  onToggleTheme: () => void
  runtime: RuntimeStatus | null
  runtimeError: string | null
  theme: 'light' | 'dark'
}

export function Sidebar({
  activeUploadCount,
  currentPage,
  onNavigate,
  onToggleTheme,
  runtime,
  runtimeError,
  theme,
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
        </nav>
      </div>

      <div className="sidebar-bottom">
        <RuntimeBadge error={runtimeError} runtime={runtime} />
        <button className="theme-toggle" onClick={onToggleTheme} type="button">
          <span className="nav-icon">{theme === 'dark' ? '☼' : '☾'}</span>
          <span>{theme === 'dark' ? 'Light theme' : 'Dark theme'}</span>
        </button>
      </div>
    </aside>
  )
}
