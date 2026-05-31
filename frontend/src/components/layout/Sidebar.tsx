import { LayoutDashboard, Search, FolderOpen, FlaskConical, Menu, ChevronLeft, ChevronRight } from 'lucide-react'
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
  | { page: 'evaluation' }
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
        'group relative flex items-center gap-3 rounded-xl text-sm font-medium',
        'transition-all duration-150 ease-smooth',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
        collapsed ? 'w-10 h-10 justify-center px-0 mx-auto' : 'w-full px-3 py-2.5',
        active
          ? [
              'bg-brand/10 text-brand',
              'before:absolute before:left-0 before:top-1/2 before:-translate-y-1/2',
              'before:h-5 before:w-0.5 before:rounded-full before:bg-brand',
              'before:transition-all before:duration-200',
            ].join(' ')
          : 'text-muted-foreground hover:bg-muted/70 hover:text-foreground',
      )}
      title={collapsed ? label : undefined}
      aria-current={active ? 'page' : undefined}
    >
      <span className={cn(
        "flex-shrink-0 transition-transform duration-150",
        active ? "text-brand" : "text-muted-foreground group-hover:text-foreground",
        "group-hover:scale-105",
      )}>
        {icon}
      </span>

      {!collapsed && (
        <span className="flex-1 text-left">{label}</span>
      )}

      {badge !== undefined && badge > 0 && (
        collapsed ? (
          <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-brand text-[10px] font-bold text-brand-foreground">
            {badge > 9 ? '9+' : badge}
          </span>
        ) : (
          <Badge variant="default" className="ml-auto text-[10px] h-5 min-w-[20px] px-1.5">
            {badge}
          </Badge>
        )
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
  onToggleCollapse,
}: SidebarProps & { collapsed?: boolean; onToggleCollapse?: () => void }) {
  return (
    <div className="flex flex-col h-full">

      <div className={cn(
        "flex items-center h-[60px] shrink-0",
        collapsed ? "justify-center px-2" : "px-4 gap-3"
      )}>
        <button
          onClick={() => onNavigate({ page: 'dashboard' })}
          className="group flex items-center gap-3 focus-visible:outline-none"
          aria-label="Go to dashboard"
        >
          <div className={cn(
            "flex items-center justify-center rounded-2xl flex-shrink-0",
            "bg-brand-gradient shadow-glow-sm",
            "transition-transform duration-150 group-hover:scale-105",
            "h-9 w-9",
          )}>
            <span className="text-white font-black text-lg leading-none tracking-tighter">S</span>
          </div>
          {!collapsed && (
            <span className="font-bold text-lg tracking-tight leading-none text-foreground">
              Semedia
            </span>
          )}
        </button>
      </div>

      <div className="mx-4 h-px bg-border/50" />

      <nav
        className={cn("flex-1 overflow-y-auto py-4", collapsed ? "px-2" : "px-3")}
        aria-label="Main navigation"
      >
        <div className={cn("space-y-0.5", collapsed && "flex flex-col items-center gap-0.5")}>
          <NavItem
            icon={<LayoutDashboard size={18} />}
            label="Dashboard"
            active={currentPage === 'dashboard'}
            onClick={() => onNavigate({ page: 'dashboard' })}
            collapsed={collapsed}
          />
          <NavItem
            icon={<Search size={18} />}
            label="Search"
            active={currentPage === 'search'}
            onClick={() => onNavigate({ page: 'search' })}
            collapsed={collapsed}
          />
          <NavItem
            icon={<FolderOpen size={18} />}
            label="Library"
            active={currentPage === 'library'}
            onClick={() => onNavigate({ page: 'library' })}
            collapsed={collapsed}
          />
          <NavItem
            icon={<FlaskConical size={18} />}
            label="Evaluation"
            active={currentPage === 'evaluation'}
            onClick={() => onNavigate({ page: 'evaluation' })}
            collapsed={collapsed}
          />
        </div>
      </nav>

      <div className="mt-auto">
        <div className="mx-4 h-px bg-border/50 mb-3" />
        {!collapsed ? (
          <div className="px-3 pb-4 space-y-3">
            <div className="flex items-center justify-between">
              <ThemeToggle showLabel />
              {onToggleCollapse && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onToggleCollapse}
                  aria-label="Collapse sidebar"
                  className="h-8 w-8 flex-shrink-0 text-muted-foreground"
                >
                  <ChevronLeft size={15} />
                </Button>
              )}
            </div>
            <RuntimeBadge runtime={runtime} error={runtimeError} />
          </div>
        ) : (
          <div className="pb-4 flex flex-col items-center gap-2">
            <ThemeToggle />
            {onToggleCollapse && (
              <Button
                variant="ghost"
                size="icon"
                onClick={onToggleCollapse}
                aria-label="Expand sidebar"
                className="h-8 w-8 text-muted-foreground"
              >
                <ChevronRight size={15} />
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
      <aside
        className={cn(
          "hidden md:flex flex-col shrink-0",
          "border-r border-border/60 bg-card/80 backdrop-blur-xl",
          "transition-all duration-300 ease-out-expo",
          collapsed ? "w-[68px]" : "w-[240px]"
        )}
      >
        <SidebarContent
          {...props}
          collapsed={collapsed}
          onToggleCollapse={() => setCollapsed(!collapsed)}
        />
      </aside>

      <div className="md:hidden">
        <Sheet>
          <SheetTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="fixed top-4 left-4 z-[40] bg-card/80 backdrop-blur-md shadow-sm border border-border/50"
              aria-label="Open navigation menu"
            >
              <Menu size={18} />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-[240px] p-0 bg-card border-border/60">
            <SidebarContent {...props} />
          </SheetContent>
        </Sheet>
      </div>
    </>
  )
}
