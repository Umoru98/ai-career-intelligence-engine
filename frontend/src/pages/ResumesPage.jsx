import { useState, useEffect } from 'react'
import { listResumes } from '../api/client'

export default function ResumesPage() {
    const [resumes, setResumes] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [infoMsg, setInfoMsg] = useState(null)

    useEffect(() => {
        listResumes()
            .then(data => {
                if (data && data.items) {
                    setResumes(data.items)
                } else {
                    setResumes([])
                }
                setError(null)
                setInfoMsg(null)
            })
            .catch(err => {
                const status = err.response?.status
                const isTimeout = err.message === 'Network Error' || err.code === 'ECONNABORTED' || [502, 504].includes(status)

                if (status === 404) {
                    setResumes([])
                } else if (isTimeout) {
                    setInfoMsg("The AI engine is waking up from sleep. This might take a minute...")
                } else {
                    setError(err.message)
                }
            })
            .finally(() => setLoading(false))
    }, [])

    const formatSize = (bytes) => {
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    }

    const formatDate = (iso) => new Date(iso).toLocaleDateString('en-US', {
        year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    })

    return (
        <div>
            <div className="hero" style={{ paddingBottom: 40 }}>
                <div className="hero-badge">📚 Library</div>
                <h1>Resume Library</h1>
                <p>All uploaded resumes stored in the system.</p>
            </div>

            <div className="container" style={{ paddingBottom: 60 }}>
                {loading && (
                    <div className="loading-overlay">
                        <div className="loading-spinner-lg" />
                        <p>Loading resumes...</p>
                    </div>
                )}

                {error && <div className="alert alert-error">⚠️ {error}</div>}
                {infoMsg && <div className="alert alert-info">✨ {infoMsg}</div>}

                {!loading && resumes.length === 0 && !error && !infoMsg && (
                    <div className="empty-state">
                        <div className="empty-state-icon">📂</div>
                        <h3>No resumes yet</h3>
                        <p>Upload resumes from the Analyze or Rank pages.</p>
                    </div>
                )}

                {!loading && resumes.length > 0 && (
                    <div className="card">
                        <div className="card-title"><span className="icon">📄</span> {resumes.length} Resume(s)</div>
                        <table className="rank-table">
                            <thead>
                                <tr>
                                    <th>Filename</th>
                                    <th>Type</th>
                                    <th>Size</th>
                                    <th>Uploaded</th>
                                </tr>
                            </thead>
                            <tbody>
                                {resumes.map(r => (
                                    <tr key={r.id}>
                                        <td style={{ fontWeight: 600 }}>{r.original_filename}</td>
                                        <td>
                                            <span className="skill-tag neutral">
                                                {r.content_type.includes('pdf') ? 'PDF' : 'DOCX'}
                                            </span>
                                        </td>
                                        <td className="text-muted text-sm">{formatSize(r.size_bytes)}</td>
                                        <td className="text-muted text-sm">{formatDate(r.created_at)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    )
}
