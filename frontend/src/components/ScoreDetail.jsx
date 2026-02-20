export default function ScoreDetail({ analysis, filename }) {
    const score = analysis.match_score_percent

    const scoreClass = score >= 75 ? 'high' : score >= 50 ? 'mid' : 'low'
    const scoreColor = score >= 75 ? 'var(--success)' : score >= 50 ? 'var(--warning)' : 'var(--danger)'

    return (
        <div className="detail-panel">
            <div className="detail-header">
                <div className={`score-badge score-${scoreClass}`}>
                    {score.toFixed(0)}%
                </div>
                <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 700, fontSize: '1rem', marginBottom: 4 }}>{filename}</div>
                    <div style={{ marginBottom: 8 }}>
                        <div className="score-bar-wrap">
                            <div className={`score-bar ${scoreClass}`} style={{ width: `${score}%` }} />
                        </div>
                    </div>
                    <div className="text-sm text-muted">
                        {score >= 75 ? '🟢 Strong match' : score >= 50 ? '🟡 Moderate match' : '🔴 Weak match'}
                    </div>
                </div>
            </div>

            <div className="detail-body">
                {/* Matching Skills */}
                <div>
                    <div className="detail-section-title">✅ Matching Skills ({analysis.matching_skills.length})</div>
                    <div className="skill-tags">
                        {analysis.matching_skills.length > 0
                            ? analysis.matching_skills.map(s => <span key={s} className="skill-tag match">{s}</span>)
                            : <span className="text-muted text-sm">No matching skills found in taxonomy</span>
                        }
                    </div>
                </div>

                {/* Missing Skills */}
                <div>
                    <div className="detail-section-title">❌ Missing Skills ({analysis.missing_skills.length})</div>
                    <div className="skill-tags">
                        {analysis.missing_skills.length > 0
                            ? analysis.missing_skills.slice(0, 15).map(s => <span key={s} className="skill-tag missing">{s}</span>)
                            : <span className="text-muted text-sm">No missing skills — great coverage!</span>
                        }
                        {analysis.missing_skills.length > 15 && (
                            <span className="skill-tag neutral">+{analysis.missing_skills.length - 15} more</span>
                        )}
                    </div>
                </div>

                {/* Sections */}
                {Object.keys(analysis.section_summary).length > 0 && (
                    <div>
                        <div className="detail-section-title">📑 Detected Sections</div>
                        <div className="skill-tags">
                            {Object.keys(analysis.section_summary).map(s => (
                                <span key={s} className="skill-tag neutral">{s}</span>
                            ))}
                        </div>
                    </div>
                )}

                {/* Explanation */}
                <div>
                    <div className="detail-section-title">💬 Explanation</div>
                    <div className="explanation-box">{analysis.explanation}</div>
                </div>

                {/* Suggestions */}
                {analysis.suggestions?.length > 0 && (
                    <div>
                        <div className="detail-section-title">🚀 Improvement Suggestions</div>
                        <div className="suggestion-list">
                            {analysis.suggestions.map((s, i) => (
                                <div key={i} className="suggestion-item">{s}</div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
