# Teaching playbook

How to turn raw resources into something a university student can learn from. Read this before structuring and again before writing each topic.

## 1. Build the source inventory first
Read every resource completely (PDF/slides/doc/notes/transcript/links). Before writing anything, list **every heading, sub-heading, definition, theorem, formula, procedure, example and named concept** in the source. This list becomes `coverage.json` and is the guarantee that nothing is skipped. If the source is long, work through it in chunks and keep the list in a scratch file. If it is images or scanned pages, read them visually and transcribe the headings.

When several resources cover the same subject, merge them: one topic can cite several sources, and where they disagree, say so inside the topic.

## 2. Order the material as a learning flow (not the order of the source)
1. For each concept ask: *what must the student already understand to understand this?* Draw the dependency graph in your head or in notes.
2. Order topologically: foundations and vocabulary first, then mechanisms, then combinations and applications, then edge cases and extensions.
3. Group into **4-10 topics**, each digestible in roughly 10-25 minutes. Split a topic that needs more than ~25 minutes or more than ~5 new ideas; merge ones that are thin.
4. Put the "why do we care" at the start of the first topic, and the integrative/applied material last.
5. For each topic write `why` ("why here, why now", which feeds the roadmap) and `needs` (the earlier topics it builds on).
If the source's own order already follows this flow, keep it. If it is e.g. alphabetical, historical-but-confusing, or has forward references, re-order and say so in the roadmap `why` lines.

## 3. Teach each topic like the best lecturer you can imagine
- **Open with the big idea** in 1-3 sentences (`callout idea`): what this topic lets you do or understand and why it matters.
- **Intuition before formalism.** Give the picture, the example or the analogy first, then the precise definition and notation, then the edge cases. University students need the precision too, so keep correct terminology and state definitions exactly; introduce each key term once, in `<dfn>`.
- **One new idea at a time**, each followed by something that uses it (example, calculation, diagram).
- **Concrete, then general.** Use specific numbers and cases before the general rule.
- **A real-life example** (`callout example`) that a student could picture. It must be accurate, not a stretch; skip a forced analogy in favour of a plain concrete case.
- **A memory trick** (`callout memory`): a mnemonic, a rhyme, a vivid image or a "same key, same slot" slogan. Make it genuinely help recall the *idea*, not just a list; if the topic has a list of items to remember, an acronym is fair.
- **Pause-and-predict** (`.predict`): 1-3 per topic, placed *before* the thing is explained, where a student can reason their way to the answer or hold a common misconception. The answer should explain the reasoning, not just give a result.
- **Worked examples** (`.worked`) for anything quantitative, procedural or algorithmic: show each step with the reason for it. Pick numbers that make the point (e.g. an example where a collision/edge case actually happens). Verify every calculation.
- **Diagrams everywhere they help** (see `diagram-patterns.md`): any process, structure, cycle, hierarchy, relationship, comparison, graph or timeline. Aim for at least one per topic. A diagram should *carry* information the text refers to, not decorate. Say what to notice in the caption.
- **Tables** for comparisons of 2+ things across 2+ criteria.
- **Link back and forward** ("this is the collision problem from topic 1") so topics read as a single story.
- Include `callout warn` for the misconceptions students most often hold, but only where one exists.
- **Stay faithful to the source.** Teach what the resource says, with its notation and its emphasis. You may add short clarifications, intuition or an example beyond the source, but never contradict it silently; if you add substantive outside facts, mark them ("Beyond the notes: ..."). Do not invent numbers, citations, dates or quotations. If the source seems wrong or ambiguous, flag it in the topic instead of picking silently.
- Tone: warm, direct, no waffle; talk to the student ("you"). Short paragraphs. Don't pad.

## 4. Quizzes (4-6 questions per topic)
- Test **understanding**, not trivia: prefer "why", "what happens if", "which of these is true", "compute / predict" over "what is the name of".
- Mix types: at least one `predict` or calculation-style, one `tf`, and a `multi` when a topic has several properties. Order from recall to application.
- Wrong options should be **plausible**: each reflects a real misconception or a common slip (off-by-one, sign error, swapped terms). No joke answers, no "all of the above" unless `fixed`.
- `explain` always says why the right answer is right and why the most tempting wrong one fails. 2-4 sentences.
- Cover every major idea of the topic across the questions; do not ask about things the topic did not teach.
- Compute any numeric answer twice.

## 5. Practice task: pick the type from the subject
| Subject kind | Good task |
|---|---|
| Maths, physics, engineering, stats, finance | `reveal`: a problem like the worked example but with new numbers, 2-3 progressive hints, full solution |
| Programming, algorithms | `reveal`: write/trace/fix code (put the snippet in `<pre><code>`), or `order` for algorithm steps, or `fill` for completing a code line |
| Sciences with processes (biology, chemistry, earth) | `order` (a pathway), `match` (structure-function), `sort` (classify) |
| Humanities, law, business, social science | `sort` (classify cases/concepts), `match` (term-meaning, event-consequence), or `reveal` with a short case study + model answer |
| Languages | `fill` (grammar), `match` (vocabulary) |
| Definitions-heavy theory | `fill` with key terms |
Make the task **active and slightly harder than the quiz**: apply, not recall. If a topic is purely introductory/overview and no task would be more than busywork, set `task` to `null` and give the reason; this is better than filler.

## 6. Flashcards (4-8 per topic)
- One idea per card. Front = a question or cue; back = a short, complete answer (1-3 lines).
- Mix kinds: definition, "why", "what happens if", compare/contrast, formula with when to use it, a tiny calculation, process-step recall.
- Phrase fronts so there is exactly one right answer. Avoid "list everything about X".
- Cover every key term and formula from the topic. Add a few cross-topic cards in `cards.json` when relationships matter.

## 7. Cheat sheet
Everything a student would want on one page the night before: definitions in a line, formulas with conditions, the key comparison table, the process in 4-6 steps, the 3-5 most common mistakes or "remember" lines. Must fit one A4 page printed.

## 8. Final checks before delivering
1. Coverage: reopen the source inventory; every item is in `coverage.json` as full/brief/skipped-with-reason.
2. Accuracy: recompute every number in examples and quizzes; re-read each definition against the source.
3. Build with `build_doc.py` (zero errors; read each warning) and run `smoke_test.py --shots`. Open at least one topic screenshot and one phone screenshot and look for clipped diagram text, overflow, empty sections.
4. Order: read the roadmap `why` lines top to bottom; do they tell a coherent story?
