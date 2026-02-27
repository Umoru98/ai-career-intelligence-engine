import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

const api = axios.create({
    baseURL: BASE_URL,
    timeout: 120000, // 2 min for ML operations
})

// Add session ID to every request
api.interceptors.request.use((config) => {
    const sessionId = localStorage.getItem('session_id')
    if (sessionId) {
        config.headers['X-Session-ID'] = sessionId
    }
    return config
})

// ── Resumes ────────────────────────────────────────────────────────────────────

export async function uploadResume(file, onProgress) {
    const MAX_FILE_SIZE = 2 * 1024 * 1024 // 2MB
    if (file.size > MAX_FILE_SIZE) {
        throw new Error(
            'File optimized for speed? We cap uploads at 2MB to ensure our AI can process your data instantly. Most standard resumes are under 200KB. Compressing your PDF will give you the fastest results!'
        )
    }
    const formData = new FormData()
    formData.append('file', file)
    const res = await api.post('/v1/resumes/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
            if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100))
        },
    })
    return res.data
}

export async function listResumes(page = 1, pageSize = 50) {
    const res = await api.get('/v1/resumes', { params: { page, page_size: pageSize } })
    return res.data
}

export async function getResume(id) {
    const res = await api.get(`/v1/resumes/${id}`)
    return res.data
}

// ── Jobs ───────────────────────────────────────────────────────────────────────

export async function createJob(title, description) {
    const res = await api.post('/v1/jobs', { title, description })
    return res.data
}

export async function getJob(id) {
    const res = await api.get(`/v1/jobs/${id}`)
    return res.data
}

// ── Analysis ───────────────────────────────────────────────────────────────────

export async function analyzeResume(resumeId, jobId) {
    const res = await api.post('/v1/analyze', { resume_id: resumeId, job_id: jobId })
    return res.data
}

export async function getAnalysisStatus(analysisId) {
    const res = await api.get(`/v1/analyses/${analysisId}`)
    return res.data
}


export async function rankResumes(jobId, resumeIds = null) {
    const body = resumeIds ? { resume_ids: resumeIds } : {}
    const res = await api.post(`/v1/jobs/${jobId}/rank`, body)
    return res.data
}

export async function compareResumes(resumeIds, jobId) {
    const res = await api.post('/v1/compare', { resume_ids: resumeIds, job_id: jobId })
    return res.data
}

export async function healthCheck() {
    const res = await api.get('/health')
    return res.data
}

export async function clearResumes() {
    const res = await api.delete('/v1/resumes/clear')
    return res.data
}
