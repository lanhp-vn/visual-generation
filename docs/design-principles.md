# Design principles

Five principles distilled from operator review of real VISEMI deliverables. They apply to every
generator in this repo and to any hand-authored visual built alongside them: slides, one-pagers,
posters, reports, handbooks, social posts.

They exist because the brand tokens and the deterministic lint answer *is this on-brand*, and say
nothing about *is this any good*. A visual can pass every automated check and still be sent back. The
rejections that produced these principles were never about colour or font; they were about legibility,
density, honesty, and care.

## 1. Legibility beats cleverness

A graphic that has to be explained has failed, however elegant the idea behind it.

Two devices were rejected for exactly this. A funding gap drawn as a full bar against a deliberately
empty bar was clever, and read as missing data rather than as "nobody pays for this". A cohort drawn
as a grid of one cell per person was an honest unit chart, and read as decoration. Both were replaced
with conventional forms carrying explicit labels, and both landed immediately.

The test is not whether the idea is defensible. It is whether a reader who is skimming, and who has
no stake in your reasoning, gets it in about two seconds. When someone asks what a graphic means,
that is the finding. Redraw it; do not add a caption explaining it.

Prefer forms readers already know: bar, stacked bar, funnel, Gantt, dot plot on a shared axis, a
timeline that looks like a timeline. Save invention for the arrangement, not the encoding.

## 2. Fill the canvas; hold the frame

Empty space inside a fixed-size page reads as unfinished, not as restraint. This is the single most
common reason a page gets sent back, and it is invisible to any automated check, because a page that
underfills passes every one of them.

The discipline is asymmetric, and the asymmetry is the point:

- **Margins are rigid.** Identical on every page, no exceptions. Consistency in the frame is what
  makes a set of pages feel like one document.
- **Inside the frame, be generous.** If content stops well short of the bottom, enlarge marks, type,
  row heights and chart dimensions until it does not. Scaling up beats leaving a hole.

When a page still cannot be filled honestly, the problem is the content, not the layout: merge it with
a neighbour. Conversely, a page that cannot be squeezed should split. Page count follows the argument,
so combine aggressively and let each page have exactly one job.

## 3. Real content, or nothing

A placeholder is worse than an absence, because it draws the eye and then disappoints it.

Coloured circles holding someone's initials where a photograph should be were rejected outright; a
plain text name would have been better. The same logic runs through the rest of the work: if a number
is strong on its own, print the number rather than wrapping it in an illustration to make it look like
a graphic. If a fact is missing, ask for it. Never invent a plausible line item to balance a panel,
which in a funder document is the most damaging failure available.

Decoration added to fill space is the thing this principle exists to prevent. Filling space is
principle 2's job, and it is done by enlarging real content.

## 4. Alignment is how care becomes visible

Nobody consciously notices correct alignment. Everybody notices its absence, and reads it as
carelessness about everything else in the document.

The details that were corrected one by one all belong to this single idea: columns of unequal content
ending at the same baseline, every logo in a wall at one size, faces cropped consistently across a row
of portraits, a heading sitting beside its icon rather than under it, a specific label held to one
line and another to two.

Two habits follow. Prefer a rule that holds automatically over a hand-tuned value, because a measured
gap breaks the moment the text rewraps while a stretch-to-fill keeps working. And when the operator
asks for a specific line break, treat it as a real constraint: widen the container first, shorten the
text second, and shrink the type only as a last resort, since that breaks the type scale for one
element.

## 5. Tables are the last resort

Almost anything laid out as a table has a better visual form waiting.

A schedule becomes a timeline. A set of tiers becomes a proportional bar. A budget becomes a
two-tier allocation bar. A process becomes a diagram with real arrows. A set of dated commitments
becomes points on a shared axis. Reach for a table only when the content genuinely is a lookup grid
that readers will scan cell by cell.

This is not decoration for its own sake, which principle 3 forbids. A good chart carries the
comparison the table was only implying, which is why it is faster to read.

## The logo files are not a colour source

The logo artwork was drawn in a different set of hexes from `brand/tokens.json`, so a colour sampled out
of a logo file is off-brand even though it came from an official asset:

| Asset | Hexes in the artwork |
| ----- | -------------------- |
| `brand/logos/cat-canh-logo-color.svg` | `#242D8F`, `#1CD29B`, `#FFAE00` |
| `brand/logos/visemi-logo-color.svg` | `#002065`, `#242D8F`, `#26AA82` |
| `brand/tokens.json`, the palette to actually design in | navy `#001669`, green `#01B68B`, ink `#262538`, gold `#F5B433` |

None of the artwork hexes appear in `tokens.json`, so the brand lint will reject them and, more to the
point, the result will not sit beside anything already published. Two consequences: never eyedrop a logo,
and never recolour one to close the gap, since recolouring is explicitly forbidden by the "Color Change"
rule in the Cất Cánh Logo Guidelines. Use a supplied treatment (`-color`, `-white`) instead.

## Using these

They are ordered by how often they get violated, not by importance. Before calling a visual done, walk
them: is anything here going to need explaining, is the canvas used, is everything on the page real, does
it align, and is there a table that wants to be a picture.

Principle 2 in particular cannot be checked without looking. Render the output and read the pages.
