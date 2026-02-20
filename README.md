# AI Resume Analyzer

An intelligent tool to analyze, score, and rank resumes against job descriptions using FastAPI, NLP, and PGVector.

## 🚀 Features

- **Resume Parsing**: Extract text from PDF and DOCX files.
- **Bias-Aware Privacy**: Redact PII (names, emails, phones) before analysis to ensure fairness.
- **Skills Matching**: Automatically extract skills and identify gaps.
- **Smart Scoring**: Uses Sentence-Transformers for semantic similarity between resumes and job descriptions.
- **Portfolio Scaffold**: Ready-to-use landing page for showcase.

## 🛠 Tech Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL (PGVector), SpaCy, Sentence-Transformers.
- **Frontend**: React, Vite, CSS Modules.
- **DevOps**: Docker, Docker Compose, GitHub Actions.

## 📦 Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js (optional, for local frontend development)
- Python 3.11+ (optional, for local backend development)

### Local Development

1.  **Clone the repo**:
    ```bash
    git clone https://github.com/your-username/AI-resume-analyzer.git
    cd AI-resume-analyzer
    ```

2.  **Setup Environment**:
    ```bash
    cp .env.example .env
    ```

3.  **Start Services**:
    ```bash
    docker-compose up -d
    ```

4.  **Run Migrations**:
    ```bash
    docker-compose exec api alembic upgrade head
    ```

The API will be available at `http://localhost:8000/docs` and the frontend at `http://localhost:5173`.

## 📈 Makefile Commands

We provide a `Makefile` for convenience:

- `make up`: Start services.
- `make logs`: View logs.
- `make test`: Run backend tests.
- `make migrate`: Run database migrations.
- `make lint`: Run linters (Ruff/MyPy).

## 🛡 Security

See [SECURITY.md](SECURITY.md) for reporting vulnerabilities.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


A production-ready, API-first resume analysis platform powered by Sentence Transformers, spaCy, and FastAPI. Upload resumes, paste a job description, and get instant match scores, skill gap analysis, and actionable improvement suggestions.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    docker-compose                        │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Frontend    │  │   Backend    │  │  PostgreSQL  │  │
│  │  React+Vite  │→ │   FastAPI    │→ │  + pgvector  │  │
│  │  nginx:80    │  │  port 8000   │  │  port 5432   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Pipeline

```
Upload (PDF/DOCX)
    → Text Extraction (pdfplumber / python-docx)
    → Text Cleaning (whitespace, bullets, page numbers)
    → PII Redaction (spaCy NER + regex: names, emails, phones, addresses)
    → Section Detection (regex heading rules)
    → Skills Extraction (dictionary/PhraseMatcher against skills.yml)
    → Embedding Generation (Sentence Transformers: all-MiniLM-L6-v2)
    → Cosine Similarity vs JD Embedding
    → Score Normalization: (cos_sim + 1) / 2 × 100
    → Skill Gap Analysis (intersection / difference)
    → Template-based Explanation + Suggestions
    → Store in PostgreSQL
```

---

## Local Development

### Prerequisites
- Docker Desktop
- Python 3.11+ (for local dev without Docker)
- Node 20+ (for frontend dev)

### Quick Start (Docker)

```bash
# 1. Clone and configure
cp .env.example .env

# 2. Start all services
docker-compose up -d

# 3. Run database migrations
docker-compose exec api alembic upgrade head

# 4. (Optional) Pre-download ML models
make download-models

# 5. Open the app
# Frontend: http://localhost:5173
# API docs: http://localhost:8000/docs
```

### Local Backend Dev

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Set env vars (copy .env.example to .env and adjust DATABASE_URL)
uvicorn app.main:app --reload --port 8000
```

### Local Frontend Dev

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

---

## API Usage Examples

### Upload a Resume

```bash
curl -X POST http://localhost:8000/v1/resumes/upload \
  -F "file=@resume.pdf"
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "original_filename": "resume.pdf",
  "extraction_status": "success",
  "sha256": "abc123...",
  "created_at": "2026-02-18T17:00:00Z"
}
```

### Create a Job Description

```bash
curl -X POST http://localhost:8000/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Python Engineer",
    "description": "We are looking for a Python engineer with FastAPI, PostgreSQL, Docker, and AWS experience..."
  }'
```

### Analyze One Resume

```bash
curl -X POST http://localhost:8000/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "<resume-uuid>",
    "job_id": "<job-uuid>"
  }'
```

### Rank Multiple Resumes

```bash
# Upload 3 resumes first, then:
curl -X POST http://localhost:8000/v1/jobs/<job-uuid>/rank \
  -H "Content-Type: application/json" \
  -d '{
    "resume_ids": ["<uuid1>", "<uuid2>", "<uuid3>"]
  }'
```

### Sample Workflow (3 Resumes → Rank)

```bash
# Step 1: Upload 3 resumes
R1=$(curl -s -X POST http://localhost:8000/v1/resumes/upload -F "file=@alice.pdf" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
R2=$(curl -s -X POST http://localhost:8000/v1/resumes/upload -F "file=@bob.docx" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
R3=$(curl -s -X POST http://localhost:8000/v1/resumes/upload -F "file=@carol.pdf" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Step 2: Create JD
JOB=$(curl -s -X POST http://localhost:8000/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"title":"Python Dev","description":"Python, FastAPI, Docker, PostgreSQL, AWS, CI/CD experience required."}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Step 3: Rank
curl -X POST http://localhost:8000/v1/jobs/$JOB/rank \
  -H "Content-Type: application/json" \
  -d "{\"resume_ids\": [\"$R1\", \"$R2\", \"$R3\"]}"

# Step 4: View details
curl http://localhost:8000/v1/resumes/$R1
```

---

## Score Interpretation

| Score | Meaning |
|-------|---------|
| 75–100% | Strong match |
| 50–74% | Moderate match |
| 0–49% | Weak match |

**Score formula**: `score = clamp((cosine_similarity + 1) / 2 × 100, 0, 100)`

This is a linear normalization of cosine similarity from [-1, 1] to [0, 100]. Typical resume-JD similarities range from 0.3–0.9 (50–95%). A calibrated threshold model is a future improvement (see TODO in `embedder.py`).

---

## ML Models

| Model | Purpose | Size |
|-------|---------|------|
| `sentence-transformers/all-MiniLM-L6-v2` | Text embeddings | ~80MB |
| `en_core_web_sm` | NER for PII redaction | ~12MB |

### Offline / Air-gapped Environments

Models are pre-downloaded during Docker build (`Dockerfile`). For fully offline use:

```bash
# Pre-download on a machine with internet, then copy cache
docker-compose exec api python -c "
from sentence_transformers import SentenceTransformer
SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
"
```

The model cache is stored in the `model_cache` Docker volume.

---

## Database Schema

| Table | Purpose |
|-------|---------|
| `resumes` | Uploaded files + extracted/cleaned/redacted text + sections |
| `jobs` | Job descriptions |
| `embeddings` | Cached embedding vectors (JSONB; pgvector upgrade path documented) |
| `analyses` | Match results: score, skills, explanation, suggestions |

### pgvector Upgrade Path

Currently embeddings are stored as JSONB arrays. To upgrade to pgvector:
1. Ensure `pgvector/pgvector:pg16` image is used (already in docker-compose)
2. The migration runs `CREATE EXTENSION IF NOT EXISTS vector`
3. Add a new `vector(384)` column to `embeddings` table
4. Migrate JSONB → vector column
5. Create `ivfflat` or `hnsw` index for ANN search

---

## Running Tests

```bash
cd backend
pip install aiosqlite  # for in-memory SQLite tests
pytest tests/ -v --tb=short
pytest tests/ --cov=app --cov-report=term-missing
```

---

## Security Considerations

- **File validation**: Content-type + size enforced before processing
- **Safe filenames**: UUID-based, no user-provided paths
- **PII redaction**: Names, emails, phones, addresses removed before embedding
- **No code execution**: Uploaded files are never executed
- **Non-root Docker**: API runs as `appuser` (UID 1000)
- **CORS**: Configurable via `CORS_ORIGINS` env var
- **No auth (MVP)**: Structure supports adding OAuth2/JWT middleware to FastAPI
- **Secrets**: Never logged; use `.env` file (not committed)

---

## Advanced Features Implemented

- ✅ Bias-aware scoring (PII redaction before embeddings)
- ✅ Section detection (education, skills, experience, projects, certifications)
- ✅ Resume improvement suggestions (grounded, template-based)
- ✅ Multiple resume comparison (`/v1/compare`)
- ✅ API-first design with versioned endpoints

## TODOs / Future Work

- [ ] Calibrate score thresholds with labeled data
- [ ] OCR support for scanned PDFs (Tesseract integration, opt-in)
- [ ] Celery/RQ for background embedding jobs
- [ ] pgvector ANN indexing for large-scale ranking
- [ ] Authentication (OAuth2 + JWT)
- [ ] Resume version history
- [ ] Export results as PDF/CSV
- [ ] LLM-based suggestions (constrained, evidence-grounded)
