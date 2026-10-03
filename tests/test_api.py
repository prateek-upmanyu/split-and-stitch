import pytest
import os
import json
import time
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure test environment variables
os.environ["MODE"] = "mock"
os.environ["MAGICAPI_KEY"] = "test_magic_key"

from app.main import app, cleanup_old_jobs, update_job, read_job, jobs
from app.settings import settings

client = TestClient(app)

def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Split & Stitch" in response.text

def test_api_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "jobs_count" in data

def test_api_preflight():
    response = client.get("/api/preflight")
    assert response.status_code == 200
    data = response.json()
    assert "ready" in data
    assert "mode" in data

def test_api_connectivity():
    response = client.get("/api/connectivity")
    assert response.status_code == 200
    data = response.json()
    assert "mode" in data

def test_job_not_found():
    response = client.get("/api/jobs/non_existent_job_12345")
    assert response.status_code == 404

def test_download_not_ready():
    response = client.get("/api/jobs/non_existent_job_12345/download")
    assert response.status_code == 404

def test_download_incomplete_job_with_empty_final():
    job_id = "test_incomplete_job_999"
    jobs[job_id] = {"id": job_id, "stage": "Processing", "complete": False, "final": ""}
    response = client.get(f"/api/jobs/{job_id}/download")
    assert response.status_code == 404
    jobs.pop(job_id, None)


def test_cleanup_old_jobs():
    # Create a temporary fake old job directory and file
    temp_dir = Path(tempfile.gettempdir()) / "character_swap_jobs"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    old_job_dir = temp_dir / "test_old_job_dir"
    old_job_dir.mkdir(parents=True, exist_ok=True)
    old_file = old_job_dir / "old_file.txt"
    old_file.write_text("old content")
    
    # Set mtime to 2 hours ago
    two_hours_ago = time.time() - 7200
    os.utime(old_job_dir, (two_hours_ago, two_hours_ago))
    
    # Run cleanup with 3600 max age
    cleanup_old_jobs(max_age_seconds=3600)
    
    # Verify the old dir is cleaned up
    assert not old_job_dir.exists()

def test_create_job_validation():
    # Posting without video and character should fail with 400
    response = client.post("/api/jobs", data={"engine": "magicapi"})
    assert response.status_code == 400

def test_job_id_validation_path_traversal():
    malicious_ids = [
        "../../etc/passwd",
        "..\\..\\Windows\\System32",
        "job; rm -rf /",
        "job id with spaces",
        "job<script>alert(1)</script>"
    ]
    for bad_id in malicious_ids:
        # Route parameter or query
        resp_get = client.get(f"/api/jobs/{bad_id}")
        assert resp_get.status_code in (400, 404), f"Failed for {bad_id}"
        
        resp_dl = client.get(f"/api/jobs/{bad_id}/download")
        assert resp_dl.status_code in (400, 404), f"Failed for {bad_id}"
        
        resp_retry = client.post(f"/api/jobs/{bad_id}/retry")
        assert resp_retry.status_code in (400, 404), f"Failed for {bad_id}"

def test_settings_attributes():
    assert hasattr(settings, "magicapi_key")
    assert hasattr(settings, "fal_key")
    assert hasattr(settings, "replicate_api_token")
    assert hasattr(settings, "storage_dir")
    assert hasattr(settings, "comfyui_url")
    assert hasattr(settings, "wan_workflow_path")

@pytest.mark.asyncio
async def test_upscale_video_graceful_fallback(monkeypatch, tmp_path):
    from app.main import upscale_video
    # Create dummy video file
    dummy_video = tmp_path / "test.mp4"
    dummy_video.write_bytes(b"dummy_data")
    
    # Unset magicapi_key to ensure graceful fallback
    monkeypatch.setattr(settings, "magicapi_key", None)
    monkeypatch.delenv("MAGICAPI_KEY", raising=False)
    
    result = await upscale_video(dummy_video, "fake_job_123")
    assert result == dummy_video
    assert result.exists()

