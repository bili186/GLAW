# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Astro (static site generator), source on a dedicated `site` branch, built output published to GitHub
Pages. Chosen by the user over hand-written static HTML; the repo itself stays a training/inference
codebase and does not carry the site build on `main`.

## Users

Primary: peers and reviewers in text-based person search (TBPS) and cross-modal retrieval. They
arrive during a review or a literature scan, with limited time, from a link in a manuscript or a
reference list. Their job: decide quickly whether the method is new, whether the reported numbers
are credible and comparable, and where the code is.

## Product Purpose

A project homepage for GLAW that lets a reviewer judge the method and the results in one screen,
then reach the code. Success means a reviewer can state the mechanism and the headline numbers
after a single viewport, and can find the repository without hunting.

## Positioning

GLAW trains a CLIP ViT-B/16 two-branch model in which a global branch and a token-selected local
branch are weighted by an image–text agreement score, with feature-denoising regularization and
EMA identity centroids on top. The mechanism a neighbouring method could not truthfully copy is the
agreement weighting itself: the per-pair reliability score drives both branch fusion and the
centroid pull, rather than serving as a fixed trade-off hyperparameter.

## Operating Context

Read on a desktop or laptop screen during review, often alongside the manuscript; also opened on a
phone from a chat link. The visitor may screenshot the results table. The code lives at
github.com/bili186/GLAW. Datasets are third-party and are not redistributed.

## Capabilities and Constraints

- Static pages only: no backend, no accounts, no telemetry, no external network requests at runtime.
- Shipped metrics are final and verbatim: CUHK-PEDES 74.27 / 89.80 / 94.15 / 66.36 / 50.06,
  ICFG-PEDES 65.82 / 81.24 / 86.77 / 39.22 / 7.66, RSTPReid 65.60 / 83.80 / 90.30 / 50.89 / 28.13
  (R@1 / R@5 / R@10 / mAP / mINP, text-to-image).
- The paper is not yet published: no DOI, no journal volume, no arXiv identifier exists.
- Only single-dataset (RSTPReid) retrieval examples are available as a figure; CUHK-PEDES and
  ICFG-PEDES example figures do not exist and must not be fabricated.

## Brand Commitments

- The mark in `assets/logo.svg` is binding: its form (selected visual patch, selected text token,
  GLAW wordmark) and its palette (navy `#132647`→`#0A1526` ground, cyan `#38BDF8` selection) are the
  identity. Extend the system; do not replace it.
- Author order and the corresponding-author star are fixed: Zhe Xu, Haoning Deng, Zhengye Zhang,
  Zhijie Yao, Kun Zhang*.
- No citation entry may appear while the paper is unpublished.

## Evidence on Hand

- `assets/logo.svg` — the identity mark.
- `figs/fig_retrieval.png` (+ `.pdf`) — real top-10 retrieval results on RSTPReid with correct/
  incorrect borders.
- The numbers above, from the reported experiments.
- The training and evaluation commands in the repository `README.md`.
- Absent, and not to be invented: a paper PDF, a venue, a DOI, comparisons against other methods
  that were not run here.

## Product Principles

1. The mechanism and its numbers speak first; decoration never delays them.
2. Show the retrieval working, not a claim that it works.
3. Every number on the page is one a reviewer could reproduce from the released code.
4. A reviewer's second question is "where is the code" — the answer is never more than one glance away.

## Accessibility & Inclusion

WCAG AA contrast for body and large text; the results table must remain readable on a phone without
horizontal scrolling of its primary columns; all figures carry text alternatives.
