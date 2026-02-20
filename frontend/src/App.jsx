import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import AnalyzePage from './pages/AnalyzePage'
import RankPage from './pages/RankPage'
import ResumesPage from './pages/ResumesPage'

export default function App() {
    return (
        <div>
            <nav className="navbar">
                <div className="navbar-inner">
                    <div className="navbar-brand">
                        <div className="logo-icon">🧠</div>
                        <span>ResumeAI</span>
                    </div>
                    <div className="navbar-links">
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
