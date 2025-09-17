import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

const isProtectedRoute = createRouteMatcher([
  '/app(.*)',
  '/account(.*)',
  '/pricing(.*)',
])

export default clerkMiddleware(async (auth, req) => {
  // Skip auth during build time
  if (process.env.NODE_ENV === 'production' && !process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.startsWith('pk_')) {
    return
  }
  
  if (isProtectedRoute(req)) {
    const session = await auth()
    if (!session.userId) {
      return Response.redirect(new URL('/sign-in', req.url))
    }
  }
})

export const config = {
  matcher: ['/((?!.*\\..*|_next).*)', '/', '/(api|trpc)(.*)'],
}
