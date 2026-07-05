import { defineConfig, type PluginOption } from 'vite'
import { devtools } from '@tanstack/devtools-vite'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import viteReact from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const lifecycle = process.env.npm_lifecycle_event ?? ''
const useCloudflare = ['build', 'preview', 'deploy'].includes(lifecycle)

export default defineConfig(async () => {
  const plugins: PluginOption[] = [devtools(), tailwindcss(), tanstackStart(), viteReact()]

  if (useCloudflare) {
    const { cloudflare } = await import('@cloudflare/vite-plugin')
    plugins.push(
      cloudflare({
        viteEnvironment: {
          name: 'ssr',
        },
      }),
    )
  }

  return {
    resolve: {
      tsconfigPaths: true,
      dedupe: ['react', 'react-dom'],
    },
    ssr: {
      noExternal: ['recharts'],
    },
    plugins,
  }
})
