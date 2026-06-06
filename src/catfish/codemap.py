"""Logic-based Map of Content for a codebase, emitted as a Foam-compatible wiki.

This is the deterministic L0/L1 rung from the spec: structure is ground truth, extracted with
the standard library (`ast` for Python — zero deps, precise; ripgrep is the language-agnostic
fallback for non-Python repos, not needed here). Each module becomes a `code-capability` node
organized by what it does, linked by `depends-on` edges, ranked by how many modules use it.

Business-value lines are PROPOSALS derived from the module's own docstring, marked
`status: proposed` — they are not asserted facts (business value is not derivable from source;
a human confirms them).
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

# heuristic value_type by capability name (a proposal, human-confirmable)
_VALUE_TYPE = [
    (("gate", "security", "secret"), "risk"),
    (("linear", "server", "memory"), "enablement"),
    (("card", "tournament", "personas"), "enablement"),
    (("llm", "knowledge", "codemap"), "enablement"),
]


def _module_name(path: Path, root: Path) -> str:
    rel = path.relative_to(root)
    parts = list(rel.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _resolve_relative(current: str, module: str | None, level: int) -> list[str]:
    base = current
    for _ in range(level):
        base = base.rsplit(".", 1)[0] if "." in base else ""
    if module:
        return [f"{base}.{module}" if base else module]
    return [base] if base else []


def _imports(tree: ast.AST, current: str) -> set[str]:
    found: set[str] = set()
    top = current.split(".")[0]
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                if node.module:
                    found.update(_resolve_relative(current, node.module, node.level))
                else:
                    base = _resolve_relative(current, None, node.level)
                    pref = base[0] if base else ""
                    for a in node.names:
                        found.add(f"{pref}.{a.name}" if pref else a.name)
            elif node.module and node.module.split(".")[0] == top:
                found.add(node.module)
        elif isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] == top:
                    found.add(a.name)
    return found


def _value(name: str, summary: str) -> dict:
    vt = "enablement"
    for keys, t in _VALUE_TYPE:
        if any(k in name for k in keys):
            vt = t
            break
    short = name.split(".")[-1]
    return {
        "value_statement": f"(proposed) {summary or short + ' capability'}",
        "value_type": vt,
        "status": "proposed",
        "owner": "unconfirmed",
    }


def scan_python(root: Path | str) -> dict:
    """Return {module_name: capability node dict} for every .py under root."""
    root = Path(root)
    modules: dict[str, dict] = {}
    for py in sorted(root.rglob("*.py")):
        if "__pycache__" in py.parts:
            continue
        name = _module_name(py, root)
        if not name:
            continue
        try:
            tree = ast.parse(py.read_text())
        except SyntaxError:
            continue
        doc = ast.get_docstring(tree) or ""
        summary = " ".join(doc.strip().splitlines()[0].split()) if doc else ""
        funcs, classes, entry = [], [], []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                funcs.append(node.name)
                if node.name == "main" or node.name.startswith(("cmd_", "run_", "build_parser")):
                    entry.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
        modules[name] = {
            "id": name.replace(".", "-"),
            "name": name,
            "path": str(py),
            "summary": summary,
            "funcs": funcs,
            "classes": classes,
            "entrypoints": entry,
            "tags": [name.split(".")[-1]],
            "_imports": _imports(tree, name),
        }

    names = set(modules)
    for m in modules.values():
        m["depends_on"] = sorted({i for i in m["_imports"] if i in names and i != m["name"]})
    for n, m in modules.items():
        m["used_by"] = sorted(x for x in names if n in modules[x]["depends_on"])
        m["ref_count"] = len(m["used_by"])
        m["type"] = "code-entrypoint" if m["entrypoints"] and not m["used_by"] else "code-capability"
        m["value"] = _value(n, m["summary"])
        del m["_imports"]
    return modules


# ------------------------------------------------------------------ Foam render

def _frontmatter(node: dict) -> str:
    fm = [
        "---",
        f"id: {node['id']}",
        f"title: {node['name']}",
        f"type: {node['type']}",
        f"tags: [{', '.join(node['tags'])}]",
        f'summary: "{node["summary"].replace(chr(34), chr(39))}"',
        f"ref_count: {node['ref_count']}",
        f"source: {node['path']}",
        "status: proposed",
        "---",
    ]
    return "\n".join(fm)


def _note(node: dict) -> str:
    out = [_frontmatter(node), "", f"# {node['name']}", ""]
    if node["summary"]:
        out += [f"> {node['summary']}", ""]
    kind = "Entry point" if node["type"] == "code-entrypoint" else "Capability"
    out.append(f"**{kind}** · used by {node['ref_count']} module(s) · "
               f"{len(node['classes'])} class(es) · {len(node['funcs'])} function(s)")
    out += ["", "## Business value (proposed — confirm me)",
            f"- {node['value']['value_statement']}  "
            f"_(type: {node['value']['value_type']} · status: {node['value']['status']})_"]
    if node["classes"]:
        out += ["", "## Classes", ", ".join(f"`{c}`" for c in node["classes"])]
    if node["funcs"]:
        shown = node["funcs"][:12]
        more = "" if len(node["funcs"]) <= 12 else f" … (+{len(node['funcs']) - 12})"
        out += ["", "## Functions", ", ".join(f"`{f}`" for f in shown) + more]
    if node["entrypoints"]:
        out += ["", "## Entry points", ", ".join(f"`{e}`" for e in node["entrypoints"])]
    if node["depends_on"]:
        out += ["", "## Depends on", " ".join(f"[[{m.replace('.', '-')}]]" for m in node["depends_on"])]
    if node["used_by"]:
        out += ["", "## Used by", " ".join(f"[[{m.replace('.', '-')}]]" for m in node["used_by"])]
    out.append("")
    return "\n".join(out)


def _mermaid(modules: dict) -> str:
    lines = ["```mermaid", "graph LR"]
    for m in modules.values():
        short = m["name"].split(".")[-1]
        lines.append(f"  {m['id']}([{short}])")
    for m in modules.values():
        for d in m["depends_on"]:
            lines.append(f"  {m['id']} --> {d.replace('.', '-')}")
    lines.append("```")
    return "\n".join(lines)


def _index(modules: dict) -> str:
    ranked = sorted(modules.values(), key=lambda m: (-m["ref_count"], m["name"]))
    out = [
        "---", "id: index", "title: Catfish — Codebase Map of Content", "type: moc", "---", "",
        "# Catfish — Codebase Map of Content", "",
        "A **logic map** of the repo, organized by capability (what the code does), not file tree. "
        "Each node is a module-level capability; edges are `depends-on`. "
        "Open this folder in VS Code with the **Foam** extension for the interactive graph "
        "(the static graph below renders anywhere).", "",
        "**Two layers:** this is the *engineer* dependency view. The *PM* business-capability view "
        "is in [[business]].", "",
        "## Dependency graph", "", _mermaid(modules), "",
        "## Capabilities (by load-bearing rank)", "",
    ]
    for m in ranked:
        tag = " ⚙️ entry" if m["type"] == "code-entrypoint" else ""
        out.append(f"- [[{m['id']}]] — {m['summary'] or m['name']} _(used by {m['ref_count']}){tag}_")
    out += ["", "---",
            "_Structure is extracted deterministically (stdlib `ast`). Business-value lines are "
            "**proposals**, not facts — confirm them. Catfish mapped itself with `catfish map src`._", ""]
    return "\n".join(out)


def _business(modules: dict) -> str:
    """PM-facing layer: capabilities grouped by the kind of value they protect (two-layer map,
    Understand-Anything style). Distinct from the engineer dependency graph in index.md."""
    buckets: dict[str, list] = {}
    for m in modules.values():
        buckets.setdefault(m["value"]["value_type"], []).append(m)
    order = ["revenue", "retention", "risk", "compliance", "cost", "enablement"]
    types = [t for t in order if t in buckets] + [t for t in buckets if t not in order]

    mer = ["```mermaid", "graph LR", "  user([Stakeholder / PM])"]
    for t in types:
        mer.append(f"  {t}[[{t.title()}]]")
        mer.append(f"  user --> {t}")
        for m in sorted(buckets[t], key=lambda x: -x["ref_count"]):
            mer.append(f"  {t} --> {m['id']}({m['name'].split('.')[-1]})")
    mer.append("```")

    out = ["---", "id: business", "title: Catfish — Business Capability Map", "type: moc", "---", "",
           "# Catfish — Business Capability Map", "",
           "PM-facing view: what each capability is *for*, grouped by the kind of value it protects. "
           "Pairs with the engineer view in [[index]]. **Business-value lines are proposals — confirm them.**",
           "", "## Value flow", "", "\n".join(mer), "", "## Capabilities by value"]
    for t in types:
        out.append(f"\n### {t.title()}")
        for m in sorted(buckets[t], key=lambda x: -x["ref_count"]):
            out.append(f"- [[{m['id']}]] — {m['value']['value_statement']}")
    out.append("")
    return "\n".join(out)


def render_foam(modules: dict, out_dir: Path | str, catfish_dir: Path | str = ".catfish") -> int:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for node in modules.values():
        (out_dir / f"{node['id']}.md").write_text(_note(node))
    (out_dir / "index.md").write_text(_index(modules))
    (out_dir / "business.md").write_text(_business(modules))

    catfish_dir = Path(catfish_dir)
    catfish_dir.mkdir(parents=True, exist_ok=True)
    with (catfish_dir / "_code_index.jsonl").open("w") as fh:
        for node in modules.values():
            fh.write(json.dumps({
                "id": node["id"], "type": node["type"], "summary": node["summary"],
                "tags": node["tags"], "ref_count": node["ref_count"],
                "depends_on": node["depends_on"], "value": node["value"],
            }) + "\n")
    return len(modules) + 2  # per-module notes + index (engineer) + business (PM)
