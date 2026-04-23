import { LayoutDashboard, Search, FolderOpen, Menu, ChevronLeft, ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { Button, Badge, Sheet, SheetContent, SheetTrigger } from '@/components/ui'
import { ThemeToggle } from '../ThemeToggle'
import { RuntimeBadge } from '../RuntimeBadge'
import { cn } from '@/lib/utils'
import type { RuntimeStatus } from '@/types/api'

type SidebarRoute =
  | { page: 'dashboard' }
  | { page: 'search' }
  | { page: 'library' }
  | { page: 'media'; mediaId: number; startTime: number | null }

interface SidebarProps {
  activeUploadCount: number
  currentPage: SidebarRoute['page']
  onNavigate: (route: SidebarRoute) => void
  runtime: RuntimeStatus | null
  runtimeError: string | null
}

interface NavItemProps {
  icon: React.ReactNode
  label: string
  badge?: number
  active: boolean
  onClick: () => void
  collapsed?: boolean
}

function NavItem({ icon, label, badge, active, onClick, collapsed = false }: NavItemProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all w-full relative',
        active
          ? 'bg-accent text-accent-foreground font-medium shadow-sm'
          : 'text-muted-foreground hover:bg-accent/50 hover:text-accent-foreground',
        collapsed && 'justify-center px-2'
      )}
      title={collapsed ? label : undefined}
    >
      {icon}
      {!collapsed && (
        <>
          <span className="flex-1 text-left">{label}</span>
          {badge && badge > 0 && (
            <Badge variant="secondary" className="text-xs bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300">
              {badge}
            </Badge>
          )}
        </>
      )}
      {collapsed && badge && badge > 0 && (
        <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-blue-500 text-white text-xs flex items-center justify-center">
          {badge}
        </span>
      )}
    </button>
  )
}

function SidebarContent({ 
  currentPage, 
  onNavigate, 
  runtime, 
  runtimeError,
  collapsed = false,
  onToggleCollapse
}: SidebarProps & { collapsed?: boolean; onToggleCollapse?: () => void }) {
  return (
    <div className="flex flex-col h-full">

      <div className={cn(
        "h-16 flex items-center transition-all",
        collapsed ? "px-2 justify-center" : "px-4"
      )}>
        {collapsed ? (
          <div className="w-10 h-10 bg-gradient-to-br from-foreground to-foreground/80 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg">
            <span className="text-background font-black text-xl tracking-tight">S</span>
          </div>
        ) : (
          <button
            onClick={() => onNavigate({ page: 'dashboard' })}
            className="flex items-center gap-3 hover:opacity-80 transition-opacity group"
            aria-label="Go to dashboard"
          >
            <div className="w-10 h-10 bg-gradient-to-br from-foreground to-foreground/80 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg group-hover:shadow-xl transition-shadow">
              <span className="text-background font-black text-xl tracking-tight">S</span>
            </div>
            <span className="font-bold text-xl tracking-tight leading-none">Semedia</span>
          </button>
        )}
      </div>
      
      <nav className="flex-1 overflow-y-auto py-4" aria-label="Main navigation">
        <div className={cn("space-y-1", collapsed ? "px-2" : "px-3")}>
          <NavItem
            icon={<LayoutDashboard size={20} />}
            label="Dashboard"
            active={currentPage === 'dashboard'}
            onClick={() => onNavigate({ page: 'dashboard' })}
            collapsed={collapsed}
          />
          <NavItem
            icon={<Search size={20} />}
            label="Search"
            active={currentPage === 'search'}
            onClick={() => onNavigate({ page: 'search' })}
            collapsed={collapsed}
          />
          <NavItem
            icon={<FolderOpen size={20} />}
            label="Library"
            active={currentPage === 'library'}
            onClick={() => onNavigate({ page: 'library' })}
            collapsed={collapsed}
          />
        </div>
      </nav>
      

      <div className="mt-auto">
        {!collapsed ? (
          <div className="p-4 space-y-3">
            <div className="flex items-center justify-between gap-2">
              <ThemeToggle showLabel />
              {onToggleCollapse && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onToggleCollapse}
                  aria-label="Collapse sidebar"
                  className="h-8 w-8 flex-shrink-0"
                >
                  <ChevronLeft size={16} />
                </Button>
              )}
            </div>
            <RuntimeBadge runtime={runtime} error={runtimeError} />
          </div>
        ) : (
          <div className="p-2 space-y-2 flex flex-col items-center">
            <ThemeToggle />
            {onToggleCollapse && (
              <Button
                variant="ghost"
                size="icon"
                onClick={onToggleCollapse}
                aria-label="Expand sidebar"
                className="h-8 w-8"
              >
                <ChevronRight size={16} />
              </Button>
            )}
            <RuntimeBadge runtime={runtime} error={runtimeError} compact />
          </div>
        )}
      </div>
    </div>
  )
}

export function Sidebar(props: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className={cn(
        "hidden md:flex flex-col shrink-0 border-r border-border bg-card transition-all duration-300",
        collapsed ? "w-[72px]" : "w-[260px]"
      )}>
        <SidebarContent 
          {...props} 
          collapsed={collapsed}
          onToggleCollapse={() => setCollapsed(!collapsed)}
        />
      </aside>
      
      {/* Mobile Sidebar Sheet */}
      <div className="md:hidden">
        <Sheet>
          <SheetTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="fixed top-4 left-4 z-40"
              aria-label="Open navigation menu"
            >
              <Menu size={20} />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-[260px] p-0">
            <SidebarContent {...props} />
          </SheetContent>
        </Sheet>
      </div>
    </>
  )
}