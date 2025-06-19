import sys
import types
import datetime
import importlib
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Stub external dependencies before importing the module under test
openai_stub = types.ModuleType('openai')
openai_stub.AsyncOpenAI = object
sys.modules.setdefault('openai', openai_stub)

aiohttp_stub = types.ModuleType('aiohttp')
aiohttp_stub.ClientSession = object
aiohttp_stub.ClientTimeout = object
aiohttp_stub.ClientError = Exception
sys.modules.setdefault('aiohttp', aiohttp_stub)

query_processor = importlib.import_module('query_processor')
QueryProcessor = query_processor.QueryProcessor

@pytest.fixture
def qp():
    # Create instance without invoking __init__
    return QueryProcessor.__new__(QueryProcessor)


def test_format_date_iso(monkeypatch, qp):
    fixed_now = datetime.datetime(2023, 1, 2, 12, 0, 0)

    class FixedDatetime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    monkeypatch.setattr(datetime, 'datetime', FixedDatetime)
    result = qp._format_date('2023-01-01T12:00:00Z')
    assert result == 'Yesterday'


@pytest.mark.parametrize('value', ['', 'Unknown'])
def test_format_date_unknown_strings(qp, value):
    assert qp._format_date(value) == 'Recently updated'


def test_format_date_invalid_iso(monkeypatch, qp):
    fixed_now = datetime.datetime(2023, 1, 2, 12, 0, 0)

    class FixedDatetime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    monkeypatch.setattr(datetime, 'datetime', FixedDatetime)
    # Invalid month triggers fallback path
    result = qp._format_date('2023-13-01T00:00:00Z')
    assert result == 'Recently updated'
