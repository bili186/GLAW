# Design

<!-- impeccable:design-schema 1 -->

## World

**A white gallery wall, and a proof that assembles itself.** The page opens on a fixed 1440 × 900
stage: twelve prints lie in a pile under a wide, flat scanning frame. As the visitor scrolls, the
frame opens out, the prints travel to their own places on the wall, and four annotations appear in
the left margin — one for each reading of the same search. The title never moves; it sits at the
lower left of the stage, a caption to the picture that is being made.

Nothing is skeuomorphic. The paper is white, the ink is black, the rules are hairlines, and the only
saturated colour is the logo's cyan, used where a selection is actually being made.

## Palette

| Token | Value | Role |
|---|---|---|
| `--paper` | `#FFFFFF` | the wall |
| `--paper-2` | `#F7F7F5` | command block, quiet fills |
| `--ink` | `#111111` | headings, body emphasis |
| `--ink-2` | `#3A3A38` | running copy |
| `--muted` | `#75756F` | annotations, metadata, captions |
| `--rule` | `#E6E6E2` | section rules, table rows |
| `--accent` | `#0284C7` | the selection frame and handles, hit brackets |
| `--accent-ink` | `#0B5C86` | cyan that carries small text: links, R@1, labels |

Cyan is the only hue and it always means *selected*. Everything else is black, grey or white.

## Type

One family: **Times New Roman** (`Times`, `Liberation Serif`, `Tinos`, `serif`). No webfont is
loaded; the static output ships no font binary.

- **Display:** 50px on the stage, `clamp(2.1rem, 4.6vw, 3.3rem)` in sections, `line-height` 1.0–1.04,
  tracking `-0.015em`. Title, section names, the citation stamp.
- **Body:** 17px / 1.65 for mechanism copy, captions and notes; 15px for query captions.
- **Data:** the same family at 11px, uppercase, `0.12em` tracking — frame numbers, metric headers,
  metadata. Separated by size, tracking and colour, never by family.

Emphasis inside the title is italic, the way an editorial page marks a word — not a second colour.

## Layout

The opening is a 1440 × 900 stage scaled by `min(vw / 1440, vh / 900)` and centred, so every screen
sees the same composition, letterboxed when the aspect ratio differs. The scroll length is 240vh;
`p` runs 0 → 1 and every element reads from it.

The title sits at `120, 452`, the byline and actions beneath it, the four annotations in the left
margin at `120, 104 → 430`. The prints live on the right: a pile around `625–967 × 65–495` at rest,
four columns from `690` to `1428` at the end. Sections below use a 1180px measure and are numbered
`01`–`05`.

## Marks and motion

- **Scan frame:** `400, 183, 789 × 193` at rest → `412, 261, 1151 × 601` at the end, eight square
  handles, fading out between `p = 0.32` and `0.62`.
- **Prints:** each has its own `from`/`to` box, z-layer and fade. Rotation is set by depth
  (`z ≥ 12 → 8°`, `z ≥ 8 → 4.5°`, `z ≥ 4 → 1.8°`, else `-3°`). Opacity is
  `fade × 0.95 → 1` over `p = 0.06 → 0.88`.
- **Annotations:** leader lines fade in at `p = 0.55 → 0.95`, labels at `p = 0.86 → 1`. Hovering a
  label or a print after `p = 0.85` keeps its group in colour and takes the rest to 30% grey.
- **Develop:** the twenty retrieval frames still rise 10px and fade in on load, once.

## Constraints worth remembering

- The stage is the only absolute coordinate system. Every opening value is authored in its 1440 × 900
  space, then transformed; never mix viewport units into it.
- Below 720px the opening becomes a normal page: the stage stops scaling, the twelve prints become a
  3 × 4 grid, the frame and leader lines are removed, and the annotations flow under the grid.
- `prefers-reduced-motion` paints the settled state and skips the scroll listener.
- `public/.nojekyll` must stay: Astro emits `_astro/`, which Jekyll would otherwise drop.
- `.frame--hit` is derived from the figure's own border colour, never asserted by hand. 10 of 20.

## Sources

- `assets/logo.svg` — the mark, its navy and its cyan (binding).
- `figs/fig_retrieval.png` — sliced into 20 frames by border colour; the twelve prints in the opening
  and the twenty frames in `01 Retrieval` are the figure's own truth, not a redrawing.
- The scroll grammar — a fixed stage, a scanning frame, prints that travel from a pile to a
  composition, and margin annotations that resolve last — follows StepFun's homepage opening,
  rebuilt here with our own assets and our own numbers.
