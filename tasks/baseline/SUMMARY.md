# P0 baseline (2026-11-11, branch chore/state-machine-census, base 7338445)

| Gate | Result | Pre-existing? |
|---|---|---|
| `pytest -m "not slow and not e2e and not llm"` | 4559 passed, 2 failed, 4 errors, 24 skipped (8m11s) | yes |
| `ruff check berb/ tests/` | pass | |
| `ruff format --check berb/ tests/` | `berb/reasoning/USAGE.md` would reformat | yes (a .md file) |
| `mypy berb/ --python-version 3.11` | 4 errors, all `Library stubs not installed for "yaml"` (config.py:10, writing/reporting_guidelines.py:26, literature/paper_mill.py:23, llm/client.py:1224) | yes (env: types-PyYAML missing) |
| `check_reachability.py` | pass; 341 wired / 71 parked / 2 DEAD (experiment.react_agent, experiment.split_policy) | |

Pre-existing pytest failures (not from this work):
- `tests/test_entry_point_validation.py::TestValidateEntryPointResolved::test_symlink_escape_rejected` (DID NOT RAISE ValueError; symlink semantics on Windows)
- `tests/test_phase3_knowledge.py::TestObsidianExporter::test_exporter_missing_vault_path`
- `tests/test_berb_pdf_ingestor.py` x4 errors (PermissionError on Windows temp pdf; pymupdf FileDataError)

Wired-module list: `wired_modules.txt` (denominator for P1c).
