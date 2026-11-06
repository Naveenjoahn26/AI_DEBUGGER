"""
tests/repository/test_cloner.py

Tests for repository.ingestion.cloner.

Design principle: no network calls.
We create a local bare Git repository as a fake "remote" so that
`git clone` works without touching the internet.
"""

import subprocess
import tempfile
from pathlib import Path

import pytest

from repository.exceptions import CloneFailedError, InvalidRepositoryURLError
from repository.ingestion.cloner import RepositoryCloner, validate_url


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_local_bare_repo() -> tempfile.TemporaryDirectory:
    """
    Create a minimal local bare Git repository that can be cloned.
    Returns the TemporaryDirectory (caller is responsible for cleanup).
    """
    tmp = tempfile.TemporaryDirectory(prefix="ai_debugger_test_remote_")
    bare_path = Path(tmp.name) / "fake_remote.git"
    bare_path.mkdir()

    subprocess.run(["git", "init", "--bare", str(bare_path)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Push one commit so the clone actually has something to check out.
    with tempfile.TemporaryDirectory(prefix="ai_debugger_test_work_") as work_dir:
        subprocess.run(["git", "init", work_dir], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", work_dir, "config", "user.email", "test@test.com"],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", work_dir, "config", "user.name", "Test"],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        readme = Path(work_dir) / "README.md"
        readme.write_text("# Test repo\n")

        subprocess.run(["git", "-C", work_dir, "add", "."], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", work_dir, "commit", "-m", "init"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(
            ["git", "-C", work_dir, "push", str(bare_path), "HEAD:main"],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )

    return tmp, bare_path


# ---------------------------------------------------------------------------
# validate_url tests  (pure — no filesystem, no network)
# ---------------------------------------------------------------------------

def test_validate_url_rejects_empty_string():
    with pytest.raises(InvalidRepositoryURLError, match="empty"):
        validate_url("")


def test_validate_url_rejects_whitespace_only():
    with pytest.raises(InvalidRepositoryURLError, match="empty"):
        validate_url("   ")


def test_validate_url_rejects_non_http_scheme():
    with pytest.raises(InvalidRepositoryURLError, match="scheme"):
        validate_url("ftp://example.com/repo.git")


def test_validate_url_rejects_shell_injection_semicolon():
    with pytest.raises(InvalidRepositoryURLError, match="unsafe"):
        validate_url("https://github.com/repo.git; rm -rf /")


def test_validate_url_rejects_shell_injection_pipe():
    with pytest.raises(InvalidRepositoryURLError, match="unsafe"):
        validate_url("https://github.com/repo.git | cat /etc/passwd")


def test_validate_url_rejects_missing_host():
    with pytest.raises(InvalidRepositoryURLError, match="host"):
        validate_url("https:///no-host/repo.git")


def test_validate_url_accepts_https():
    # Should NOT raise.
    validate_url("https://github.com/owner/repo.git")


def test_validate_url_accepts_ssh():
    validate_url("ssh://git@github.com/owner/repo.git")


def test_validate_url_accepts_git_scheme():
    validate_url("git://github.com/owner/repo.git")


# ---------------------------------------------------------------------------
# RepositoryCloner tests  (use local bare repo — no network)
# ---------------------------------------------------------------------------

def test_clone_produces_valid_path():
    """Cloning a local bare repo should yield a Path that actually exists."""
    tmp, bare_path = _make_local_bare_repo()
    try:
        with RepositoryCloner.clone(bare_path.as_uri()) as repo_path:
            assert repo_path.exists()
            assert repo_path.is_dir()
    finally:
        tmp.cleanup()


def test_cloned_repo_contains_readme():
    """The cloned directory should be non-empty (contain the committed file)."""
    tmp, bare_path = _make_local_bare_repo()
    try:
        with RepositoryCloner.clone(bare_path.as_uri()) as repo_path:
            cloned_files = list(repo_path.rglob("*"))
            assert len(cloned_files) > 0, "Expected at least one file in cloned repo"
    finally:
        tmp.cleanup()


def test_temp_directory_is_cleaned_up_after_context_exits():
    """After the context manager exits, the temp directory must be gone."""
    tmp, bare_path = _make_local_bare_repo()
    captured_path = None
    try:
        with RepositoryCloner.clone(bare_path.as_uri()) as repo_path:
            captured_path = repo_path
            assert captured_path.exists()

        # Outside the context — directory must be deleted.
        assert not captured_path.exists(), (
            f"Temp directory was not cleaned up: {captured_path}"
        )
    finally:
        tmp.cleanup()


def test_clone_raises_clone_failed_error_for_bad_url():
    """Cloning a non-existent URL should raise CloneFailedError."""
    with pytest.raises(CloneFailedError):
        with RepositoryCloner.clone("https://github.com/this-does-not-exist-xyz/no-repo-here.git"):
            pass  # pragma: no cover


def test_clone_raises_invalid_url_error_before_touching_filesystem():
    """Invalid URLs should raise before any git subprocess is spawned."""
    with pytest.raises(InvalidRepositoryURLError):
        with RepositoryCloner.clone(""):
            pass  # pragma: no cover
