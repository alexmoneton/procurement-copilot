import { NextRequest, NextResponse } from 'next/server'

// Temporarily disable Clerk middleware to avoid runtime errors
// Will re-enable when proper Clerk keys are configured
export default function middleware(req: NextRequest) {
  // For now, just pass through all requests without authentication
  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!.*\\..*|_next).*)', '/', '/(api|trpc)(.*)'],
}
