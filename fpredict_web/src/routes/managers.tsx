import { createFileRoute } from '@tanstack/react-router'
import { ManagersPage } from '../components/ManagersPage'

export const Route = createFileRoute('/managers')({
  ssr: false,
  preload: false,
  component: ManagersPage,
})
