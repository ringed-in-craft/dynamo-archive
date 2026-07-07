import hashlib
import json
from pathlib import Path


def test_report_exists():
    """The agent must write /app/report.json."""
    assert Path("/app/report.json").exists(), "report.json not found"


def test_report_valid_json():
    """The report must contain valid JSON."""
    raw = Path("/app/report.json").read_text()
    data = json.loads(raw)
    assert isinstance(data, dict), "report.json must be a JSON object"


def test_report_has_required_keys():
    """The report must contain total_requests, unique_ips, and top_path keys."""
    data = json.loads(Path("/app/report.json").read_text())
    assert "total_requests" in data, "missing total_requests"
    assert "unique_ips" in data, "missing unique_ips"
    assert "top_path" in data, "missing top_path"


def test_report_total_requests():
    """The report must report exactly 6 total requests."""
    data = json.loads(Path("/app/report.json").read_text())
    assert data["total_requests"] == 6, f"expected 6 requests, got {data['total_requests']}"


def test_report_unique_ips():
    """The report must report exactly 3 unique IPs."""
    data = json.loads(Path("/app/report.json").read_text())
    assert data["unique_ips"] == 3, f"expected 3 unique IPs, got {data['unique_ips']}"


def test_report_top_path():
    """The most requested path must be /index.html (3 requests)."""
    data = json.loads(Path("/app/report.json").read_text())
    assert data["top_path"] == "/index.html", f"expected /index.html, got {data['top_path']}"


def test_access_log_unchanged():
    """The agent must not modify /app/access.log."""
    h = hashlib.sha256(Path("/app/access.log").read_bytes()).hexdigest()
    assert h == "e83c0cb8dd9c33cbe0954cc038bd0ff90834cf48747e257d931dce5b2408d38e", "access.log was modified"
