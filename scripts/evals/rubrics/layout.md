# Layout, spacing, and overflow (0-5)

Score whether the canvas is cleanly composed at its own fixed size, independent of theme (light or dark are equally valid backgrounds) and of kind (deck slide, social post, poster, banner, or document page).

- Everything fits inside the frame. Nothing overflows the edges, nothing is
  cut off, and no element overlaps another illegibly.
- Spacing is generous and consistent: even gutters between cards/columns,
  balanced margins, related items grouped and unrelated items separated.
- Elements are aligned to a clear grid; rows and columns line up.
- Visual hierarchy is clear: a dominant headline, then supporting content, then
  accents. The eye knows where to start.
- The layout suits the content (e.g. a stat grid for figures, columns for
  parallel items, a people row for profiles) and does not look empty or crammed.
- The dominant headline stays short enough to read as one gesture, roughly one to
  three lines. A long wrapped headline that fills a third of the canvas is a
  content problem, not a type-size problem.
- Shared elements line up across side-by-side items: card titles on one baseline,
  figures on another, any footer or call to action on a common line. Ragged
  baselines between neighbouring cards make an otherwise sound layout look broken.
- Composition is not relentlessly centred where the layout allows otherwise. A
  deliberate left-aligned or asymmetric structure usually reads more designed than
  everything stacked on the centre line, though centring is right for some kinds
  (a quote card, a title canvas).
- Vertical padding is optically balanced rather than mechanically identical; the
  space below a block often needs to be slightly larger than the space above it.

5 = cleanly composed, well spaced, fully contained, clear hierarchy. 3 = right structure with alignment or spacing issues. 0 = overflowing, cut off, overlapping, or badly misaligned.

Return "Unknown" if you cannot tell how the canvas is meant to be composed.
