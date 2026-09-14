import React from 'react';
import { cn } from '@/lib/utils';

export function CardFooter({ className, ...props }) {
    return <div className={cn('p-4 border-t text-sm text-muted-foreground', className)} {...props} />
  }
  