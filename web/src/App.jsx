import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Landing from './pages/Landing'
import About from './pages/About'
import Docs from './pages/Docs'
import Terms from './pages/Terms'
import Privacy from './pages/Privacy'
import Feedback from './pages/Feedback'
import CliAuth from './pages/CliAuth'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/about" element={<About />} />
        <Route path="/docs" element={<Docs />} />
        <Route path="/terms" element={<Terms />} />
        <Route path="/privacy" element={<Privacy />} />
        <Route path="/feedback" element={<Feedback />} />
        <Route path="/cli-auth" element={<CliAuth />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
