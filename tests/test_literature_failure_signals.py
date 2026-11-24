"""Regression tests for two literature defects found in the ICM map audit.

1. Search clients swallowed every failure and returned ``[]``. ``search_papers``
   therefore never reached its cache fallback or its failed-source counter, and
   it overwrote good cache entries with an empty list.
2. ``verify_citations`` treated an OpenAlex miss as final, so the arXiv-id and
   Semantic Scholar layers never ran and real preprints were labelled
   hallucinated (which fails stage 22).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

import berb.literature.arxiv_client as arxiv_client
import berb.literature.openalex_client as openalex_client
import berb.literature.semantic_scholar as semantic_scholar
import berb.literature.verify as verify
from berb.literature.cache import get_cached, put_cache
from berb.literature.search import search_papers, search_papers_multi_query

_GOOD_ROW: dict[str, Any] = {
    "paper_id": "p1",
    "title": "Cached Paper",
    "authors": [],
    "year": 2023,
    "abstract": "",
    "venue": "",
    "citation_count": 9,
    "doi": "",
    "arxiv_id": "",
    "url": "",
    "source": "openalex",
}


# ---------------------------------------------------------------------------
# Clients: opt-in raise_on_failure, default unchanged
# ---------------------------------------------------------------------------


def test_openalex_raises_on_failure_when_asked_and_returns_empty_otherwise() -> None:
    with patch.object(openalex_client, "_request_with_retry", return_value=None):
        assert openalex_client.search_openalex("q") == []
        with pytest.raises(RuntimeError):
            openalex_client.search_openalex("q", raise_on_failure=True)


def test_semantic_scholar_raises_on_failure_when_asked_and_returns_empty_otherwise() -> None:
    with (
        patch.object(semantic_scholar, "_request_with_retry", return_value=None),
        patch.object(semantic_scholar._rate_limiter, "wait_sync", lambda: None),
    ):
        assert semantic_scholar.search_semantic_scholar("q") == []
        with pytest.raises(RuntimeError):
            semantic_scholar.search_semantic_scholar("q", raise_on_failure=True)


def test_arxiv_raises_on_failure_when_asked_and_returns_empty_otherwise() -> None:
    with patch.object(arxiv_client, "arxiv", None):
        assert arxiv_client.search_arxiv("q") == []
        with pytest.raises(RuntimeError):
            arxiv_client.search_arxiv("q", raise_on_failure=True)


def test_arxiv_raises_when_the_circuit_breaker_is_open() -> None:
    with (
        patch.object(arxiv_client, "_cb_should_allow", return_value=False),
        patch.object(arxiv_client, "arxiv", object()),
    ):
        assert arxiv_client.search_arxiv("q") == []
        with pytest.raises(RuntimeError, match="circuit breaker"):
            arxiv_client.search_arxiv("q", raise_on_failure=True)


# ---------------------------------------------------------------------------
# search_papers: cache fallback, failure counter, cache not poisoned
# ---------------------------------------------------------------------------


def _search_with_dead_openalex(tmp_path: Path, failure_counter: dict[str, int]) -> list[Any]:
    with (
        patch.object(openalex_client, "_request_with_retry", return_value=None),
        patch("berb.literature.cache._DEFAULT_CACHE_DIR", tmp_path),
        patch("berb.literature.search.time.sleep", lambda _: None),
    ):
        return search_papers("q", limit=10, sources=("openalex",), failure_counter=failure_counter)


def test_a_failing_source_falls_back_to_the_cache_and_is_counted(tmp_path: Path) -> None:
    put_cache("q", "openalex", 10, [_GOOD_ROW], cache_base=tmp_path)
    counter: dict[str, int] = {}

    papers = _search_with_dead_openalex(tmp_path, counter)

    assert [p.title for p in papers] == ["Cached Paper"]
    assert counter == {"openalex": 1}


def test_a_failing_source_does_not_overwrite_the_cache(tmp_path: Path) -> None:
    put_cache("q", "openalex", 10, [_GOOD_ROW], cache_base=tmp_path)

    _search_with_dead_openalex(tmp_path, {})

    cached = get_cached("q", "openalex", 10, cache_base=tmp_path)
    assert cached is not None and len(cached) == 1


def test_a_genuinely_empty_result_does_not_overwrite_the_cache(tmp_path: Path) -> None:
    put_cache("q", "openalex", 10, [_GOOD_ROW], cache_base=tmp_path)

    with (
        patch.object(openalex_client, "_request_with_retry", return_value={"results": []}),
        patch("berb.literature.cache._DEFAULT_CACHE_DIR", tmp_path),
        patch("berb.literature.search.time.sleep", lambda _: None),
    ):
        assert search_papers("q", limit=10, sources=("openalex",)) == []

    cached = get_cached("q", "openalex", 10, cache_base=tmp_path)
    assert cached is not None and len(cached) == 1


def test_enough_failed_sources_trigger_the_perplexity_top_up(tmp_path: Path) -> None:
    """With the old swallow-and-return-[] clients the failed-source count stayed 0."""
    with (
        patch.object(openalex_client, "_request_with_retry", return_value=None),
        patch.object(semantic_scholar, "_request_with_retry", return_value=None),
        patch.object(semantic_scholar._rate_limiter, "wait_sync", lambda: None),
        patch.object(arxiv_client, "arxiv", None),
        patch("berb.literature.cache._DEFAULT_CACHE_DIR", tmp_path),
        patch("berb.literature.search.time.sleep", lambda _: None),
        patch("berb.literature.search._perplexity_top_up", return_value=[]) as top_up,
    ):
        search_papers_multi_query(
            ["q"],
            perplexity_top_up=True,
            perplexity_min_candidates=0,  # rule out the "too few candidates" trigger
            perplexity_min_failed_sources=2,
        )

    top_up.assert_called_once()


# ---------------------------------------------------------------------------
# verify_citations: an OpenAlex miss is provisional
# ---------------------------------------------------------------------------


def _result(status: verify.VerifyStatus, method: str) -> verify.CitationResult:
    return verify.CitationResult("", "A Real Recent Preprint", status, 0.9, method)


@pytest.fixture
def layers_run(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Stub the on-disk cache and sleeps; the returned list records which layers ran."""
    monkeypatch.setattr(verify, "_read_cache", lambda *a, **k: None)
    monkeypatch.setattr(verify, "_write_cache", lambda *a, **k: None)
    monkeypatch.setattr(verify.time, "sleep", lambda _: None)
    return []


def _stub(
    monkeypatch: pytest.MonkeyPatch,
    layers_run: list[str],
    *,
    doi: verify.CitationResult | None = None,
    openalex: verify.CitationResult | None = None,
    arxiv: verify.CitationResult | None = None,
    s2: verify.CitationResult | None = None,
) -> None:
    def layer(name: str, out: verify.CitationResult | None) -> Any:
        def _call(*_a: Any, **_k: Any) -> verify.CitationResult | None:
            layers_run.append(name)
            return out

        return _call

    monkeypatch.setattr(verify, "verify_by_doi", layer("doi", doi))
    monkeypatch.setattr(verify, "verify_by_openalex", layer("openalex", openalex))
    monkeypatch.setattr(verify, "verify_by_arxiv_id", layer("arxiv", arxiv))
    monkeypatch.setattr(verify, "verify_by_title_search", layer("s2", s2))


_MISS = _result(verify.VerifyStatus.HALLUCINATED, "openalex")
_HIT = _result(verify.VerifyStatus.VERIFIED, "arxiv_id")

_BIB_EPRINT = "@article{real2024,\n  title={A Real Recent Preprint},\n  eprint={2401.00001},\n}\n"
_BIB_PLAIN = "@article{real2024,\n  title={A Real Recent Preprint},\n}\n"


def test_openalex_miss_still_checks_the_arxiv_id(
    layers_run: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub(monkeypatch, layers_run, openalex=_MISS, arxiv=_HIT)

    report = verify.verify_citations(_BIB_EPRINT)

    assert report.results[0].status == verify.VerifyStatus.VERIFIED
    assert "arxiv" in layers_run


def test_openalex_miss_still_tries_semantic_scholar_without_an_arxiv_id(
    layers_run: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub(monkeypatch, layers_run, openalex=_MISS, s2=_result(verify.VerifyStatus.VERIFIED, "s2"))

    report = verify.verify_citations(_BIB_PLAIN)

    assert report.results[0].status == verify.VerifyStatus.VERIFIED
    assert layers_run == ["openalex", "s2"]


def test_openalex_miss_stands_when_no_later_layer_answers(
    layers_run: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub(monkeypatch, layers_run, openalex=_MISS, arxiv=None, s2=None)

    report = verify.verify_citations(_BIB_EPRINT)

    assert report.results[0].status == verify.VerifyStatus.HALLUCINATED
    assert report.hallucinated == 1


def test_a_doi_verdict_is_still_final(
    layers_run: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The fix must not widen fallthrough for the authoritative DOI layer."""
    _stub(monkeypatch, layers_run, doi=_result(verify.VerifyStatus.HALLUCINATED, "doi"))
    bib = "@article{k,\n  title={A Real Recent Preprint},\n  doi={10.1000/x},\n}\n"

    report = verify.verify_citations(bib)

    assert report.results[0].status == verify.VerifyStatus.HALLUCINATED
    assert layers_run == ["doi"]
