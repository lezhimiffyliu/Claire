import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

// LIFECYCLE DEBUG - only logs on FULL PAGE RELOAD (not on component remount)
console.log('[MAIN.JSX] Script loaded - FULL PAGE LOAD', {
  timestamp: Date.now(),
  url: window.location.href
})

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
