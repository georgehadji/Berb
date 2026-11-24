"""berb/literature/retraction.py: a one-sided lookup is not a clean bill (LT-7).

A retraction check that could only reach one index must read as UNKNOWN and
must not be cached; the cache is keyed by DOI, not by cite_key.
See tasks/implicit_state_machines_plan.md wave 2.
"""

from __future__ import annotations

import json
import urllib.error
from unittest.mock import MagicMock, patch

from berb.literature.retraction import (
    RetractionRecord,
    RetractionState,
    resolve_retraction,
    store_lookup,
)


def _urlopen_for(crossref, openalex):
    """Fake urlopen: payload None means that index is unreachable."""

    def fake(req, **_kw):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        payload = crossref if "crossref.org" in url else openalex
        if payload is None:
            raise urllib.error.URLError("down")
        resp = MagicMock()
        resp.read.return_value = json.dumps(payload).encode()
        resp.__enter__.return_value = resp
        return resp

    return fake


_CROSSREF_OK = {"message": {}}


def test_one_sided_outage_is_unknown_and_not_cached(tmp_path):
    with patch("urllib.request.urlopen", _urlopen_for(None, {"is_retracted": False})):
        first = resolve_retraction("smith2023", "10.1/a", cache_base=tmp_path)
    assert first.state is RetractionState.UNKNOWN

    # Both indexes are up now and OpenAlex knows the retraction: it must be seen.
    with patch("urllib.request.urlopen", _urlopen_for(_CROSSREF_OK, {"is_retracted": True})):
        second = resolve_retraction("smith2023", "10.1/a", cache_base=tmp_path)
    assert second.state is RetractionState.RETRACTED


def test_adverse_finding_from_one_source_still_surfaces(tmp_path):
    with patch("urllib.request.urlopen", _urlopen_for(None, {"is_retracted": True})):
        record = resolve_retraction("k", "10.1/a", cache_base=tmp_path)
    assert record.state is RetractionState.RETRACTED


def test_cache_is_keyed_by_doi_not_cite_key(tmp_path):
    with patch("urllib.request.urlopen", _urlopen_for(_CROSSREF_OK, {"is_retracted": False})):
        first = resolve_retraction("smith2023", "10.1/a", cache_base=tmp_path)
    assert first.state is RetractionState.NONE

    # A different paper that happens to share the cite_key must not inherit NONE.
    with patch("urllib.request.urlopen", _urlopen_for(_CROSSREF_OK, {"is_retracted": True})):
        other = resolve_retraction("smith2023", "10.1/b", cache_base=tmp_path)
    assert other.state is RetractionState.RETRACTED


def test_complete_lookup_is_cached_for_the_same_doi(tmp_path):
    with patch("urllib.request.urlopen", _urlopen_for(_CROSSREF_OK, {"is_retracted": False})):
        resolve_retraction("k", "10.1/A", cache_base=tmp_path)
    with patch("urllib.request.urlopen") as net:
        again = resolve_retraction("other_key", "10.1/a", cache_base=tmp_path)  # DOI is case-blind
    net.assert_not_called()
    assert again.state is RetractionState.NONE
    assert again.cite_key == "other_key"


def test_legacy_cached_none_is_not_trusted(tmp_path):
    store_lookup(RetractionRecord("k1", RetractionState.NONE), cache_base=tmp_path)
    with patch("urllib.request.urlopen", _urlopen_for(_CROSSREF_OK, {"is_retracted": True})):
        record = resolve_retraction("k1", "10.1/a", cache_base=tmp_path)
    assert record.state is RetractionState.RETRACTED
