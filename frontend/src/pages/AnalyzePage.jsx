import { useState, useRef } from 'react'
import { uploadResume, createJob, analyzeResume, getAnalysisStatus } from '../api/client'
import ScoreDetail from '../components/ScoreDetail'

export default function AnalyzePage() {
    const [files, setFiles] = useState([])
    const [jdTitle, setJdTitle] = useState('')
    const [jdText, setJdText] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [result, setResult] = useState(null)
    const [dragOver, setDragOver] = useState(false)
    const fileInputRef = useRef()

    const handleFiles = (newFiles) => {
        const valid = Array.from(newFiles).filter(f =>
            f.type === 'application/pdf' ||
            f.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        if (valid.length !== newFiles.length) {
            setError('Only PDF and DOCX files are accepted.')
        }
        setFiles(prev => [...prev, ...valid].slice(0, 1)) // single resume for analyze
    }

    const handleDrop = (e) => {
        e.preventDefault()
        setDragOver(false)
        handleFiles(e.dataTransfer.files)
    }

    const removeFile = (i) => setFiles(f => f.filter((_, idx) => idx !== i))

    const formatSize = (bytes) => {
        if (bytes < 1024) return `${bytes} B`
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    }

    const handleAnalyze = async () => {
        if (!files.length) { setError('Please upload a resume.'); return }
        if (!jdText.trim()) { setError('Please enter a job description.'); return }
        if (jdText.trim().length < 10) { setError('Job description is too short.'); return }

        setLoading(true)
        setError(null)
        setResult(null)

        try {
            const uploaded = await uploadResume(files[0])
            if (uploaded.extraction_status === 'error') {
                setError(`Text extraction failed: ${uploaded.extraction_error}`)
                setLoading(false)
                return
            }

            const job = await createJob(jdTitle || null, jdText)

            // Start analysis (returns 202)
            const initialAnalysis = await analyzeResume(uploaded.id, job.id)

            // Polling
            let pollCount = 0
            const maxPolls = 30 // 30 * 2s = 60s

            const poll = setInterval(async () => {
                try {
                    const analysis = await getAnalysisStatus(initialAnalysis.id)
                    pollCount++

                    if (analysis.status === 'done') {
                        clearInterval(poll)
                        setResult({ analysis, resume: uploaded, job })
                        setLoading(false)
                    } else if (analysis.status === 'failed') {
                        clearInterval(poll)
                        setError(`Analysis failed: ${analysis.error_message || 'Unknown error'}`)
                        setLoading(false)
                    } else if (pollCount >= maxPolls) {
                        clearInterval(poll)
                        setError('Analysis timed out. Please try again.')
                        setLoading(false)
                    }
                } catch (err) {
                    clearInterval(poll)
                    setError('Error polling analysis status.')
                    setLoading(false)
                }
            }, 2000)

        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Analysis failed.')
            setLoading(false)
        }

    }

    return (
        <div>
            <div className="hero">
                <div className="hero-badge">✨ AI-Powered</div>
                <h1>Analyze Your Resume</h1>
                <p>Upload a resume and paste a job description to get an instant match score, skill gap analysis, and actionable suggestions.</p>
            </div>

            <div className="container" style={{ paddingBottom: 60 }}>
                <div className="grid-2">
                    {/* Left: Upload + JD */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                        <div className="card">
                            <div className="card-title"><span className="icon">📄</span> Resume</div>
                            <div
                                className={`drop-zone${dragOver ? ' drag-over' : ''}`}
                                onClick={() => fileInputRef.current?.click()}
                                onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                                onDragLeave={() => setDragOver(false)}
                                onDrop={handleDrop}
                            >
                                <div className="drop-zone-icon">📁</div>
                                <div className="drop-zone-text">Drop your resume here or <strong>click to browse</strong></div>
                                <div className="drop-zone-hint">PDF or DOCX · Max 10MB</div>
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                    style={{ display: 'none' }}
                                    onChange={e => handleFiles(e.target.files)}
                                />
                            </div>
                            {files.length > 0 && (
                                <div className="file-list">
                                    {files.map((f, i) => (
                                        <div key={i} className="file-item">
                                            <span>📎</span>
                                            <span className="file-item-name">{f.name}</span>
                                            <span className="file-item-size">{formatSize(f.size)}</span>
                                            <button className="file-item-remove" onClick={() => removeFile(i)}>✕</button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        <div className="card">
                            <div className="card-title"><span className="icon">💼</span> Job Description</div>
                            <div className="form-group">
                                <label className="form-label">Job Title (optional)</label>
                                <input
                                    className="form-input"
                                    placeholder="e.g. Senior Python Engineer"
                                    value={jdTitle}
                                    onChange={e => setJdTitle(e.target.value)}
                                />
                            </div>
                            <div className="form-group" style={{ marginBottom: 0 }}>
                                <label className="form-label">Job Description *</label>
                                <textarea
                                    className="form-textarea"
                                    placeholder="Paste the full job description here..."
                                    value={jdText}
                                    onChange={e => setJdText(e.target.value)}
                                    style={{ minHeight: 180 }}
                                />
                            </div>
                        </div>

                        {error && <div className="alert alert-error">⚠️ {error}</div>}

                        <button
                            className="btn btn-primary btn-lg btn-full"
                            onClick={handleAnalyze}
                            disabled={loading}
                            id="analyze-btn"
                        >
                            {loading ? <><span className="spinner" /> Analyzing...</> : '🔍 Analyze Resume'}
                        </button>
                    </div>

                    {/* Right: Results */}
                    <div>
                        {loading && (
                            <div className="loading-overlay">
                                <div className="loading-spinner-lg" />
                                <p>Running AI analysis...</p>
                                <p className="text-sm text-muted">Generating embeddings and extracting skills</p>
                            </div>
                        )}
                        {result && !loading && (
                            <ScoreDetail analysis={result.analysis} filename={result.resume.original_filename} />
                        )}
                        {!result && !loading && (
                            <div className="empty-state">
                                <div className="empty-state-icon">🎯</div>
                                <h3>Results will appear here</h3>
                                <p>Upload a resume and enter a job description to get started.</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
