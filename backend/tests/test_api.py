from __future__ import annotations

import pytest


@pytest.mark.asyncio
class TestHealthEndpoint:
    async def test_health_check(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


@pytest.mark.asyncio
class TestResumeEndpoints:
    async def test_upload_invalid_type(self, client):
        """Reject non-PDF/DOCX files."""
        response = await client.post(
            "/v1/resumes/upload",
            files={"file": ("test.txt", b"hello world", "text/plain")},
        )
        assert response.status_code == 415

    async def test_upload_too_large(self, client):
        """Reject files exceeding size limit."""
        # Create a file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)
        response = await client.post(
            "/v1/resumes/upload",
            files={"file": ("big.pdf", large_content, "application/pdf")},
        )
        assert response.status_code == 413

    async def test_list_resumes_empty(self, client):
        """List resumes returns empty list initially."""
        response = await client.get("/v1/resumes")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_get_resume_not_found(self, client):
        """Get non-existent resume returns 404."""
        response = await client.get("/v1/resumes/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    async def test_list_resumes_pagination(self, client):
        """Pagination parameters are respected."""
        response = await client.get("/v1/resumes?page=1&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5


@pytest.mark.asyncio
class TestJobEndpoints:
    async def test_create_job(self, client):
        """Create a job description."""
        response = await client.post(
            "/v1/jobs",
            json={
                "title": "Senior Python Engineer",
                "description": "We are looking for a Python engineer with FastAPI and PostgreSQL experience.",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Senior Python Engineer"
        assert "id" in data
        assert "created_at" in data

    async def test_create_job_no_title(self, client):
        """Job without title is valid."""
        response = await client.post(
            "/v1/jobs",
            json={"description": "Looking for a developer with Python skills."},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] is None

    async def test_create_job_too_short(self, client):
        """Job with too-short description is rejected."""
        response = await client.post(
            "/v1/jobs",
            json={"description": "Short"},
        )
        assert response.status_code == 422

    async def test_get_job(self, client):
        """Get a created job by ID."""
        create_resp = await client.post(
            "/v1/jobs",
            json={
                "title": "Test Job",
                "description": "A test job description with enough content.",
            },
        )
        job_id = create_resp.json()["id"]

        get_resp = await client.get(f"/v1/jobs/{job_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == job_id

    async def test_get_job_not_found(self, client):
        """Get non-existent job returns 404."""
        response = await client.get("/v1/jobs/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestAnalysisEndpoints:
    async def test_analyze_not_found_resume(self, client):
        """Analyze with non-existent resume returns 404."""
        create_resp = await client.post(
            "/v1/jobs",
            json={"description": "Python developer with FastAPI experience needed."},
        )
        job_id = create_resp.json()["id"]

        response = await client.post(
            "/v1/analyze",
            json={
                "resume_id": "00000000-0000-0000-0000-000000000000",
                "job_id": job_id,
            },
        )
        assert response.status_code == 404

    async def test_get_analysis_not_found(self, client):
        """Get non-existent analysis returns 404."""
        response = await client.get("/v1/analyses/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404


    async def test_rank_not_found_job(self, client):
        """Rank with non-existent job returns 404."""
        response = await client.post(
            "/v1/jobs/00000000-0000-0000-0000-000000000000/rank",
            json={},
        )
        assert response.status_code == 404

    async def test_compare_not_found_job(self, client):
        """Compare with non-existent job returns 404."""
        response = await client.post(
            "/v1/compare",
            json={
                "resume_ids": [
                    "00000000-0000-0000-0000-000000000001",
                    "00000000-0000-0000-0000-000000000002",
                ],
                "job_id": "00000000-0000-0000-0000-000000000000",
            },
        )
        assert response.status_code == 404
