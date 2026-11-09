# Diagram patterns (inline SVG)

Diagrams are hand-written SVG inside `<figure class="diagram">`. They use CSS classes (not hex colours) so they follow light/dark mode. Always use `viewBox="0 0 720 H"` (width 720, height 150-420) so every diagram scales the same way.

## Classes
| class | for |
|---|---|
| `d-box` (+ `d2` teal, `d3` amber, `d4` rose, `d5` green, `plain` neutral) | rectangles / nodes: tinted fill + coloured outline. Add `rx="12"` for rounded corners |
| `d-solid1`..`d-solid5` | solid fills for bars, dots, areas |
| `d-line` (+ `d1`..`d5`, `thick`, `dash`) | plain lines, curves, graph plots |
| `d-arrow` (+ `dash`) | arrows: put on a `<path d="M x y H x2">`; the arrowhead is automatic |
| `d-axis` | graph axes with arrowhead; `d-grid` faint gridlines |
| `d-text` (+ `d-bold`), `d-small` (muted 12px), `d-accent` | text. Use `text-anchor="middle"` and `dominant-baseline="central"` for centred labels |
| `d-dot` | highlighted points |
| `hot` on a `<g>` | clickable: needs `data-title` and `data-info`; add `data-interactive` to the figure |

Never use `fill="#..."` / `stroke="#..."`; the builder warns because it breaks dark mode.

## Making text fit (the most common diagram bug)
Body text at 14px is about 7.5px per character; `d-small` about 6.5px. A box needs `width >= chars * 7.5 + 24`. Keep labels to 1-3 short words, move detail into `data-info` or the caption. Leave 40px between boxes for arrows. Check the screenshot from the smoke test: look for clipped or overlapping text.

## Patterns to copy
Choose the pattern from what is being explained:

| Explaining... | Pattern |
|---|---|
| a process / algorithm / pipeline | **Flow**: boxes left to right (or top to bottom) joined by `d-arrow`; decision = amber `d3` box with two labelled arrows |
| a cycle (water cycle, feedback loop, Krebs cycle) | **Cycle**: 4-6 boxes on a circle, curved arrows `<path d="M .. Q .. ..">` between them |
| a hierarchy / taxonomy / tree / org chart | **Tree**: parent on top, children below, straight `d-line`s |
| how ideas relate | **Concept map**: nodes with labelled `d-line`s; centre node `d-box`, others `d2`..`d5` |
| a structure with parts (cell, circuit, machine, memory layout) | **Labelled figure** with `hot` groups so each part explains itself on click |
| comparison of 2-3 things | **Side by side**: two columns of boxes with matching rows (a table is better if it is only text) |
| change over time / history | **Timeline**: one horizontal `d-line`, dots with year above and event below, alternating up/down |
| a relationship between quantities (supply-demand, graph of f(x), decay) | **Graph**: `d-axis` x and y, `d-grid`, curve as `<path class="d-line d1 thick">`, `d-dot` for key points, labels on axes |
| layers (network stack, atmosphere, organisation levels) | **Layers**: stacked full-width `d-box` rectangles, each a different colour |
| quantities (shares, results) | **Bars**: rects with `d-solid1`..; baseline `d-line`; value labels above bars |

### Flow skeleton
```html
<svg viewBox="0 0 720 140" role="img" aria-label="Three-step process">
  <g class="hot" data-title="Step 1." data-info="What happens here.">
    <rect class="d-box" x="20" y="35" width="180" height="70" rx="12"/>
    <text class="d-text d-bold" x="110" y="70" text-anchor="middle" dominant-baseline="central">Input</text></g>
  <path class="d-arrow" d="M200 70 H260"/>
  <g class="hot" data-title="Step 2." data-info="..."><rect class="d-box d3" x="264" y="35" width="192" height="70" rx="12"/>
    <text class="d-text d-bold" x="360" y="70" text-anchor="middle" dominant-baseline="central">Transform</text></g>
  <path class="d-arrow" d="M456 70 H516"/>
  <g class="hot" data-title="Step 3." data-info="..."><rect class="d-box d2" x="520" y="35" width="180" height="70" rx="12"/>
    <text class="d-text d-bold" x="610" y="70" text-anchor="middle" dominant-baseline="central">Output</text></g>
</svg>
```
### Graph skeleton
```html
<svg viewBox="0 0 720 320" role="img" aria-label="Demand falls as price rises">
  <path class="d-grid" d="M80 40 V260 M180 40 V260 M280 40 V260 M380 40 V260 M480 40 V260 M80 150 H520"/>
  <path class="d-axis" d="M80 260 H560"/><path class="d-axis" d="M80 260 V20"/>
  <text class="d-small" x="560" y="282" text-anchor="end">Quantity</text><text class="d-small" x="70" y="20" text-anchor="end">Price</text>
  <path class="d-line d1 thick" d="M100 50 L500 240"/><text class="d-text" x="505" y="244">Demand</text>
  <circle class="d-dot" cx="300" cy="145" r="7"/>
</svg>
```
### Cycle: place N boxes at angles; arrows as quadratic curves
Centre (360,150), radius 105: top (360,45), right (465,150), bottom (360,255), left (255,150); arrow from top to right `M400 60 Q455 70 462 112`. Draw arrows first, boxes after, so boxes sit on top.

## Hotspots
Any `<g class="hot">` is clickable: the template adds invisible wide hit areas around its lines, curves and text, so arrow-only or label-only groups work. Give a curve its own `hot` group with the label inside it, and keep neighbouring hotspots from overlapping much. `d-arrow` takes colour modifiers too (`d-arrow d2`).

## Interactivity rule of thumb
Use `hot` groups when a diagram has parts the student should explore (anatomy, architectures, flows with several steps). Skip them for simple graphs; the caption does the job.
