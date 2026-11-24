"""berb/literature/verify.py: an outage is not a verdict (LT-1, LT-2).

LT-1  every search source down must not label real citations HALLUCINATED.
LT-2  an outage verdict must not be cached; the cache must not answer for a
      different DOI/arXiv id, and must survive an unwritable directory.
See tasks/implicit_state_machines_plan.md wave 2.
"""

from __future__ import annotations

import hashlib
import json
import urllib.error
from pathlib import Path

import pytest

import berb.literature.verify as verify
from berb.literature.models import Paper

_BIB = """@article{vaswani2017,
  title = {Attention Is All You Need},
  author = {Vaswani, Ashish},
  year = {2017},
}"""


def _result(status: verify.VerifyStatus, method: str = "openalex") -> verify.CitationResult:
    return verify.CitationResult(
        cite_key="",
        title="Attention Is All You Need",
        status=status,
        confidence=0.9,
        method=method,
    )


@pytest.fixture
def tmp_verify_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    cache = tmp_path / "citation_verify"
    monkeypatch.setattr(verify, "_CACHE_DIR", cache)
    monkeypatch.setattr(verify.time, "sleep", lambda _s: None)
    return cache


def _all_sources_down(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_a, **_kw):
        raise urllib.error.URLError("network down")

    monkeypatch.setattr(verify.urllib.request, "urlopen", boom)
    for name in ("search_openalex", "search_semantic_scholar", "search_arxiv"):
        monkeypatch.setattr(f"berb.literature.search.{name}", boom)
    monkeypatch.setattr("berb.literature.search.time.sleep", lambda _s: None)


# --- LT-1 ---------------------------------------------------------------


def test_total_search_outage_is_skipped_not_hallucinated(tmp_verify_cache, monkeypatch):
    _all_sources_down(monkeypatch)

    report = verify.verify_citations(_BIB, inter_verify_delay=0)

    assert report.results[0].status is verify.VerifyStatus.SKIPPED
    assert report.hallucinated == 0


def test_outage_leaves_nothing_in_the_cache(tmp_verify_cache, monkeypatch):
    _all_sources_down(monkeypatch)

    verify.verify_citations(_BIB, inter_verify_delay=0)

    assert not list(tmp_verify_cache.glob("*.json"))


def test_genuine_empty_search_is_still_hallucinated(monkeypatch):
    """A search that worked and found nothing keeps its verdict (no regression)."""
    for name in ("search_openalex", "search_semantic_scholar", "search_arxiv"):
        monkeypatch.setattr(f"berb.literature.search.{name}", lambda *a, **k: [])
    monkeypatch.setattr("berb.literature.search.time.sleep", lambda _s: None)

    result = verify.verify_by_title_search("A Title Nobody Ever Wrote")

    assert result is not None
    assert result.status is verify.VerifyStatus.HALLUCINATED


# --- LT-2 ---------------------------------------------------------------


def test_hallucinated_verdict_is_not_cached(tmp_verify_cache, monkeypatch):
    monkeypatch.setattr(
        verify, "verify_by_openalex", lambda _t: _result(verify.VerifyStatus.HALLUCINATED)
    )
    monkeypatch.setattr(verify, "verify_by_title_search", lambda *a, **k: None)

    verify.verify_citations(_BIB, inter_verify_delay=0)

    assert not list(tmp_verify_cache.glob("*.json"))


def test_stale_pre_fix_cache_entry_is_ignored(tmp_verify_cache, monkeypatch):
    """Entries written under the old unversioned key may be outage artefacts."""
    tmp_verify_cache.mkdir(parents=True)
    old_key = hashlib.sha256(b"attention is all you need").hexdigest()[:16]
    (tmp_verify_cache / f"{old_key}.json").write_text(
        json.dumps(
            {
                "cite_key": "x",
                "title": "Attention Is All You Need",
                "status": "hallucinated",
                "confidence": 0.7,
                "method": "title_search",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        verify, "verify_by_openalex", lambda _t: _result(verify.VerifyStatus.VERIFIED)
    )

    report = verify.verify_citations(_BIB, inter_verify_delay=0)

    assert report.results[0].status is verify.VerifyStatus.VERIFIED


def test_cached_verified_does_not_answer_for_a_different_doi(tmp_verify_cache, monkeypatch):
    monkeypatch.setattr(
        verify, "verify_by_openalex", lambda _t: _result(verify.VerifyStatus.VERIFIED)
    )
    verify.verify_citations(_BIB, inter_verify_delay=0)  # caches VERIFIED for the bare title

    with_doi = _BIB.replace("year = {2017},", "year = {2017},\n  doi = {10.9999/fake},")
    monkeypatch.setattr(
        verify,
        "verify_by_doi",
        lambda _d, _t: _result(verify.VerifyStatus.HALLUCINATED, "doi"),
    )

    report = verify.verify_citations(with_doi, inter_verify_delay=0)

    assert report.results[0].status is verify.VerifyStatus.HALLUCINATED


def test_unwritable_cache_dir_does_not_raise(tmp_path, monkeypatch):
    blocker = tmp_path / "file"
    blocker.write_text("not a dir", encoding="utf-8")
    monkeypatch.setattr(verify, "_CACHE_DIR", blocker / "sub")

    assert verify._read_cache("t") is None
    verify._write_cache(
        "t", verify.CitationResult("k", "t", verify.VerifyStatus.VERIFIED, 1.0, "doi")
    )  # must not raise


def test_cache_hit_keeps_matched_paper_doi(tmp_verify_cache):
    paper = Paper(paper_id="p", title="T", doi="10.1/abc", year=2020, source="openalex")
    verify._write_cache(
        "T",
        verify.CitationResult(
            "k", "T", verify.VerifyStatus.VERIFIED, 1.0, "title_search", "", paper
        ),
    )

    hit = verify._read_cache("T")

    assert hit is not None and hit.matched_paper is not None
    assert hit.matched_paper.doi == "10.1/abc"
