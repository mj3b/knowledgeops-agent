import os
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Provide a stub AsyncOpenAI to avoid dependency on the real openai package
class _DummyClient:
    def __init__(self, *args, **kwargs):
        pass

sys.modules.setdefault("openai", types.SimpleNamespace(AsyncOpenAI=_DummyClient))

# Stub knowledge source clients to avoid external dependencies
class _DummySource:
    def __init__(self, *args, **kwargs):
        self.enabled = False

    async def search(self, *args, **kwargs):
        return []

dummy_source_module = types.SimpleNamespace(ConfluenceClient=_DummySource)
sys.modules.setdefault("confluence_client", dummy_source_module)
sys.modules.setdefault("sharepoint_client", types.SimpleNamespace(SharePointClient=_DummySource))
sys.modules.setdefault("local_docs_client", types.SimpleNamespace(LocalDocsClient=_DummySource))

from query_processor import QueryProcessor


def setup_query_processor():
    os.environ.setdefault("OPENAI_API_KEY", "test")
    return QueryProcessor()


def test_format_sources_includes_days_old():
    qp = setup_query_processor()
    now = datetime.now(timezone.utc)
    iso_date = now.isoformat().replace('+00:00', 'Z')
    results = [{
        "title": "Doc", 
        "url": "http://example.com", 
        "source": "Confluence", 
        "last_modified": iso_date, 
        "content": "Example content"
    }]
    formatted = qp._format_sources(results)
    assert formatted[0]["title"] == "Doc"
    assert formatted[0]["url"] == "http://example.com"
    assert formatted[0]["source_type"] == "Confluence"
    assert formatted[0]["days_old"] == 0
    assert formatted[0]["excerpt"].startswith("Example content")


def test_format_sources_handles_missing_date():
    qp = setup_query_processor()
    results = [{"title": "Doc", "url": "http://example.com", "source": "Confluence", "content": "Info"}]
    formatted = qp._format_sources(results)
    assert formatted[0]["days_old"] is None
    assert formatted[0]["last_updated"] == "Recently updated"
