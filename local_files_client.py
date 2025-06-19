"""
Local Files Client
Search local documentation directory for simple keyword matches.
This client provides an example of extending NAVO's knowledge sources.
"""

import os
import logging
from typing import List, Dict, Any
import glob

logger = logging.getLogger(__name__)


class LocalFilesClient:
    """Client for searching local markdown and text files."""

    def __init__(self):
        self.docs_path = os.getenv("LOCAL_DOCS_PATH")
        if not self.docs_path or not os.path.isdir(self.docs_path):
            logger.warning("Local files path not configured or invalid")
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"Local files client enabled at {self.docs_path}")

    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search the local docs directory for files containing the query."""
        if not self.enabled:
            return []

        results: List[Dict[str, Any]] = []
        try:
            pattern = os.path.join(self.docs_path, "**", "*.*")
            for path in glob.glob(pattern, recursive=True):
                if not os.path.isfile(path):
                    continue
                if not path.lower().endswith((".md", ".txt", ".rst")):
                    continue
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                except Exception:
                    continue
                if query.lower() in content.lower() or query.lower() in os.path.basename(path).lower():
                    stat = os.stat(path)
                    result = {
                        "title": os.path.basename(path),
                        "url": f"file://{os.path.abspath(path)}",
                        "content": content[:1000],
                        "source": "LocalDocs",
                        "last_modified": str(stat.st_mtime),
                    }
                    results.append(result)
                    if len(results) >= limit:
                        break
        except Exception as e:
            logger.warning(f"Local files search error: {e}")

        return results
