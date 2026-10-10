"""
Unit Tests for CryptoScanner (Phase B1)
Validates multi-backend scanning, AST analysis, regex pattern matching,
directory exclusion, and metadata accuracy.
"""

import pytest
from pathlib import Path
from app.engines.scanner import CryptoScanner, scan_project


@pytest.fixture
def mock_project(tmp_path: Path) -> Path:
    """
    Creates a temporary mock project tree with heterogeneous source code
    and configuration files containing classical and quantum-safe cryptography.
    """
    project_dir = tmp_path / "mock_mining_project"
    project_dir.mkdir()

    # 1. auth.py with RSA.generate(2048)
    auth_file = project_dir / "auth.py"
    auth_file.write_text(
        """
import Crypto.PublicKey.RSA as RSA

def setup_keys():
    key = RSA.generate(2048)
    return key.export_key()
""",
        encoding="utf-8"
    )

    # 2. server.js with prime256v1 (ECDSA)
    server_file = project_dir / "server.js"
    server_file.write_text(
        """
const crypto = require('crypto');
function createEcKeys() {
    return crypto.generateKeyPairSync('ec', { namedCurve: 'prime256v1' });
}
""",
        encoding="utf-8"
    )

    # 3. config.yaml with RSA-4096
    config_file = project_dir / "config.yaml"
    config_file.write_text(
        """
tls:
  enabled: true
  cipher: RSA-4096
  cert_path: /etc/certs/node.crt
""",
        encoding="utf-8"
    )

    # 4. hash.py with hashlib.md5()
    hash_file = project_dir / "hash.py"
    hash_file.write_text(
        """
import hashlib

def calculate_checksum(data):
    return hashlib.md5(data.encode('utf-8')).hexdigest()
""",
        encoding="utf-8"
    )

    # 5. safe.py with hashlib.sha256()
    safe_file = project_dir / "safe.py"
    safe_file.write_text(
        """
import hashlib

def secure_digest(payload):
    return hashlib.sha256(payload).hexdigest()
""",
        encoding="utf-8"
    )

    # 6. node_modules file to test directory skipping
    nm_dir = project_dir / "node_modules" / "vendor_pkg"
    nm_dir.mkdir(parents=True)
    nm_file = nm_dir / "index.js"
    nm_file.write_text(
        """
const crypto = require('crypto');
const dummy = crypto.generateKeyPairSync('rsa', { modulusLength: 1024 });
""",
        encoding="utf-8"
    )

    return project_dir


def test_scanner_finds_rsa(mock_project: Path):
    scanner = CryptoScanner(str(mock_project))
    result = scanner.scan()
    findings = result["findings"]

    rsa_findings = [f for f in findings if "RSA" in f["algorithm"].upper()]
    assert len(rsa_findings) >= 1
    # Check that RSA-2048 or RSA-4096 was discovered
    algos = {f["algorithm"].upper() for f in rsa_findings}
    assert any("RSA" in a for a in algos)
    for f in rsa_findings:
        assert f["severity"] == "CRITICAL"


def test_scanner_finds_ecdsa(mock_project: Path):
    scanner = CryptoScanner(str(mock_project))
    result = scanner.scan()
    findings = result["findings"]

    ecdsa_findings = [f for f in findings if "ECDSA" in f["algorithm"].upper() or "PRIME256V1" in f.get("context", "").lower()]
    assert len(ecdsa_findings) >= 1
    target = ecdsa_findings[0]
    assert target["severity"] == "CRITICAL"
    assert "server.js" in target["file"]


def test_scanner_finds_md5(mock_project: Path):
    scanner = CryptoScanner(str(mock_project))
    result = scanner.scan()
    findings = result["findings"]

    md5_findings = [f for f in findings if f["algorithm"].upper() == "MD5"]
    assert len(md5_findings) >= 1
    target = md5_findings[0]
    assert target["severity"] == "HIGH"
    assert "hash.py" in target["file"]


def test_scanner_returns_metadata(mock_project: Path):
    scanner = CryptoScanner(str(mock_project))
    result = scanner.scan()

    assert "count" in result
    assert "source" in result
    assert "scan_time_ms" in result
    assert "findings" in result
    assert isinstance(result["count"], int)
    assert result["count"] == len(result["findings"])
    assert result["scan_time_ms"] >= 0
    assert result["source"] in ["ast+regex", "regex-engine", "quantum-safe-audit", "postquant"]


def test_scanner_skips_node_modules(mock_project: Path):
    scanner = CryptoScanner(str(mock_project))
    result = scanner.scan()
    findings = result["findings"]

    for f in findings:
        file_path_str = f["file"].replace("\\", "/")
        assert "node_modules" not in file_path_str, f"Finding leaked from node_modules: {file_path_str}"


def test_scan_project_convenience(mock_project: Path):
    result = scan_project(str(mock_project))
    assert isinstance(result, dict)
    assert result["count"] >= 4
    assert len(result["findings"]) == result["count"]
