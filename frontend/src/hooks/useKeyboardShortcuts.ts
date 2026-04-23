import { useEffect, useCallback } from 'react'

/**
 * Check if the user is currently typing in an input field
 */
function isTypingInInput(): boolean {
  const activeElement = document.activeElement
  if (!activeElement) return false

  const tagName = activeElement.tagName.toLowerCase()
  const isContentEditable = activeElement.getAttribute('contenteditable') === 'true'
  
  return (
    tagName === 'input' ||
    tagName === 'textarea' ||
    tagName === 'select' ||
    isContentEditable
  )
}

export interface KeyboardShortcut {
  key: string
  description: string
  handler: () => void
  /** If true, shortcut will work even when typing in input fields */
  allowInInput?: boolean
}

interface UseKeyboardShortcutsOptions {
  shortcuts: KeyboardShortcut[]
  enabled?: boolean
}

/**
 * Hook to register global keyboard shortcuts
 * Automatically prevents shortcuts when user is typing in input fields
 */
export function useKeyboardShortcuts({ shortcuts, enabled = true }: UseKeyboardShortcutsOptions) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return

      // Find matching shortcut
      const shortcut = shortcuts.find((s) => s.key === event.key)
      if (!shortcut) return

      // Check if user is typing (unless shortcut explicitly allows it)
      if (!shortcut.allowInInput && isTypingInInput()) {
        return
      }

      // Prevent default behavior and execute handler
      event.preventDefault()
      shortcut.handler()
    },
    [shortcuts, enabled]
  )

  useEffect(() => {
    if (!enabled) return undefined

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [handleKeyDown, enabled])
}

/**
 * Common keyboard shortcuts for the application
 */
export const KEYBOARD_SHORTCUTS = {
  FOCUS_SEARCH: '/',
  OPEN_UPLOAD: 'u',
  SHOW_HELP: '?',
  ESCAPE: 'Escape',
  ARROW_UP: 'ArrowUp',
  ARROW_DOWN: 'ArrowDown',
  ENTER: 'Enter',
} as const
