# Flat-design fidelity (0-5)

Score how strictly the image follows a flat-design system. This dimension is opt-in (it is not in the default DIMENSIONS list; pass it explicitly to load_rubrics/grade when the active brand mandates flat design). It is brand-agnostic: palette and font correctness belong to the brand dimension. Judge construction and depth discipline only, in light or dark theme alike.

- Surfaces are flat fills. No gradients anywhere: not in backgrounds, panels, buttons, or decorative shapes. A soft solid-color wash is fine; a two-stop color ramp is not.
- No outlines or strokes on illustration shapes; edges are shape-on-shape. No texture, noise, or skeuomorphic effects; no inner shadows.
- Depth inside an illustrated object is at most one darker shade of the same hue; no multi-step shading, no photoreal rendering.
- Shadows, where present at all, are soft, low-opacity, tinted with the brand ink color (never pure black), and sit only under elements that read as pressable (buttons, actionable cards). Decorative and informational surfaces carry no shadow.
- Negative space is respected: roughly 40 percent or more of the canvas is empty, and hierarchy comes from size and spacing, not from extra colors or effects.
- Illustrations, if any, are geometry-first flat vector: simple circles, rectangles, and rounded forms; realistic adult proportions; minimal facial detail; no cartoon heads or mascots; no red or alarm colors; no photographic elements.
- No emoji used as icons; icons are monoline SVG.

5 = strictly flat throughout, depth used only as sanctioned above. 3 = flat overall with one or two slips (a stray gradient, one heavy or black shadow). 0 = gradients, outlines, texture, or heavy shadows dominate the composition.

Return "Unknown" if the image is unreadable or missing.

Provenance: this dimension encodes the flat-design system itself rather than any
one kit. For a concrete gradient-free component reference, see the vendored
`references/ui-component-libs/flat-ui` (`dist/css/flat-ui.css` and
`docs/components.html`). It is a Bootstrap-era kit, so read it for construction
patterns only, never for palette, type, or markup idiom - those come from
`brand/tokens.json` and the studio templates.
