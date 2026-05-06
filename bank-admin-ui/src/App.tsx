import { BrowserRouter } from 'react-router-dom'
import { AppRouter } from './router'
import { Toaster } from './components/ui/toaster'

export default function App() {
  return (
    <BrowserRouter>
      <AppRouter />
      <Toaster />
    </BrowserRouter>
  )
}
