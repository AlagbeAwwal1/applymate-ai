import React from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
import './index.css'
import App from './App'
import Dashboard from './pages/Dashboard'
import AddJob from './pages/AddJob'
import JobDetail from './pages/JobDetail'
import Applications from './pages/Applications'
import Settings from './pages/Settings'
import Login from './pages/Login'
import Register from './pages/Register'
import { isAuthed } from './lib/auth'

const RequireAuth = ({children}) => isAuthed() ? children : <Navigate to="/login" replace />

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { path: 'login', element: <Login /> },
      { path: 'register', element: <Register /> },

      { index: true, element: <RequireAuth><Dashboard /></RequireAuth> },
      { path: 'add', element: <RequireAuth><AddJob /></RequireAuth> },
      { path: 'jobs/:id', element: <RequireAuth><JobDetail /></RequireAuth> },
      { path: 'applications', element: <RequireAuth><Applications /></RequireAuth> },
      { path: 'settings', element: <RequireAuth><Settings /></RequireAuth> },
    ]
  }
])

createRoot(document.getElementById('root')).render(<RouterProvider router={router} />)
