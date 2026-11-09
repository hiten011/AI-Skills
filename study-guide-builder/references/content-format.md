# Content format reference

The builder (`scripts/build_doc.py`) turns a content folder into one HTML file. Write the folder, run the builder, fix what it reports.

```
content/
  meta.json
  overview.html        (optional, recommended when there are 4+ topics: a diagram of how topics connect)
  topics/01-slug.html  + topics/01-slug.json     (one pair per topic; the number sets the order and the id: 01 -> "t1")
  cheatsheet.html
  coverage.json
  cards.json           (optional: extra cross-topic flashcards)
```

## meta.json
```json
{ "title": "Plain-text title", "subtitle": "Plain text", "level": "Undergraduate · Course name",
  "source": "Lecture 7 notes", "accent": "#4f46e5", "math": false,
  "intro": "<p>2-4 sentences: the big picture of the whole resource and how the topics fit together.</p>" }
```
`math: true` loads KaTeX from a CDN (needs internet) so `\( x^2 \)` and `$$ ... $$` render. Without it, write maths with `<sup>`, `<sub>`, Unicode and `<div class="formula">`. `accent` is any 6-digit hex; pick one per subject.

## topics/NN-slug.json
```json
{ "title": "Plain text (not HTML)", "minutes": 15,
  "why": "One or two sentences: why this topic comes at this point in the order.",
  "needs": ["t1"],
  "objectives": ["Starts with a verb: explain, compute, compare ...", "..."],
  "quiz": [ ... 4-6 questions ... ],
  "task": { ... } ,
  "task_skip_reason": "only when task is null",
  "cards": [ {"front": "...", "back": "..."} , ... 4-8 cards ... ] }
```
`needs` lists earlier topic ids only. `task` must be present: an object, or `null` when no genuinely useful task exists (say why in `task_skip_reason`). Strings in quiz/task/cards/why/objectives may contain inline HTML (`<code>`, `<sub>`, `<em>`). Escape a literal `&` as `&amp;` and `<` as `&lt;`.

### Quiz questions (4-6 per topic, mix the types)
| type | fields | notes |
|---|---|---|
| `mcq` | `q`, `options` (3-5), `answer` (index), `explain` | options are shuffled when shown; set `"fixed": true` if order matters ("both of the above") |
| `tf` | `q`, `answer` (true/false), `explain` | state a claim, not a question |
| `multi` | `q`, `options`, `answer` ([indexes], 2+), `explain` | "select all that apply"; graded all-or-nothing |
| `predict` | `q`, `options`, `answer`, `explain` | a scenario or small calculation: "what happens / what is the result?" |
`explain` is required and shows after every answer: say why the right answer is right and, when a tempting wrong option exists, why it is wrong.

### Practice task (one per topic, or null)
| type | fields | use for |
|---|---|---|
| `reveal` | `title`, `prompt` (HTML), `hints` ([..]), `solution` (HTML) | problems, derivations, short essays, coding, case analysis: student attempts, uses hints, then reveals the model solution |
| `fill` | `title`, `prompt`, `text` with `[[answer]]` or `[[answer\|alt\|alt]]` blanks | definitions, key terms, a worked calculation with numeric blanks (numbers match within 0.5%) |
| `order` | `title`, `prompt`, `items` (steps in the CORRECT order) | processes, algorithms, historical sequences, proofs. Shuffled on screen, drag or use arrows |
| `match` | `title`, `prompt`, `pairs` ([[left, right], ...]) | term-definition, cause-effect, formula-name. Right-hand side is plain text |
| `sort` | `title`, `prompt`, `categories` (["A","B"]), `items` ([{"text":"..","cat":0}]) where `cat` is the integer index into `categories` | classification: which items belong to which category |

## topics/NN-slug.html: components
Write plain HTML (`h3`, `h4`, `p`, `ul`, `ol`, `table`, `pre><code`, `dfn` for the first use of a key term, `<div class="formula">`). Do not write `<h2>` or `<h1>` (the builder adds the topic heading) and never `<script>`. Interactive behaviour is attached automatically to these:

```html
<div class="callout idea"><span class="label">Big idea</span><p>...</p></div>
<div class="callout example"><span class="label">Real-life example</span><p>...</p></div>
<div class="callout memory"><span class="label">Memory trick</span><p>...</p></div>
<div class="callout warn"><span class="label">Watch out</span><p>...</p></div>     <!-- also: note -->

<div class="predict">                       <!-- pause-and-predict: answer is hidden until the student guesses and clicks -->
  <div class="q">Question to think about first.</div>
  <div class="a"><p>The answer and the reasoning.</p></div>
</div>

<div class="worked">                        <!-- steps are revealed one at a time -->
  <div class="problem">The problem statement.</div>
  <ol class="steps"><li>Step 1 ...</li><li>Step 2 ...</li></ol>
</div>

<figure class="diagram" data-interactive>   <!-- data-interactive only if it contains .hot groups -->
  <svg viewBox="0 0 720 300" role="img" aria-label="what the diagram shows"> ... </svg>
  <figcaption>One line saying what to notice.</figcaption>
</figure>
<!-- inside the svg, clickable parts: <g class="hot" data-title="Name." data-info="Explanation shown when clicked."> ... </g> -->
```
See `diagram-patterns.md` for the SVG classes and ready-made patterns.

**Text inside SVG and attributes.** SVG is validated as XML, so write `&amp;` for `&` and `&lt;` for `<` in text. Named HTML entities (`&Delta;`, `&minus;`, `&eta;`) are accepted; Unicode characters (Δ, −, η) are simplest. In `data-info` / `data-title` you may put `<sub>`, `<b>`, `<code>` directly (they are rendered as HTML), but write a literal less-than as `&lt;`.

**Content that goes beyond the source.** When you add something the resource does not say (an extra worked number, a related fact), put it in `<div class="callout note"><span class="label">Beyond the notes</span>...</div>` so the student can tell source from supplement.

## cheatsheet.html
A fragment that fits one printed page. Wrap content in `<div class="cols"> ... </div>` for a two-column layout. Use `h3` headings, short bullets, one comparison table, the key formulas. No diagrams unless tiny.

## coverage.json
One row per heading/sub-heading/concept in the SOURCE (use the source's own wording):
```json
[ {"source": "2.1 Newton's first law", "where": ["t1"], "depth": "full"},
  {"source": "2.4 Historical background", "where": ["t1"], "depth": "brief", "note": "one paragraph in the intro"},
  {"source": "2.7 Proof of Noether's theorem", "where": [], "depth": "skipped", "note": "why it was left out (e.g. marked non-examinable)"} ]
```
`where` = topic ids. `depth` = `full`, `brief` or `skipped` (skipped requires a note).

## cards.json (optional)
`[{"topic": "t1", "front": "...", "back": "..."}]` for cards that span topics ("Compare X and Y across the guide"). `topic` may be "".

## Build and check
```
python3 scripts/build_doc.py content/ out/<name>-study-guide.html      # validates, then writes
python3 scripts/smoke_test.py out/<name>-study-guide.html --shots out/shots   # clicks everything in headless Chrome
```
The builder reports errors (it will not write) and warnings (missing diagram, no predict box, too-short quiz...). Treat warnings as a to-do list, not noise.
