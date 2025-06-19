import os
import sys
import types
import datetime
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Stub external dependencies before importing the module under test
class _DummyClient:
    def __init__(self, *args, **kwargs):
        pass

sys.modules.setdefault("openai", types.SimpleNamespace(AsyncOpenAI=_DummyClient))

aiohttp_stub = types.ModuleType('aiohttp')
aiohttp_stub.ClientSession = object
aiohttp_stub.ClientTimeout = object
aiohttp_stub.ClientError = Exception
sys.modules.setdefault('aiohttp', aiohttp_stub)

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


def test_format_date_iso(monkeypatch):
    qp = setup_query_processor()
    fixed_now = datetime.datetime(2023, 1, 2, 12, 0, 0)

    class FixedDatetime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    monkeypatch.setattr(datetime, 'datetime', FixedDatetime)
    result = qp._format_date('2023-01-01T12:00:00Z')
    assert result == 'Yesterday'


@pytest.mark.parametrize('value', ['', 'Unknown'])
def test_format_date_unknown_strings(value):
    qp = setup_query_processor()
    assert qp._format_date(value) == 'Recently updated'


def test_format_date_invalid_iso(monkeypatch):
    qp = setup_query_processor()
    fixed_now = datetime.datetime(2023, 1, 2, 12, 0, 0)

    class FixedDatetime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    monkeypatch.setattr(datetime, 'datetime', FixedDatetime)
    # Invalid month triggers fallback path
    result = qp._format_date('2023-13-01T00:00:00Z')
    assert result == 'Recently updated'


def test_format_sources_includes_days_old():
    qp = setup_query_processor()
    now = datetime.datetime.now(datetime.timezone.utc)
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

