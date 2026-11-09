#!/usr/bin/env python3
"""Open a built study guide in headless Chrome, click through its interactive parts, and report problems.

Usage:  python3 smoke_test.py GUIDE.html [--shots DIR]

Checks: no JavaScript errors, every topic's quiz/task rendered, quiz can be completed, tasks can be
solved, flashcards flip and can be marked, progress is saved, and (with --shots) screenshots of a
desktop and a phone-sized page are written so you can LOOK at the result (diagrams, overflow, dark mode).
Screenshots: desktop-full, dark top, one PNG per topic (look at ALL of them), phone top.
Requires: python3 -m pip install playwright (and a Chrome/Chromium; /usr/bin/google-chrome is used if present).
Exit code 1 if anything failed.
"""
import argparse, shutil, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("guide"); ap.add_argument("--shots")
    a = ap.parse_args()
    url = Path(a.guide).resolve().as_uri()
    problems, notes = [], []
    chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=chrome, args=["--no-sandbox"]) if chrome else p.chromium.launch(args=["--no-sandbox"])
        ctx = b.new_context(viewport={"width": 1280, "height": 900})
        page = ctx.new_page()
        errs = []
        page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
        page.on("console", lambda m: errs.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        page.goto(url); page.wait_for_load_state("load")

        topics = page.locator("section.topic").count()
        notes.append(f"{topics} topic sections")
        if topics == 0: problems.append("no topic sections found")
        # horizontal overflow
        if page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth + 2"):
            problems.append("page scrolls horizontally on desktop (something is too wide)")

        for i in range(topics):
            sec = page.locator("section.topic").nth(i)
            tid = sec.get_attribute("data-topic")
            if sec.locator(".mount-quiz .quiz").count() == 0: problems.append(f"{tid}: quiz did not render")
            # predict + worked + hotspots
            for _ in range(20):
                pb = sec.locator(".predict button:has-text('Reveal')")
                if pb.count() == 0: break
                pb.first.click()
            for _ in range(30):
                nb = sec.locator(".worked button:has-text('Reveal step')")
                if nb.count() == 0: break
                nb.first.click()
            hots = sec.locator("figure.diagram .hot")
            if hots.count():
                hots.first.dispatch_event('click')  # behaviour check; geometry is checked by eye in the screenshots
                if "Click" in sec.locator("figure.diagram .diagram-info").first.inner_text():
                    problems.append(f"{tid}: clicking a diagram hotspot did not update the info panel")
            # quiz: answer every question by trying options until we finish
            quiz = sec.locator(".mount-quiz .quiz")
            for q in range(12):
                if quiz.locator(".score-big").count(): break
                opts = quiz.locator("button.opt")
                if opts.count() == 0: problems.append(f"{tid}: quiz stuck without options"); break
                opts.first.click(); quiz.locator("button:has-text('Check answer')").click()
                if quiz.locator(".fb").count() == 0: problems.append(f"{tid}: no feedback shown after checking")
                nxt = quiz.locator("button:has-text('Next question'), button:has-text('See my score')")
                nxt.first.click()
            if quiz.locator(".score-big").count() == 0: problems.append(f"{tid}: quiz never reached the score screen")
            # task
            task = sec.locator(".mount-task .task")
            if task.count():
                for label in ["Show answers", "Show correct order", "Show solution"]:
                    b_ = task.locator(f"button:has-text('{label}')")
                    if b_.count(): b_.first.click(); break
                else: problems.append(f"{tid}: task has no reveal/show button")
                if task.locator(".done-tag").first.inner_text().strip() == "": problems.append(f"{tid}: task not marked done after showing the answer")
            sec.locator(".done-btn").click()

        # progress
        txt = page.locator("#progText").inner_text()
        notes.append("progress: " + txt)
        if not txt.startswith(f"{topics} of {topics}"): problems.append(f"progress text unexpected: {txt}")
        # flashcards
        page.locator("#flashcards").scroll_into_view_if_needed()
        total = page.locator(".fc-count").inner_text()
        for _ in range(60):
            if page.locator(".fc").count() == 0: break
            page.locator("button:has-text('Flip card')").click()
            if page.locator("button:has-text('Got it')").count() == 0: problems.append("flashcards: Got it button missing after flip"); break
            page.locator("button:has-text('Got it')").click()
        if page.locator(".fc-done").count() == 0: problems.append("flashcards: never reached round-complete screen")
        notes.append("flashcards: " + total)
        # persistence
        page.reload(); page.wait_for_load_state("load")
        if not page.locator("#progText").inner_text().startswith(f"{topics} of {topics}"): problems.append("progress was not restored after reload")

        # screenshots
        if a.shots:
            out = Path(a.shots); out.mkdir(parents=True, exist_ok=True)
            page.evaluate("localStorage.clear()"); page.reload(); page.wait_for_load_state("load")
            page.screenshot(path=str(out / "desktop-full.png"), full_page=True)
            page.emulate_media(color_scheme="dark"); page.reload(); page.wait_for_load_state("load")
            page.screenshot(path=str(out / "desktop-dark-top.png"))
            for i in range(topics):
                page.locator("section.topic").nth(i).screenshot(path=str(out / f"topic-{i+1}.png"))
            m = b.new_context(viewport={"width": 390, "height": 800}, is_mobile=True).new_page()
            m.goto(url); m.wait_for_load_state("load")
            if m.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth + 2"):
                problems.append("page scrolls horizontally on a phone-sized screen")
            m.screenshot(path=str(out / "phone-top.png"))
            notes.append(f"screenshots in {out}")
        b.close()
    errs = [e for e in errs if "favicon" not in e and "ERR_INTERNET" not in e and "net::" not in e]
    problems += errs
    print("\n".join(notes))
    if problems:
        print("\nPROBLEMS:"); [print(" -", x) for x in problems]; sys.exit(1)
    print("\nSmoke test passed: no JS errors, all interactive parts work.")

if __name__ == "__main__":
    main()
