---
name: study-guide-builder
description: Turns study resources (PDF, lecture slides, textbook chapter, notes, transcripts, links) into ONE structured, interactive HTML study guide for university-level learners - a dependency-ordered roadmap, topic-by-topic explanations with inline SVG diagrams, real-life examples, memory tricks, pause-and-predict prompts and worked examples, an end-of-topic quiz and practice task for every topic, flashcards, a printable cheat sheet and a coverage checklist. Use this whenever the user shares material and wants to study, learn, revise, summarise into notes, make a study guide, make flashcards or a quiz from it, "teach me this", or prepare for an exam - even if they never say "HTML" or "interactive".
---

# Study guide builder

Act as the best teacher the student could have: read the resources, decide what must be learned first and why, then produce a single self-contained interactive HTML file they can study from, with diagrams, quizzes, practice and flashcards. The file works offline in any browser and remembers progress.

Default audience: **university / undergraduate (18+)**. Use precise terminology and real depth; explain it clearly rather than simplifying it away. If the user states a different level, adapt the language, pacing and difficulty (the structure stays the same).

## What every guide contains
1. **Study roadmap**: topics in the best learning order, each with "why this comes here" and what it builds on, plus a progress tracker.
2. **Topics** (4-10), each with: objectives; explanation built from a big idea, real-life example, memory trick, tables and **inline SVG diagrams** (clickable where useful); **pause-and-predict** prompts; **worked examples** revealed step by step for quantitative/technical content; an **end-of-topic quiz** (4-6 mixed questions with instant feedback and explanations, score at the end); one **practice task** (interactive when the subject allows).
3. **Flashcards** for the whole guide (flip, "Got it / Still learning", shuffle, filter, re-study the misses).
4. **One-page cheat sheet** (printable).
5. **Coverage checklist**: every section of the source mapped to where the guide covers it.
Progress ticks, quiz scores and flashcard piles are saved in the browser. There is no glossary section, "common mistakes" section or final mock test unless the user asks for them (a `callout warn` inside a topic is fine where a real misconception exists).

## Workflow

### 1. Gather and read the resources completely
Read every attached/linked resource in full (use the pdf-reading / file-reading / pptx / docx skills or WebFetch as appropriate; for images or scans, view them). If the user named a topic but attached nothing, research it from authoritative sources first (WebSearch/WebFetch) and say which sources you used. Ask one short question only if something blocks you (unreadable file, unclear which of several resources matters most); otherwise proceed.

### 2. Make the source inventory, then the flow
Follow `references/teaching-playbook.md` sections 1-2: list every heading/concept in the source, then order into 4-10 topics by dependency (what must be understood first). Tell the user the topic order in a few lines as you start (do not wait for approval), then continue. Quick wins: a short resource may only need 3-4 topics, a whole textbook chapter 6-8; a whole book or course should be split into several guides (one per part/week) rather than one enormous file, so propose the split.

### 3. Write the content folder
Create a folder (e.g. `<name>-content/`) following `references/content-format.md`: `meta.json`, one `topics/NN-slug.html` + `.json` pair per topic, `cheatsheet.html`, `coverage.json`, and `overview.html` when there are four or more topics. Read `references/teaching-playbook.md` (how to teach, write quizzes/tasks/cards) and `references/diagram-patterns.md` (SVG classes and patterns) before writing. Write topic by topic so you can keep quality high; for big guides, draft the topics in order and keep a running list of terms already introduced so later topics reuse them.

Non-negotiables, because they are what the student relies on:
- **Cover everything in the resources**, in the resources' terminology, and stay faithful to them (the playbook says how to add clarification without contradicting).
- **Diagrams wherever a process, structure, relationship or comparison is explained**: at least one per topic.
- **Every topic ends with a quiz and a practice task** (or a `task: null` with a reason when a task would be filler).
- **Every number in examples and quizzes is computed and double-checked.**

### 4. Build, validate, look
```bash
python3 scripts/build_doc.py <content-dir> <out>/<name>-study-guide.html
python3 scripts/smoke_test.py <out>/<name>-study-guide.html --shots <out>/shots
```
The builder fails on structural errors (broken JSON, bad quiz answers, malformed SVG, unclosed tags) and warns about missing diagrams / predict boxes / examples / memory tricks: fix warnings rather than ignoring them. The smoke test opens the file in headless Chrome, clicks through quizzes, tasks, diagrams and flashcards, and fails on any JS error. Then **look at the screenshots** (every topic's PNG plus the phone view, using Read on the PNGs; diagrams are where text overflows and labels collide) and fix clipped diagram text, overlapping labels or empty-looking sections. If Playwright or Chrome is missing, `pip install playwright` or skip the smoke test and say so; never skip the builder.

### 5. Deliver
Send the single `.html` file to the user with the available file-delivery tool (SendUserFile / present_files), and also save it to their folder if they are linked to one. If the user asked for a shareable link and an artifact tool is available, publish the same file as an artifact instead. Finish with: topic count, what is in it (quiz/task/flashcard counts from the builder), anything left out and why (from the coverage checklist), and one next step (e.g. "tell me which topics felt thin and I'll expand them").

## Things that go wrong
- **Source order is not learning order.** Slides often introduce notation before motivation; re-order and explain in the roadmap.
- **Text-heavy topics with no pictures.** Reread the topic: what is a process, structure or comparison? Draw it.
- **Quizzes that test memory of the page.** Ask "why" and "what happens if" instead.
- **SVG text overflowing boxes.** 7.5px per character at 14px; keep labels short and put detail in `data-info`.
- **Overlong guides.** If a topic runs past ~25 minutes of reading, split it.
- **Inventing content.** If the source is thin on something, say so in the topic rather than padding with unverified facts.
- Math-heavy material: set `"math": true` in `meta.json` for KaTeX (needs internet in the browser) or keep to Unicode/`<sup>`/`<sub>`; tell the user which you chose.

## Files in this skill
- `assets/template.html`: the interactive shell (styles + behaviour). Do not hand-edit per guide; improve it here if a feature is missing.
- `scripts/build_doc.py`: validates content and assembles the guide.
- `scripts/smoke_test.py`: headless-browser check + screenshots.
- `references/content-format.md`: every file, field and HTML component.
- `references/teaching-playbook.md`: how to structure, teach, quiz and review.
- `references/diagram-patterns.md`: SVG classes and diagram patterns.
- `examples/mini/`: a complete small guide (2 topics) showing every component; copy its structure.
