import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import AnalyzePage from './pages/AnalyzePage'
import RankPage from './pages/RankPage'
import ResumesPage from './pages/ResumesPage'

export default function App() {
    const [isMenuOpen, setIsMenuOpen] = useState(false)
    const location = useLocation()

    useEffect(() => {
        let sessionId = localStorage.getItem('session_id')
        if (!sessionId) {
            sessionId = crypto.randomUUID()
            localStorage.setItem('session_id', sessionId)
        }
    }, [])

    // Close menu when route changes
    useEffect(() => {
        setIsMenuOpen(false)
    }, [location])

    return (
        <div className={isMenuOpen ? 'menu-open' : ''}>
            <nav className="navbar">
                <div className="navbar-inner">
                    <div className="navbar-brand">
                        <div className="logo-icon">🧠</div>
                        <span>ResumeAI</span>
                    </div>

                    <button
                        className="mobile-menu-toggle"
                        onClick={() => setIsMenuOpen(!isMenuOpen)}
                        aria-label="Toggle menu"
                    >
                        {isMenuOpen ? '✕' : '☰'}
                    </button>

                    <div className={`navbar-links ${isMenuOpen ? 'show' : ''}`}>
                        <NavLink to="/" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`} end>
                            Analyze
                        </NavLink>
                        <NavLink to="/rank" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
                            Rank & Compare
                        </NavLink>
                        <NavLink to="/resumes" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
                            Resumes
                        </NavLink>
                    </div>
                </div>
            </nav>

            <main>
                <Routes>
                    <Route path="/" element={<AnalyzePage />} />
                    <Route path="/rank" element={<RankPage />} />
                    <Route path="/resumes" element={<ResumesPage />} />
                </Routes>
            </main>
        </div>
    )
}
