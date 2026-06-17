import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ErrorBoundary } from './components/ErrorBoundary.jsx'
import './styles/global.css'
import App from './App.jsx'

const rootEl = document.getElementById('root')
if (!rootEl) {
  throw new Error('#root not found')
}

createRoot(rootEl).render(
  <StrictMode>
    <ErrorBoundary>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ErrorBoundary>
  </StrictMode>,
)