#!/usr/bin/env python3
"""Assemble a self-contained interactive study guide (one HTML file) from a content folder.

Usage:
    python3 build_doc.py CONTENT_DIR OUTPUT.html [--template PATH] [--strict]

CONTENT_DIR layout (see references/content-format.md for every field):
    meta.json                 title, subtitle, level, source, accent, math, intro
    overview.html             optional: big-picture diagram of how the topics connect
    topics/NN-slug.html       explanation for topic NN (HTML fragment using the components)
    topics/NN-slug.json       title, minutes, why, needs, objectives, quiz, task, cards
    cards.json                optional: extra cross-topic flashcards
    cheatsheet.html           one-page summary (HTML fragment)
    coverage.json             source section -> where it is covered

Exit code 0 = built (warnings may be printed). 1 = errors (nothing written unless --force).
--strict turns warnings into errors.
"""
import argparse
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = HERE.parent / "assets" / "template.html"

errors, warnings = [], []


def err(where, msg):
    errors.append(f"ERROR   {where}: {msg}")


def warn(where, msg):
    warnings.append(f"warning {where}: {msg}")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "guide"


def load_json(path, required=True):
    if not path.exists():
        if required:
            err(path.name, "file is missing")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(path.name, f"invalid JSON ({e.msg} at line {e.lineno} col {e.colno})")
        return None


# ---------------------------------------------------------------- HTML checks
VOID = {"br", "hr", "img", "input", "meta", "link", "source", "wbr", "col", "area", "base", "embed", "track", "param"}
OPTIONAL_CLOSE = {"p", "li", "td", "th", "tr", "thead", "tbody", "tfoot", "option", "dt", "dd"}


class Balance(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.problems = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        names = [t for t, _ in self.stack]
        if tag not in names:
            self.problems.append(f"stray </{tag}> near line {self.getpos()[0]}")
            return
        while self.stack:
            t, line = self.stack.pop()
            if t == tag:
                break
            if t not in OPTIONAL_CLOSE:
                self.problems.append(f"<{t}> opened on line {line} was never closed")

    def finish(self):
        for t, line in self.stack:
            if t not in OPTIONAL_CLOSE:
                self.problems.append(f"<{t}> opened on line {line} was never closed")
        return self.problems


XML_SAFE = {"amp", "lt", "gt", "quot", "apos"}


def _entity_fix(m):
    name = m.group(1)
    if name in XML_SAFE:
        return m.group(0)
    return html.unescape(m.group(0))


def check_fragment(where, text, *, diagrams=False):
    if re.search(r"<script\b", text, re.I):
        err(where, "<script> is not allowed in content fragments (interactivity comes from the template)")
    if re.search(r"\son\w+\s*=", text, re.I):
        warn(where, "inline event handler attributes (onclick=...) are ignored/unsafe; use the built-in components")
    p = Balance()
    try:
        p.feed(text)
        p.close()
    except Exception as e:  # pragma: no cover
        err(where, f"HTML could not be parsed: {e}")
        return
    for prob in p.finish():
        err(where, prob)
    svgs = re.findall(r"<svg\b.*?</svg>", text, re.S | re.I)
    hardcoded = False
    for k, svg in enumerate(svgs, 1):
        fixed = re.sub(r"&([A-Za-z][A-Za-z0-9]*);", _entity_fix, svg)
        # '<' and '>' inside attribute values (e.g. data-info="H<sub>2</sub>O") are fine in HTML but not XML
        fixed = re.sub(r'="([^"]*)"', lambda m: '="' + m.group(1).replace("<", "&lt;").replace(">", "&gt;") + '"', fixed)
        try:
            ET.fromstring(fixed)
        except ET.ParseError as e:
            err(where, f"SVG #{k} is not well-formed XML: {e}")
        if "viewBox" not in svg:
            warn(where, f"SVG #{k} has no viewBox, so it will not scale")
        if re.search(r'(fill|stroke)="#[0-9a-fA-F]{3,8}"', svg):
            hardcoded = True
    if hardcoded:
        warn(where, 'SVG uses hard-coded colours (fill="#...") which break in dark mode; use the d-* classes instead')
    return svgs


# ---------------------------------------------------------------- data checks
def check_quiz(where, quiz):
    if not isinstance(quiz, list) or not quiz:
        err(where, "quiz must be a non-empty list (every topic needs a quiz)")
        return
    if len(quiz) < 4:
        warn(where, f"only {len(quiz)} quiz questions; aim for 4-6")
    if len(quiz) > 8:
        warn(where, f"{len(quiz)} quiz questions is long; aim for 4-6")
    types = set()
    for i, q in enumerate(quiz, 1):
        w = f"{where} quiz Q{i}"
        t = q.get("type")
        types.add(t)
        if t not in ("mcq", "tf", "multi", "predict"):
            err(w, f"unknown type {t!r} (use mcq, tf, multi, predict)")
            continue
        if not q.get("q"):
            err(w, "missing q")
        if not q.get("explain") or len(str(q["explain"])) < 25:
            warn(w, "explain is missing or too short; the explanation is where the learning happens")
        if t == "tf":
            if not isinstance(q.get("answer"), bool):
                err(w, "tf answer must be true or false (JSON boolean)")
            continue
        opts = q.get("options")
        if not isinstance(opts, list) or len(opts) < 3:
            err(w, "options must be a list of at least 3 choices")
            continue
        a = q.get("answer")
        if t == "multi":
            if not (isinstance(a, list) and a and all(isinstance(x, int) and 0 <= x < len(opts) for x in a)):
                err(w, "multi answer must be a list of valid option indexes")
            elif len(a) < 2:
                warn(w, "multi question with one correct answer; use mcq")
        else:
            if not (isinstance(a, int) and not isinstance(a, bool) and 0 <= a < len(opts)):
                err(w, "answer must be the index (0-based) of the correct option")
        texts = [str(o).strip().lower() for o in opts]
        if len(set(texts)) != len(texts):
            err(w, "duplicate options")
    if len(types) == 1 and len(quiz) >= 4:
        warn(where, "quiz uses only one question type; mix mcq, tf, multi and predict")


def check_task(where, task):
    if task is None:
        return
    if not isinstance(task, dict):
        err(where, "task must be an object or null")
        return
    t = task.get("type")
    w = f"{where} task"
    if not task.get("title"):
        warn(w, "missing title")
    if t == "reveal":
        if not task.get("prompt") or not task.get("solution"):
            err(w, "reveal task needs prompt and solution")
        if not task.get("hints"):
            warn(w, "reveal task has no hints; hints make a hard problem approachable")
    elif t == "fill":
        if len(re.findall(r"\[\[.+?\]\]", task.get("text", ""))) < 2:
            err(w, "fill task needs text with at least 2 blanks written as [[answer]] or [[answer|alt]]")
    elif t == "order":
        if not (isinstance(task.get("items"), list) and len(task["items"]) >= 3):
            err(w, "order task needs items: a list of at least 3 steps in the CORRECT order")
    elif t == "match":
        pairs = task.get("pairs")
        if not (isinstance(pairs, list) and len(pairs) >= 3 and all(isinstance(p, list) and len(p) == 2 for p in pairs)):
            err(w, "match task needs pairs: [[left, right], ...] with at least 3 pairs")
    elif t == "sort":
        cats, items = task.get("categories"), task.get("items")
        if not (isinstance(cats, list) and len(cats) >= 2):
            err(w, "sort task needs categories (2 or more)")
        elif not (isinstance(items, list) and len(items) >= 4 and all(isinstance(i, dict) and isinstance(i.get("cat"), int) and 0 <= i["cat"] < len(cats) and i.get("text") for i in items)):
            err(w, "sort task needs items: [{text, cat}] (at least 4) where cat indexes categories")
    else:
        err(w, f"unknown task type {t!r} (use reveal, fill, order, match, sort) or set task to null")


# ---------------------------------------------------------------- build
def build(content: Path, out: Path, template: Path, strict: bool, force: bool):
    meta = load_json(content / "meta.json") or {}
    title = meta.get("title")
    if not title:
        err("meta.json", "title is required")
        title = "Study guide"
    meta.setdefault("id", slug(title))
    accent = meta.get("accent", "#4f46e5")
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", accent):
        err("meta.json", "accent must look like #4f46e5")
        accent = "#4f46e5"

    tdir = content / "topics"
    json_files = sorted(tdir.glob("*.json")) if tdir.exists() else []
    if not json_files:
        err("topics/", "no topic files found (expected topics/01-name.json + topics/01-name.html)")

    topics, cards, svg_total, q_total, task_total = [], [], 0, 0, 0
    bodies = {}
    ids = []
    for jf in json_files:
        m = re.match(r"(\d+)", jf.stem)
        tid = f"t{int(m.group(1))}" if m else f"t{len(ids) + 1}"
        if tid in ids:
            err(jf.name, f"duplicate topic number -> id {tid}")
        ids.append(tid)
    for jf, tid in zip(json_files, ids):
        data = load_json(jf) or {}
        hf = jf.with_suffix(".html")
        if not hf.exists():
            err(hf.name, "matching .html explanation file is missing")
            body = ""
        else:
            body = hf.read_text(encoding="utf-8")
        where = jf.stem
        if not data.get("title"):
            err(jf.name, "title is required")
        if not data.get("objectives"):
            warn(jf.name, "no objectives (what the student can do after this topic)")
        if not data.get("why"):
            warn(jf.name, 'no "why" (why this topic comes at this point in the roadmap)')
        for n in data.get("needs", []):
            if n not in ids:
                err(jf.name, f"needs refers to unknown topic id {n!r}")
            elif ids.index(n) >= ids.index(tid):
                err(jf.name, f"needs {n!r} which does not come before this topic; fix the order")
        svgs = check_fragment(where + ".html", body) or []
        svg_total += len(svgs)
        if not re.search(r'<figure[^>]*class="[^"]*diagram', body):
            warn(where + ".html", "no diagram (<figure class=\"diagram\">); add one wherever a process, structure or relationship is explained")
        if 'class="predict"' not in body:
            warn(where + ".html", "no pause-and-predict box")
        if 'callout example' not in body:
            warn(where + ".html", "no real-life example callout")
        if 'callout memory' not in body:
            warn(where + ".html", "no memory-trick callout")
        if len(re.sub(r"<[^>]+>", " ", body).split()) < 150:
            warn(where + ".html", "explanation is very short (<150 words); does it really cover the source?")
        check_quiz(where, data.get("quiz"))
        q_total += len(data.get("quiz") or [])
        if "task" not in data:
            err(jf.name, 'task key is missing: give a task object, or "task": null (and "task_skip_reason") if no useful task exists')
        elif data["task"] is None:
            if not data.get("task_skip_reason"):
                warn(jf.name, "task is null without task_skip_reason")
        else:
            task_total += 1
        check_task(where, data.get("task"))
        tcards = data.get("cards") or []
        if len(tcards) < 3:
            warn(jf.name, f"only {len(tcards)} flashcards; aim for 4-8")
        for k, c in enumerate(tcards, 1):
            if not (c.get("front") and c.get("back")):
                err(jf.name, f"card {k} needs front and back")
            cards.append({"id": f"{tid}-c{k}", "topic": tid, "front": c.get("front", ""), "back": c.get("back", "")})
        topics.append({
            "id": tid, "title": data.get("title", where), "minutes": data.get("minutes"),
            "why": data.get("why", ""), "needs": data.get("needs", []), "objectives": data.get("objectives", []),
            "quiz": data.get("quiz") or [], "task": data.get("task"),
        })
        bodies[tid] = body

    extra = load_json(content / "cards.json", required=False)
    for k, c in enumerate(extra or [], 1):
        if not (c.get("front") and c.get("back")):
            err("cards.json", f"card {k} needs front and back")
        cards.append({"id": f"x-c{k}", "topic": c.get("topic", ""), "front": c.get("front", ""), "back": c.get("back", "")})

    # coverage
    coverage = load_json(content / "coverage.json", required=False)
    if coverage is None:
        warn("coverage.json", "missing; the coverage checklist is how you prove nothing from the source was skipped")
        coverage = []
    for k, c in enumerate(coverage, 1):
        if c.get("depth", "full") not in ("full", "brief", "skipped"):
            err("coverage.json", f"row {k}: depth must be full, brief or skipped")
        if c.get("depth") == "skipped" and not c.get("note"):
            warn("coverage.json", f"row {k} is skipped without a note explaining why")
        for w_ in (c.get("where") if isinstance(c.get("where"), list) else [c.get("where")]):
            if c.get("depth") != "skipped" and w_ not in ids:
                err("coverage.json", f"row {k}: where={w_!r} is not a topic id ({', '.join(ids)})")

    def frag(name, required):
        p = content / name
        if not p.exists():
            if required:
                warn(name, "missing")
            return ""
        t = p.read_text(encoding="utf-8")
        check_fragment(name, t)
        return t

    overview = frag("overview.html", False)
    cheat = frag("cheatsheet.html", True)
    intro = meta.get("intro", "")
    if intro:
        check_fragment("meta.json intro", intro)
        intro = f'<div class="card tint">{intro}</div>'

    if not topics:
        err("content", "nothing to build")

    # ---- topic sections
    parts = []
    n = len(topics)
    for i, t in enumerate(topics):
        mins = f" · ≈{t['minutes']} min" if t.get("minutes") else ""
        objs = "".join(f"<li>{o}</li>" for o in t["objectives"])
        obj_html = f'<div class="objectives"><b>After this topic you can:</b><ul>{objs}</ul></div>' if objs else ""
        nxt = ""
        if i + 1 < n:
            nxt = f'<a class="btn ghost" href="#topic-{topics[i + 1]["id"]}">Next: {html.escape(topics[i + 1]["title"])} →</a>'
        else:
            nxt = '<a class="btn ghost" href="#flashcards">On to the flashcards →</a>'
        parts.append(
            f'<section class="topic sec" id="topic-{t["id"]}" data-topic="{t["id"]}">\n'
            f'<header class="topic-head"><div class="kicker">Topic {i + 1} of {n}{mins}</div><h2>{html.escape(t["title"])}</h2></header>\n'
            f'{obj_html}\n<div class="topic-body">\n{bodies.get(t["id"], "")}\n</div>\n'
            f'<div class="mount-quiz" data-topic="{t["id"]}"></div>\n<div class="mount-task" data-topic="{t["id"]}"></div>\n'
            f'<div class="row no-print" style="margin-top:6px"><button class="btn ghost done-btn" data-topic="{t["id"]}" type="button">Mark topic complete</button>{nxt}</div>\n'
            f'</section>\n'
        )

    doc = {"meta": {k: meta.get(k) for k in ("id", "title", "subtitle", "level", "source")},
           "topics": [{k: v for k, v in t.items() if k != "objectives"} for t in topics],
           "cards": cards, "coverage": coverage}
    payload = json.dumps(doc, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--")

    head_extra = ""
    if meta.get("math"):
        head_extra = (
            '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">\n'
            '<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>\n'
            '<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>'
        )

    tpl = template.read_text(encoding="utf-8")
    rep = {
        "@@TITLE@@": html.escape(title), "@@SUBTITLE@@": html.escape(meta.get("subtitle", "")),
        "@@ACCENT@@": accent, "@@HEAD_EXTRA@@": head_extra, "@@INTRO@@": intro,
        "@@OVERVIEW@@": overview, "@@CHEATSHEET@@": cheat or "<p class='muted'>No cheat sheet provided.</p>",
        "@@TOPICS@@": "\n".join(parts), "@@DATA@@": payload,
    }
    # replace DATA last so user content containing "@@" markers can't be re-substituted
    out_html = tpl
    for k, v in rep.items():
        if k != "@@DATA@@":
            out_html = out_html.replace(k, v)
    out_html = out_html.replace("@@DATA@@", payload)

    for w in warnings:
        print(w)
    for e in errors:
        print(e)
    if errors and not force:
        print(f"\n{len(errors)} error(s); not writing {out}. Fix them and run again.")
        return 1
    if strict and warnings:
        print(f"\n--strict: {len(warnings)} warning(s) treated as errors; not writing {out}.")
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(out_html, encoding="utf-8")
    print(f"\nBuilt {out}  ({out.stat().st_size / 1024:.0f} KB)")
    print(f"  topics: {n}   quiz questions: {q_total}   practice tasks: {task_total}   flashcards: {len(cards)}   inline SVGs: {svg_total}   coverage rows: {len(coverage)}")
    print(f"  {len(warnings)} warning(s), {len(errors)} error(s)")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("content_dir")
    ap.add_argument("output")
    ap.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--force", action="store_true", help="write the file even if there are errors")
    a = ap.parse_args()
    sys.exit(build(Path(a.content_dir), Path(a.output), Path(a.template), a.strict, a.force))


if __name__ == "__main__":
    main()
