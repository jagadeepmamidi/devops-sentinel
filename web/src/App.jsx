import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Landing from './pages/Landing'
import About from './pages/About'
import Docs from './pages/Docs'
import Terms from './pages/Terms'
import Privacy from './pages/Privacy'
import Feedback from './pages/Feedback'
import CliAuth from './pages/CliAuth'
import OperatorServices from './pages/OperatorServices'
import OperatorIncidents from './pages/OperatorIncidents'
import OperatorIncidentDetail from './pages/OperatorIncidentDetail'
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
        <Route path="/operator/services" element={<OperatorServices />} />
        <Route path="/operator/incidents" element={<OperatorIncidents />} />
        <Route path="/operator/incidents/:incidentId" element={<OperatorIncidentDetail />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
