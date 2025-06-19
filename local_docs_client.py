"""
Local Documentation Client
Provides simple search over local Markdown or text files
for NAVO knowledge discovery.
"""

import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class LocalDocsClient:
    """Client to search local documentation files"""

    def __init__(self):
        self.docs_path = os.getenv("LOCAL_DOCS_PATH")
        if self.docs_path and os.path.isdir(self.docs_path):
            self.enabled = True
            logger.info("LocalDocs client enabled")
        else:
            self.enabled = False
            logger.warning("LOCAL_DOCS_PATH not configured or invalid")

    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search local documents for the given query"""
        if not self.enabled:
            return []

        results: List[Dict[str, Any]] = []
        try:
            for root, _dirs, files in os.walk(self.docs_path):
                for name in files:
                    if name.lower().endswith((".md", ".txt")):
                        path = os.path.join(root, name)
                        try:
                            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read()
                            if query.lower() in content.lower() or query.lower() in name.lower():
                                results.append({
                                    "title": name,
                                    "url": f"file://{path}",
                                    "content": content[:1000],
                                    "source": "LocalDocs",
                                    "last_modified": str(os.path.getmtime(path))
                                })
                                if len(results) >= limit:
                                    return results
                        except Exception as e:
                            logger.warning(f"LocalDocs read error: {e}")
                            continue
            return results
        except Exception as e:
            logger.error(f"LocalDocs search error: {e}")
            return []
