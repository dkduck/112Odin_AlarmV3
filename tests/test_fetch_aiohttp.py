import asyncio
import feedparser

def test_feedparser_import():
    # simple smoke test
    assert hasattr(feedparser, 'parse')
