---
template: report
title: Directory Anchor Probe
subtitle: A generic two-entity fixture
lang: en
date: 2026-09-16
audience: internal
---

This fixture proves that internal jump links survive Paged.js plus Chromium
print. It exercises both routes a directory needs: the auto-generated table of
contents, and a hand-written anchor into a hand-written id.

<div class="probe-index">
  <p><a href="#entry-one">Entry One</a></p>
  <p><a href="#entry-two">Entry Two</a></p>
</div>

<!-- TOC -->

# Group One

Placeholder body text for the first group, long enough to occupy part of a page
so that pagination has something real to lay out.

<p id="entry-one">Entry One, a generic placeholder entity.</p>

# Group Two

Placeholder body text for the second group.

<p id="entry-two">Entry Two, a second generic placeholder entity.</p>
