#!/usr/bin/env python3
"""Census of implicit state-machine signals (S1, S2, S4, S5, S12) in ``berb/``.

Usage:
    python scripts/find_implicit_state.py                 # TSV on stdout
    python scripts/find_implicit_state.py -o census.tsv

Columns: signal, file:line, snippet, module, wired.  Read-only, stdlib ``ast``.
``wired`` comes from ``scripts/check_reachability.py`` (reachable from the CLI or
server).  This only finds candidates; deciding what is a real machine is a
human or agent call.  Plan: ``tasks/implicit_state_machines_plan.md``.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import os
import re
import sys
from collections.abc import Iterator

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))

STATE_NAMES = frozenset(
    {"status", "state", "phase", "mode", "stage", "step", "decision", "verdict"}
)
FLAG_RE = re.compile(
    r"^_?(running|closed|active|started|stopped|done|finished|cancelled|timed_out|is_\w+)$"
)
LIFECYCLE = frozenset(
    {
        "start",
        "stop",
        "close",
        "end",
        "shutdown",
        "open",
        "begin",
        "finish",
        "cancel",
        "pause",
        "resume",
    }
)
MUTATORS = frozenset(
    {"append", "extend", "add", "update", "pop", "clear", "setdefault", "remove", "insert"}
)
ENUM_BASES = frozenset({"Enum", "IntEnum", "StrEnum", "IntFlag", "Flag"})

Row = tuple[str, int, str]  # signal, line, note


def _base_name(node: ast.expr) -> str:
    return node.attr if isinstance(node, ast.Attribute) else getattr(node, "id", "")


def _is_mutable_literal(node: ast.expr | None) -> bool:
    if isinstance(node, (ast.Dict, ast.List, ast.Set)):
        return True
    return isinstance(node, ast.Call) and _base_name(node.func) in {
        "dict",
        "list",
        "set",
        "defaultdict",
        "OrderedDict",
        "deque",
    }


def _functions(tree: ast.AST) -> Iterator[ast.FunctionDef | ast.AsyncFunctionDef]:
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield n


def _s1(tree: ast.AST) -> Iterator[Row]:
    for n in ast.walk(tree):
        targets: list[ast.expr] = []
        if isinstance(n, ast.Assign):
            targets = list(n.targets)
        elif isinstance(n, (ast.AugAssign, ast.AnnAssign)):
            targets = [n.target]
        for t in targets:
            if isinstance(t, ast.Attribute) and t.attr in STATE_NAMES:
                yield "S1", n.lineno, "attr"
            elif (
                isinstance(t, ast.Subscript)
                and isinstance(t.slice, ast.Constant)
                and t.slice.value in STATE_NAMES
            ):
                yield "S1", n.lineno, "key"
        if isinstance(n, ast.Dict):
            for k in n.keys:
                if isinstance(k, ast.Constant) and k.value in STATE_NAMES:
                    yield "S1", k.lineno, "dict-key"


def _s2(tree: ast.AST) -> Iterator[Row]:
    for fn in _functions(tree):
        if fn.name == "__init__":
            continue
        for n in ast.walk(fn):
            if (
                isinstance(n, ast.Assign)
                and isinstance(n.value, ast.Constant)
                and isinstance(n.value.value, bool)
            ):
                for t in n.targets:
                    if isinstance(t, ast.Attribute) and FLAG_RE.match(t.attr):
                        yield "S2", n.lineno, f"in {fn.name}"


def _enums(tree: ast.AST) -> dict[str, dict[str, object]]:
    """Enum classes defined in a tree: name -> {member: constant value}."""
    out: dict[str, dict[str, object]] = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef) and any(_base_name(b) in ENUM_BASES for b in n.bases):
            members: dict[str, object] = {}
            for s in n.body:
                if isinstance(s, ast.Assign) and isinstance(s.targets[0], ast.Name):
                    v = s.value.value if isinstance(s.value, ast.Constant) else None
                    members[s.targets[0].id] = v
            out[n.name] = members
    return out


def _s4_defs(tree: ast.AST) -> Iterator[Row]:
    names = _enums(tree)
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef) and n.name in names:
            yield "S4", n.lineno, f"enum {n.name}"


def _s4_raw(tree: ast.AST, str_values: set[str]) -> Iterator[Row]:
    """String equality against a value that some enum in the tree defines."""
    for n in ast.walk(tree):
        if isinstance(n, ast.Compare) and any(isinstance(o, (ast.Eq, ast.NotEq)) for o in n.ops):
            for c in [n.left, *n.comparators]:
                if (
                    isinstance(c, ast.Constant)
                    and isinstance(c.value, str)
                    and c.value in str_values
                ):
                    yield "S4", n.lineno, f"raw string {c.value!r}"


def _s5(tree: ast.Module) -> Iterator[Row]:
    for n in ast.walk(tree):
        if isinstance(n, ast.Global):
            yield "S5", n.lineno, "global " + ",".join(n.names)
    mutable = {
        t.id
        for s in tree.body
        if isinstance(s, (ast.Assign, ast.AnnAssign))
        for t in (s.targets if isinstance(s, ast.Assign) else [s.target])
        if isinstance(t, ast.Name) and _is_mutable_literal(s.value)
    }
    for fn in _functions(tree):
        local = {a.arg for a in fn.args.args} | {
            t.id
            for s in ast.walk(fn)
            if isinstance(s, ast.Assign)
            for t in s.targets
            if isinstance(t, ast.Name)
        }
        for n in ast.walk(fn):
            name = None
            if (
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and n.func.attr in MUTATORS
            ):
                name = getattr(n.func.value, "id", None)
            elif isinstance(n, (ast.Assign, ast.Delete)):
                for t in n.targets:
                    if isinstance(t, ast.Subscript):
                        name = getattr(t.value, "id", None)
            if name in mutable and name not in local:
                yield "S5", n.lineno, f"{name} mutated in {fn.name}"


def _s12(tree: ast.AST) -> Iterator[Row]:
    for n in ast.walk(tree):
        if not isinstance(n, ast.ClassDef):
            continue
        methods = {
            m.name: m for m in n.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        found = sorted(set(methods) & LIFECYCLE)
        if len(found) >= 2:
            guarded = [m for m in found if any(isinstance(s, ast.If) for s in methods[m].body[:2])]
            yield (
                "S12",
                n.lineno,
                (
                    f"class {n.name}: {','.join(found)}; if-guard in first 2 stmts: {','.join(guarded) or 'none'}"
                ),
            )


def scan_source(source: str, str_enum_values: set[str] | None = None) -> list[Row]:
    tree = ast.parse(source)
    rows: list[Row] = [*_s1(tree), *_s2(tree), *_s4_defs(tree), *_s5(tree), *_s12(tree)]
    if str_enum_values:
        rows.extend(_s4_raw(tree, str_enum_values))
    return rows


def _string_enum_values(trees: list[ast.AST]) -> set[str]:
    vals: set[str] = set()
    for t in trees:
        for members in _enums(t).values():
            vals.update(v for v in members.values() if isinstance(v, str))
    return vals


def _wired_set() -> set[str] | None:
    script = os.path.join(HERE, "check_reachability.py")
    spec = importlib.util.spec_from_file_location("check_reachability", script)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    all_mods, is_pkg = mod.discover_modules(mod.ROOT, mod.PKG)
    edges = mod.build_import_graph(all_mods, is_pkg, mod.PKG)
    return mod.compute_reachable(all_mods, edges, is_pkg)


def _module_name(path: str, root: str) -> str:
    rel = os.path.relpath(path, root).replace("\\", "/")[:-3]
    return rel.removesuffix("/__init__").replace("/", ".")


def scan_tree(root: str, pkg: str = "berb", wired: set[str] | None = None) -> list[tuple[str, ...]]:
    files: list[str] = []
    for dp, dn, fns in os.walk(os.path.join(root, pkg)):
        dn[:] = [d for d in dn if d not in ("__pycache__", "node_modules")]
        files += [os.path.join(dp, f) for f in fns if f.endswith(".py")]
    parsed: dict[str, tuple[str, ast.Module]] = {}
    for p in sorted(files):
        try:
            with open(p, encoding="utf-8") as fh:
                src = fh.read()
            parsed[p] = (src, ast.parse(src))
        except (SyntaxError, UnicodeDecodeError) as exc:
            print(f"skip {p}: {exc}", file=sys.stderr)
    values = _string_enum_values([t for _, t in parsed.values()])
    out: list[tuple[str, ...]] = []
    for p, (src, _) in parsed.items():
        lines = src.splitlines()
        mod = _module_name(p, root)
        flag = "?" if wired is None else ("Y" if mod in wired else "N")
        rel = os.path.relpath(p, root).replace("\\", "/")
        for sig, line, note in scan_source(src, values):
            text = lines[line - 1].strip().replace("\t", " ")[:110] if line <= len(lines) else ""
            out.append((sig, f"{rel}:{line}", f"{note} | {text}", mod, flag))
    out.sort(key=lambda r: (r[0], r[1]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-o", "--output", help="write TSV here instead of stdout")
    ap.add_argument("--root", default=ROOT)
    args = ap.parse_args()
    rows = scan_tree(args.root, wired=_wired_set())
    text = (
        "signal\tfile:line\tsnippet\tmodule\twired\n" + "\n".join("\t".join(r) for r in rows) + "\n"
    )
    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print(f"{len(rows)} rows -> {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
