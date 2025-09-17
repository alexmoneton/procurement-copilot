import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

const isProtectedRoute = createRouteMatcher([
  '/app(.*)',
  '/account(.*)',
  '/pricing(.*)',
])

export default clerkMiddleware(async (auth, req) => {
  // Skip auth when Clerk is not properly configured
  if (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.startsWith('pk_')) {
    return
  }
  
  if (isProtectedRoute(req)) {
    try {
      const session = await auth()
      if (!session.userId) {
        return Response.redirect(new URL('/sign-in', req.url))
      }
    } catch (error) {
      // If auth fails, just continue without protection
      console.warn('Auth failed:', error)
      return
    }
  }
})

export const config = {
  matcher: ['/((?!.*\\..*|_next).*)', '/', '/(api|trpc)(.*)'],
}
