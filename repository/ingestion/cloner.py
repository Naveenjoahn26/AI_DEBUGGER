"""
repository/ingestion/cloner.py

Responsible for:
  1. Validating a Git repository URL (rejects malformed / unsafe inputs).
  2. Cloning the repository into a temporary directory.
  3. Exposing the local path to callers via a context manager.
  4. Cleaning up the temporary directory automatically on exit.

Usage:
    from repository.ingestion.cloner import RepositoryCloner

    with RepositoryCloner.clone("https://github.com/owner/repo.git") as repo_path:
        # repo_path is a pathlib.Path pointing to the cloned repo
        scanner.scan(repo_path)
    # temp directory deleted automatically here
"""

import logging
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse

from repository.exceptions import CloneFailedError, InvalidRepositoryURLError

logger = logging.getLogger(__name__)

# Schemes we consider valid for a Git remote URL.
_ALLOWED_SCHEMES = {"https", "http", "git", "ssh", "file"}

# Characters that could allow shell injection when passed to subprocess.
_UNSAFE_CHARACTERS = {";", "&", "|", "`", "$(", "\n", "\r"}


def validate_url(url: str) -> None:
    """
    Validate a Git repository URL.

    Raises:
        InvalidRepositoryURLError: if the URL is empty, has a disallowed
            scheme, has no host, or contains shell-injection characters.
    """
    if not url or not url.strip():
        raise InvalidRepositoryURLError("Repository URL must not be empty.")

    # Check for shell-injection characters before parsing.
    for char in _UNSAFE_CHARACTERS:
        if char in url:
            raise InvalidRepositoryURLError(
                f"Repository URL contains unsafe character: {char!r}"
            )

    parsed = urlparse(url)

    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise InvalidRepositoryURLError(
            f"URL scheme {parsed.scheme!r} is not allowed. "
            f"Allowed schemes: {sorted(_ALLOWED_SCHEMES)}"
        )

    # file:// URIs (used for local-path clones) legitimately have no host.
    if parsed.scheme != "file" and not parsed.netloc:
        raise InvalidRepositoryURLError(
            "Repository URL must contain a valid host."
        )


class RepositoryCloner:
    """
    Clones a remote Git repository into a temporary local directory.

    Use as a context manager so the temporary directory is always cleaned up:

        with RepositoryCloner.clone(url) as path:
            ...

    The @contextmanager approach mirrors the simple style used elsewhere in
    this project (subprocess in scanner.py, stdlib-only dependencies).
    """

    @staticmethod
    @contextmanager
    def clone(url: str, depth: int = 1):
        """
        Validate *url*, clone the repository, yield the local path, then clean up.

        Args:
            url:   The Git remote URL to clone.
            depth: Number of commits to fetch (default 1 for a shallow clone,
                   which is much faster and uses less disk space).

        Yields:
            pathlib.Path — the root directory of the cloned repository.

        Raises:
            InvalidRepositoryURLError: if the URL is invalid.
            CloneFailedError:          if `git clone` exits non-zero.
        """
        validate_url(url)

        with tempfile.TemporaryDirectory(prefix="ai_debugger_clone_") as tmp_dir:
            dest = Path(tmp_dir) / "repo"

            logger.info(
                "cloning_repository: Starting git clone",
                extra={"url": url, "dest": str(dest), "depth": depth},
            )

            result = subprocess.run(
                ["git", "clone", "--depth", str(depth), url, str(dest)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            if result.returncode != 0:
                logger.error(
                    "clone_failed: git clone exited non-zero",
                    extra={
                        "url": url,
                        "returncode": result.returncode,
                        "stderr": result.stderr.strip(),
                    },
                )
                raise CloneFailedError(
                    f"git clone failed for {url!r} "
                    f"(exit {result.returncode}): {result.stderr.strip()}"
                )

            logger.info(
                "clone_complete: Repository cloned successfully",
                extra={"url": url, "dest": str(dest)},
            )

            yield dest

            # TemporaryDirectory.__exit__ deletes tmp_dir (and dest inside it).
            logger.info(
                "clone_cleanup: Temporary clone directory removed",
                extra={"tmp_dir": tmp_dir},
            )
