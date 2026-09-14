import { NextResponse } from 'next/server'

/**
 * La protection réelle est la session FastAPI (cookie httpOnly).
 * Ce middleware ne fait plus confiance à un cookie `role` client.
 */
export function middleware() {
  return NextResponse.next()
}

export const config = {
  matcher: ['/admin/:path*', '/employe/:path*', '/grc/:path*'],
}
