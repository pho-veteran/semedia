import { Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui'
import { useTheme } from '../contexts/ThemeContext'
import { cn } from '@/lib/utils'

interface ThemeToggleProps {
  showLabel?: boolean
  className?: string
}

export function ThemeToggle({ showLabel = false, className }: ThemeToggleProps) {
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'

  if (showLabel) {
    return (
      <Button
        variant="ghost"
        onClick={toggleTheme}
        aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
        className={cn(
          "w-full justify-start gap-3 px-3 py-2 h-auto",
          "text-muted-foreground hover:text-foreground",
          className
        )}
      >
        <span className="relative w-5 h-5 flex items-center justify-center">
          <Sun
            className={cn(
              "h-4 w-4 absolute transition-all duration-300 ease-spring",
              isDark ? "opacity-100 rotate-0 scale-100" : "opacity-0 rotate-90 scale-75"
            )}
          />
          <Moon
            className={cn(
              "h-4 w-4 absolute transition-all duration-300 ease-spring",
              !isDark ? "opacity-100 rotate-0 scale-100" : "opacity-0 -rotate-90 scale-75"
            )}
          />
        </span>
        <span className="text-sm">{isDark ? 'Light Mode' : 'Dark Mode'}</span>
      </Button>
    )
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      className={cn("text-muted-foreground hover:text-foreground", className)}
    >
      <span className="relative w-5 h-5 flex items-center justify-center">
        <Sun
          className={cn(
            "h-4 w-4 absolute transition-all duration-300 ease-spring",
            isDark ? "opacity-100 rotate-0 scale-100" : "opacity-0 rotate-90 scale-75"
          )}
        />
        <Moon
          className={cn(
            "h-4 w-4 absolute transition-all duration-300 ease-spring",
            !isDark ? "opacity-100 rotate-0 scale-100" : "opacity-0 -rotate-90 scale-75"
          )}
        />
      </span>
    </Button>
  )
}
