import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from './ui/Dialog'
import { Badge } from './ui/Badge'

interface ShortcutsHelpDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

interface ShortcutItem {
  key: string
  description: string
  category: 'Navigation' | 'Search' | 'General'
}

const shortcuts: ShortcutItem[] = [
  { key: '/', description: 'Focus search input', category: 'Search' },
  { key: 'u', description: 'Open upload dialog', category: 'General' },
  { key: '?', description: 'Show keyboard shortcuts', category: 'General' },
  { key: 'Esc', description: 'Close modals and dialogs', category: 'General' },
  { key: '↑ / ↓', description: 'Navigate search results', category: 'Search' },
  { key: 'Enter', description: 'Open focused result', category: 'Search' },
]

const categories = ['Navigation', 'Search', 'General'] as const

export function ShortcutsHelpDialog({ open, onOpenChange }: ShortcutsHelpDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Keyboard Shortcuts</DialogTitle>
          <DialogDescription>
            Use these keyboard shortcuts to navigate the application more efficiently
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {categories.map((category) => {
            const categoryShortcuts = shortcuts.filter((s) => s.category === category)
            if (categoryShortcuts.length === 0) return null

            return (
              <div key={category}>
                <h3 className="text-sm font-semibold text-foreground mb-3">{category}</h3>
                <div className="space-y-2">
                  {categoryShortcuts.map((shortcut) => (
                    <div
                      key={shortcut.key}
                      className="flex items-center justify-between py-2 px-3 rounded-md hover:bg-accent/50 transition-colors"
                    >
                      <span className="text-sm text-muted-foreground">{shortcut.description}</span>
                      <Badge variant="outline" className="font-mono text-xs">
                        {shortcut.key}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>

        <div className="mt-6 pt-4 border-t border-border">
          <p className="text-xs text-muted-foreground">
            Note: Shortcuts are disabled when typing in input fields
          </p>
        </div>
      </DialogContent>
    </Dialog>
  )
}
