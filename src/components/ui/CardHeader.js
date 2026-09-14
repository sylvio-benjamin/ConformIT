import { cn } from '@/lib/utils'

export function CardHeader({ className, ...props }) {
    return <div className={cn('p-4 border-b', className)} {...props} />
  }