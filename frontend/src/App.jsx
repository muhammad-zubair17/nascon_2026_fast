import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Onboarding from './pages/Onboarding'
import Paper from './pages/Paper'
import Archive from './pages/Archive'
import { getUid } from './api'

function Home() {
  return getUid() ? <Paper /> : <Navigate to="/welcome" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/welcome" element={<Onboarding />} />
        <Route path="/edition/:id" element={<Paper />} />
        <Route path="/archive" element={<Archive />} />
      </Routes>
    </BrowserRouter>
  )
}