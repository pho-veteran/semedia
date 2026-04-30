import { cn } from '@/lib/utils'

interface LinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  to: string
  children: React.ReactNode
  className?: string
}

export function Link({ to, children, className, ...props }: LinkProps) {
  return (
    <a href={to} className={cn(className)} {...props}>
      {children}
    </a>
  )
}
