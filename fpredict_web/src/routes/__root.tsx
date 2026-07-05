import { HeadContent, Scripts, createRootRoute } from '@tanstack/react-router'
import { Outlet } from '@tanstack/react-router'
import appCss from '../styles.css?url'

export const Route = createRootRoute({
  head: () => ({
    meta: [
      { charSet: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      { title: 'FPredict | Quantitative Sports-Trading Platform' },
      { name: 'description', content: 'Autonomous, self-adjusting predictive engine for the English Premier League.' }
    ],
    links: [
      { rel: 'stylesheet', href: appCss },
    ],
  }),
  component: RootDocument,
})

function RootDocument() {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        <Outlet />
        <Scripts />
      </body>
    </html>
  )
}
