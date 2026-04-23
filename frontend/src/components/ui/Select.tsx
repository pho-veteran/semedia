import { useState, useRef, useEffect, type ReactNode } from 'react'
import { ChevronDown, Check } from 'lucide-react'
import { cn } from '../../lib/utils'

interface SelectProps {
  value?: string
  onValueChange?: (value: string) => void
  placeholder?: string
  children: ReactNode
  className?: string
}

export function Select({ value, onValueChange, placeholder, children, className }: SelectProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [selectedValue, setSelectedValue] = useState(value || '')
  const selectRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (value !== undefined) {
      setSelectedValue(value)
    }
  }, [value])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  const handleValueChange = (newValue: string) => {
    setSelectedValue(newValue)
    onValueChange?.(newValue)
    setIsOpen(false)
  }

  // Find the selected item to display its label
  let selectedLabel = placeholder || 'Select...'
  if (selectedValue && children) {
    const childrenArray = Array.isArray(children) ? children : [children]
    for (const child of childrenArray) {
      if (child && typeof child === 'object' && 'props' in child) {
        const props = child.props as any
        if (props.value === selectedValue) {
          selectedLabel = props.children || props.value
          break
        }
      }
    }
  }

  return (
    <div ref={selectRef} className={cn("relative", className)}>
      <button
        type="button"
        role="combobox"
        aria-expanded={isOpen}
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
          "min-w-[140px]"
        )}
      >
        <span className="truncate">{selectedLabel}</span>
        <ChevronDown className={cn("h-4 w-4 opacity-50 transition-transform", isOpen && "rotate-180")} />
      </button>
      {isOpen && (
        <div className="absolute top-full z-50 mt-1 max-h-60 w-full overflow-auto rounded-md border bg-popover text-popover-foreground shadow-md animate-in fade-in-0 zoom-in-95">
          <div className="p-1">
            {Array.isArray(children) 
              ? children.map((child, index) => {
                  if (child && typeof child === 'object' && 'props' in child) {
                    const props = child.props as any
                    return (
                      <button
                        key={index}
                        type="button"
                        onClick={() => handleValueChange(props.value)}
                        className={cn(
                          "relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground",
                          selectedValue === props.value && "bg-accent text-accent-foreground"
                        )}
                      >
                        {selectedValue === props.value && (
                          <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
                            <Check className="h-4 w-4" />
                          </span>
                        )}
                        {props.children}
                      </button>
                    )
                  }
                  return null
                })
              : children && typeof children === 'object' && 'props' in children
                ? (() => {
                    const props = (children as any).props
                    return (
                      <button
                        type="button"
                        onClick={() => handleValueChange(props.value)}
                        className={cn(
                          "relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground",
                          selectedValue === props.value && "bg-accent text-accent-foreground"
                        )}
                      >
                        {selectedValue === props.value && (
                          <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
                            <Check className="h-4 w-4" />
                          </span>
                        )}
                        {props.children}
                      </button>
                    )
                  })()
                : null
            }
          </div>
        </div>
      )}
    </div>
  )
}

// Simple wrapper for creating select items
interface SimpleSelectItemProps {
  value: string
  children: ReactNode
}

export function SimpleSelectItem({ value, children }: SimpleSelectItemProps) {
  return <div data-value={value}>{children}</div>
}

// Legacy exports for compatibility
export const SelectTrigger = () => null
export const SelectValue = () => null
export const SelectContent = () => null
export const SelectItem = () => null