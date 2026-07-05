import { createRouter as createTanStackRouter } from '@tanstack/react-router'
import { routeTree } from './routeTree.gen'

function DefaultNotFound() {
  return (
    <div className="container page-stack">
      <div className="empty-state">
        <div className="empty-icon">404</div>
        <h1 className="heading-secondary">Page not found</h1>
        <p className="card-caption">The page you requested could not be matched.</p>
      </div>
    </div>
  )
}

export function getRouter() {
  const router = createTanStackRouter({
    routeTree,
    scrollRestoration: true,
    defaultPreload: 'intent',
    defaultPreloadStaleTime: 0,
    defaultNotFoundComponent: DefaultNotFound,
  })

  return router
}

declare module '@tanstack/react-router' {
  interface Register {
    router: ReturnType<typeof getRouter>
  }
}
