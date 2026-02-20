import { useState, useRef } from 'react'
import { uploadResume, createJob, rankResumes } from '../api/client'
import ScoreDetail from '../components/ScoreDetail'

export default function RankPage() {
    const [files, setFiles] = useState([])
    const [uploadedResumes, setUploadedResumes] = useState([])
    const [jdTitle, setJdTitle] = useState('')
    const [jdText, setJdText] = useState('')
    const [loading, setLoading] = useState(false)
    const [uploading, setUploading] = useState(false)
    const [error, setError] = useState(null)
    const [rankResult, setRankResult] = useState(null)
    const [selectedAnalysis, setSelectedAnalysis] = useState(null)
    const [dragOver, setDragOver] = useState(false)
    const fileInputRef = useRef()

    const handleFiles = (newFiles) => {
        const valid = Array.from(newFiles).filter(f =>
            f.type === 'application/pdf' ||
            f.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        setFiles(prev => [...prev, ...valid])
    }

    const handleDrop = (e) => {
        e.preventDefault()
        setDragOver(false)
        handleFiles(e.dataTransfer.files)
    }

    const removeFile = (i) => setFiles(f => f.filter((_, idx) => idx !== i))

    const formatSize = (bytes) => {
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    }

    const handleUploadAll = async () => {
        if (!files.length) { setError('Please add resume files.'); return }
        setUploading(true)
        setError(null)
        const results = []
        for (const file of files) {
            try {
                const r = await uploadResume(file)
                results.push({ ...r, localName: file.name })
            } catch (err) {
                setError(`Failed to upload ${file.name}: ${err.response?.data?.detail || err.message}`)
            }
        }
        setUploadedResumes(prev => [...prev, ...results])
        setFiles([])
        setUploading(false)
    }

    const handleRank = async () => {
        if (uploadedResumes.length < 1) { setError('Upload at least 1 resume.'); return }
        if (!jdText.trim()) { setError('Please enter a job description.'); return }

        setLoading(true)
        setError(null)
        setRankResult(null)
        setSelectedAnalysis(null)

        try {
            const job = await createJob(jdTitle || null, jdText)
            const result = await rankResumes(job.id, uploadedResumes.map(r => r.id))
            setRankResult(result)
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Ranking failed.')
        } finally {
            setLoading(false)
        }
    }

    const getRankClass = (i) => {
        if (i === 0) return 'gold'
        if (i === 1) return 'silver'
        if (i === 2) return 'bronze'
        return ''
    }

    const getScoreClass = (score) => {
        if (score >= 75) return 'high'
        if (score >= 50) return 'mid'
        return 'low'
    }

    return (
        <div>
            <div className="hero" style={{ paddingBottom: 40 }}>
                <div className="hero-badge">📊 Batch Analysis</div>
                <h1>Rank & Compare Resumes</h1>
                <p>Upload multiple resumes and rank them against a job description to find the best candidates.</p>
            </div>

            <div className="container" style={{ paddingBottom: 60 }}>
                <div className="grid-2">
                    {/* Left: Setup */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                        <div className="card">
                            <div className="card-title"><span className="icon">📄</span> Upload Resumes</div>
                            <div
                                className={`drop-zone${dragOver ? ' drag-over' : ''}`}
                                onClick={() => fileInputRef.current?.click()}
                                onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                                onDragLeave={() => setDragOver(false)}
                                onDrop={handleDrop}
                            >
                                <div className="drop-zone-icon">📁</div>
                                <div className="drop-zone-text">Drop multiple resumes or <strong>click to browse</strong></div>
                                <div className="drop-zone-hint">PDF or DOCX · Max 10MB each</div>
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept=".pdf,.docx"
                                    multiple
                                    style={{ display: 'none' }}
                                    onChange={e => handleFiles(e.target.files)}
                                />
                            </div>

                            {files.length > 0 && (
                                <>
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
                                    <button
                                        className="btn btn-secondary btn-full mt-4"
                                        onClick={handleUploadAll}
                                        disabled={uploading}
                                        id="upload-all-btn"
                                    >
                                        {uploading ? <><span className="spinner" /> Uploading...</> : `⬆️ Upload ${files.length} file(s)`}
                                    </button>
                                </>
                            )}

                            {uploadedResumes.length > 0 && (
                                <div style={{ marginTop: 12 }}>
                                    <div className="form-label">Uploaded ({uploadedResumes.length})</div>
                                    <div className="file-list">
                                        {uploadedResumes.map((r, i) => (
                                            <div key={r.id} className="file-item">
                                                <span style={{ color: 'var(--success)' }}>✓</span>
                                                <span className="file-item-name">{r.original_filename}</span>
                                                <button
                                                    className="file-item-remove"
                                                    onClick={() => setUploadedResumes(prev => prev.filter((_, idx) => idx !== i))}
                                                >✕</button>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="card">
                            <div className="card-title"><span className="icon">💼</span> Job Description</div>
                            <div className="form-group">
                                <label className="form-label">Job Title (optional)</label>
                                <input className="form-input" placeholder="e.g. Backend Engineer" value={jdTitle} onChange={e => setJdTitle(e.target.value)} />
                            </div>
                            <div className="form-group" style={{ marginBottom: 0 }}>
                                <label className="form-label">Job Description *</label>
                                <textarea className="form-textarea" placeholder="Paste the full job description..." value={jdText} onChange={e => setJdText(e.target.value)} />
                            </div>
                        </div>

                        {error && <div className="alert alert-error">⚠️ {error}</div>}

                        <button
                            className="btn btn-primary btn-lg btn-full"
                            onClick={handleRank}
                            disabled={loading || uploadedResumes.length === 0}
                            id="rank-btn"
                        >
                            {loading ? <><span className="spinner" /> Ranking...</> : '🏆 Rank Resumes'}
                        </button>
                    </div>

                    {/* Right: Results */}
                    <div>
                        {loading && (
                            <div className="loading-overlay">
                                <div className="loading-spinner-lg" />
                                <p>Ranking {uploadedResumes.length} resumes...</p>
                                <p className="text-sm text-muted">This may take a moment for large batches</p>
                            </div>
                        )}

                        {rankResult && !loading && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                                <div className="card">
                                    <div className="card-title"><span className="icon">🏆</span> Rankings</div>
                                    <table className="rank-table">
                                        <thead>
                                            <tr>
                                                <th>#</th>
                                                <th>Resume</th>
                                                <th>Score</th>
                                                <th>Matches</th>
                                                <th>Missing</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {rankResult.ranked.map((item, i) => (
                                                <tr key={item.resume_id} onClick={() => setSelectedAnalysis(item)}>
                                                    <td><div className={`rank-num ${getRankClass(i)}`}>{i + 1}</div></td>
                                                    <td>
                                                        <div style={{ fontWeight: 600, fontSize: '0.9rem', maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                            {item.original_filename}
                                                        </div>
                                                    </td>
                                                    <td>
                                                        <span style={{
                                                            fontWeight: 800,
                                                            color: item.match_score_percent >= 75 ? 'var(--success)' :
                                                                item.match_score_percent >= 50 ? 'var(--warning)' : 'var(--danger)'
                                                        }}>
                                                            {item.match_score_percent.toFixed(1)}%
                                                        </span>
                                                    </td>
                                                    <td><span className="skill-tag match">{item.matching_skills.length}</span></td>
                                                    <td><span className="skill-tag missing">{item.missing_skills_count}</span></td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>

                                {selectedAnalysis && (
                                    <div className="card">
                                        <div className="card-title"><span className="icon">📋</span> {selectedAnalysis.original_filename}</div>
                                        <div style={{ marginBottom: 12 }}>
                                            <div className="detail-section-title">Match Score</div>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                                <span style={{
                                                    fontSize: '1.8rem',
                                                    fontWeight: 800,
                                                    color: selectedAnalysis.match_score_percent >= 75 ? 'var(--success)' :
                                                        selectedAnalysis.match_score_percent >= 50 ? 'var(--warning)' : 'var(--danger)'
                                                }}>
                                                    {selectedAnalysis.match_score_percent.toFixed(1)}%
                                                </span>
                                                <div style={{ flex: 1 }}>
                                                    <div className="score-bar-wrap">
                                                        <div
                                                            className={`score-bar ${getScoreClass(selectedAnalysis.match_score_percent)}`}
                                                            style={{ width: `${selectedAnalysis.match_score_percent}%` }}
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div style={{ marginBottom: 12 }}>
                                            <div className="detail-section-title">Matching Skills</div>
                                            <div className="skill-tags">
                                                {selectedAnalysis.matching_skills.slice(0, 10).map(s => (
                                                    <span key={s} className="skill-tag match">{s}</span>
                                                ))}
                                                {selectedAnalysis.matching_skills.length === 0 && <span className="text-muted text-sm">None found</span>}
                                            </div>
                                        </div>
                                        <div>
                                            <div className="detail-section-title">Explanation</div>
                                            <div className="explanation-box">{selectedAnalysis.explanation}</div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {!rankResult && !loading && (
                            <div className="empty-state">
                                <div className="empty-state-icon">📊</div>
                                <h3>Rankings will appear here</h3>
                                <p>Upload resumes and enter a job description, then click Rank.</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
