"""Web search, crawling, and content extraction layer.

Provides unified access to:
- **Crawl4AI**: Web page → Markdown extraction
- **Tavily**: AI-native web search API
- **scholarly**: Google Scholar search
- **PDF extraction**: Full-text from PDF files

Public API
----------
- ``WebSearchAgent`` — orchestrates all web capabilities
- ``WebCrawler`` — Crawl4AI wrapper
- ``WebSearchClient`` — Tavily search wrapper
- ``GoogleScholarClient`` — scholarly wrapper
- ``PDFExtractor`` — PDF text extraction
- ``check_url_ssrf`` — SSRF validation for URLs
"""

from berb.web._ssrf import check_url_ssrf
from berb.web.crawler import WebCrawler
from berb.web.search import WebSearchClient
from berb.web.scholar import GoogleScholarClient
from berb.web.pdf_extractor import PDFExtractor
from berb.web.agent import WebSearchAgent

__all__ = [
    "check_url_ssrf",
    "WebCrawler",
    "WebSearchClient",
    "GoogleScholarClient",
    "PDFExtractor",
    "WebSearchAgent",
]
