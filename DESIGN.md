# Design

<!-- impeccable:design-schema 1 -->

## World

**A contact sheet on a dark table.** The page is not a poster about a retrieval model; it is the
proof sheet a photographer would lay down after a shoot — frames in order, printed frame numbers,
and grease-pencil marks on the frames that are the person asked for. The visitor reads the result
before reading a single claim about the method.

The scene supplies every material: the room is dark navy (the same navy as the logo ground), the
sheet is cool paper, and the only saturated colour is the mark — the logo's cyan, used exactly where
the logo uses it, on the selected token.

## Palette

| Token | Value | Role |
|---|---|---|
| `--navy-800` | `#0A1526` | page ground, from the logo's outer ground |
| `--navy-700` | `#132647` | logo inner navy; used only inside the mark |
| `--sheet` | `#EDEFF2` | the proof sheet. Cool paper — deliberately not cream |
| `--sheet-ink` | `#0F1928` | print on the sheet |
| `--sheet-muted` | `#57677D` | printed annotations, 5.4:1 on the sheet |
| `--select` | `#38BDF8` | the logo cyan: marks, rules, code, links on navy |
| `--select-deep` | `#0284C7` | bracket strokes and the one accent word (3.5:1, graphic + large text) |
| `--select-ink` | `#0B5C86` | cyan that must carry small text: frame numbers, R@1 column (6.3:1) |

Cyan is the only hue. Everything else is navy, paper, or grey. Emphasis inside a table or a heading
is carried by weight and rule, never by a second accent colour.

## Type

One family, three sizes of voice: **Times New Roman** throughout (`Times`, `Liberation Serif`,
`Tinos`, `serif` as fallbacks). The sheet is a printed page, so its type is the type of a printed
page — no display grotesk, no mono, no webfont fetched at runtime.

- **Display:** the family at `clamp(2.1rem, 5.4vw, 4.05rem)`, leading `1.02`, tracking `-.012em`.
  The title and section names only.
- **Body:** the same family at `1.0625rem/1.6` for mechanism copy, captions and notes.
- **Data:** the same family, uppercase at `0.75rem` with `0.05em` tracking, for frame numbers,
  metrics, keys and commands. Separated by size, tracking and colour — not by family.

Hierarchy is size, weight and rule — no letterspaced eyebrow labels above headings.

## Layout

A 1240px sheet inside a dark ground, with a printed header band (mark left, run data right). The
title is flush left at display size, then byline, then the two actions, then the strips.

Frames sit in a 10-column grid, 5px gutters, reflowing to 5 columns below 720px so a frame is never
cut in half. Sections are numbered `01`–`04` in small uppercase type at the left of a rule; the
section name is the only thing in display size on that line.

## Marks and motion

- **Select mark:** two cyan bracket corners on the frame — top-left and bottom-right, inset 3px. No
  border, no badge, no tint. On hover the print lifts 3px and the brackets grow; nothing else moves.
- **Develop:** frames rise 10px and fade in with a 34ms stagger, once, on load. This is the only
  authored motion; `prefers-reduced-motion` removes it.

## Constraints worth remembering

- Nothing is loaded from `/fonts/`. Times New Roman is a system face on macOS and Windows; Linux
  falls back to Liberation Serif or Tinos. `static` output therefore ships no binary font at all.
- `public/.nojekyll` must stay: Astro emits `_astro/`, which Jekyll would otherwise drop.
- `.frame--hit` is derived from the figure's own border colour, never asserted by hand. 10 of 20.

## Sources

- `assets/logo.svg` — the mark, its navy and its cyan (binding).
- `figs/fig_retrieval.png` — sliced into 20 frames by border colour; the marks on the page are the
  figure's own truth, not a redrawing.
- Binding donors named at roll time: the darkroom's sequential emergence (the develop sweep) and
  ligne claire's single line weight (every rule, box and bracket on the page is 1.25–2px).
