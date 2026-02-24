import { useState, useRef, useEffect } from 'react'
import { uploadResume, createJob, analyzeResume, getAnalysisStatus } from '../api/client'
import ScoreDetail from '../components/ScoreDetail'

export default function AnalyzePage() {
    const [files, setFiles] = useState([])
    const [jdTitle, setJdTitle] = useState('')
    const [jdText, setJdText] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [infoMsg, setInfoMsg] = useState(null)
    const [result, setResult] = useState(null)
    const [dragOver, setDragOver] = useState(false)
    const fileInputRef = useRef()
    const resultsRef = useRef(null)

    const statusMap = {
        'STARTING': "Waking up the AI engine...",
        'EXTRACTING_TEXT': "Extracting your skills & experience...",
        'COMPUTING_EMBEDDINGS': "Running semantic matching against the job description...",
    }
    const [status, setStatus] = useState('')

    useEffect(() => {
        if (loading) {
            setTimeout(() => {
                resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
            }, 100)
        }
    }, [loading])

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

    const [secondsElapsed, setSecondsElapsed] = useState(0)

    const handleAnalyze = async () => {
        if (!files.length) { setError('Please upload a resume.'); return }
        if (!jdText.trim()) { setError('Please enter a job description.'); return }
        if (jdText.trim().length < 10) { setError('Job description is too short.'); return }

        setLoading(true)
        setError(null)
        setInfoMsg(null)
        setResult(null)
        setSecondsElapsed(0)

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

            const loadingMessages = [
                "Brewing some digital coffee for the AI...",
                "Reading between the lines of your experience...",
                "Translating HR-speak into Machine Learning vectors...",
                "Cross-referencing your skills with industry standards...",
                "Quantifying your impact and identifying skill gaps...",
                "Aligning your profile with the target job description...",
                "Polishing up the final semantic insights..."
            ]

            setStatus(loadingMessages[0])
            let messageIdx = 0

            const messageInterval = setInterval(() => {
                messageIdx = (messageIdx + 1) % loadingMessages.length
                setStatus(loadingMessages[messageIdx])
                setSecondsElapsed(prev => prev + 4)
            }, 4000)

            const pollStatus = async () => {
                try {
                    const analysis = await getAnalysisStatus(initialAnalysis.id)

                    if (analysis.status === 'COMPLETED' || analysis.status === 'done') {
                        clearInterval(messageInterval)
                        setResult({ analysis, resume: uploaded, job })
                        setLoading(false)
                        return
                    } else if (analysis.status === 'failed') {
                        clearInterval(messageInterval)
                        setError(`Analysis failed: ${analysis.error_message || 'Unknown error'}`)
                        setLoading(false)
                        return
                    }

                    setTimeout(pollStatus, 2000)

                } catch (err) {
                    // Exponential backoff or simple retry
                    setTimeout(pollStatus, 4000)
                }
            }

            // Start polling loop
            setTimeout(pollStatus, 2000)

        } catch (err) {
            const isTimeout = err.message === 'Network Error' || err.code === 'ECONNABORTED' || [502, 504].includes(err.response?.status)
            if (isTimeout) {
                setError("The AI engine was deep in sleep mode to save energy. We've just nudged it awake! Please click 'Analyze' again to continue.")
            } else {
                setError(err.response?.data?.detail || err.message || 'Analysis failed.')
            }
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
                                <input
                                    className="form-input"
                                    style={{ display: 'none' }} // spacer
                                />
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
                        {infoMsg && <div className="alert alert-info">✨ {infoMsg}</div>}

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
                    <div ref={resultsRef}>
                        {loading && (
                            <div className="loading-overlay" style={{ minHeight: '300px' }}>
                                <div className="loading-spinner-lg" />
                                <p style={{ fontWeight: '500', fontSize: '1.1rem', marginTop: '20px', textAlign: 'center' }}>
                                    {status}
                                </p>
                                <p className="text-sm text-muted" style={{ maxWidth: 400, textAlign: 'center', marginTop: 12 }}>
                                    Great resumes take a moment to analyze. We're making sure we don't miss any of your skills!
                                </p>
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
