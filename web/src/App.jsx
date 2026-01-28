import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Landing from './pages/Landing'
import Auth from './pages/Auth'
import Dashboard from './pages/Dashboard'
import Projects from './pages/Projects'
import Incidents from './pages/Incidents'
import Postmortems from './pages/Postmortems'
import Docs from './pages/Docs'
import About from './pages/About'
import Terms from './pages/Terms'
import Privacy from './pages/Privacy'
import Feedback from './pages/Feedback'
import './App.css'

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
      </div>
    )
  }

  return user ? children : <Navigate to="/auth" />
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/auth" element={<Auth />} />
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="/projects" element={
            <ProtectedRoute>
              <Projects />
            </ProtectedRoute>
          } />
          <Route path="/incidents" element={
            <ProtectedRoute>
              <Incidents />
            </ProtectedRoute>
          } />
          <Route path="/postmortems" element={
            <ProtectedRoute>
              <Postmortems />
            </ProtectedRoute>
          } />
          <Route path="/docs" element={<Docs />} />
          <Route path="/about" element={<About />} />
          <Route path="/terms" element={<Terms />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="/feedback" element={<Feedback />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
