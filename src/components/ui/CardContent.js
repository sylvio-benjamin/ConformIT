import { cn } from '@/lib/utils'

export function CardContent({ className, ...props }) {
    return <div className={cn('p-4', className)} {...props} />
  }