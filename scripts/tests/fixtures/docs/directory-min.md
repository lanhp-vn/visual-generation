---
template: directory
title: Directory Anchor Probe
subtitle: A generic two-entity fixture
edition: Edition 1
date: September 2026
count_line: 5 entries
confidential: true
lang: en
audience: internal
---

This fixture proves that internal jump links survive Paged.js plus Chromium
print. It exercises both routes a directory needs: the auto-generated table of
contents, and a hand-written anchor into a hand-written id.

<div class="dindex">
  <p class="dindex-group">Group One</p>
  <a class="dindex-row" href="#entry-one"><span class="dindex-name">Entry One</span><span class="dindex-field">Discipline A</span><span class="dindex-place">Region A</span></a>
  <a class="dindex-row" href="#entry-two"><span class="dindex-name">Entry Two</span><span class="dindex-field">Discipline B</span><span class="dindex-place">Region B</span></a>
</div>

<p class="probe-index"><a href="#group-one">Group One</a> and <a href="#group-two">Group Two</a></p>

<!-- TOC -->

# Group One

Placeholder body text for the first group, long enough to occupy part of a page
so that pagination has something real to lay out.

<div class="dentry" id="entry-one">
  <div class="dentry-head">
    <p class="dentry-name">Entry One</p>
    <p class="dentry-place">Country A</p>
    <p class="dentry-role">Role Title, Institution Name</p>
  </div>
  <div class="dentry-rail">
    <p class="drail-label">Helps with</p>
    <ul class="drail-tags"><li>Tag A</li><li>Tag B</li><li>Tag C</li></ul>
    <p class="drail-label">Available</p>
    <p class="drail-value">2 to 5 h/week</p>
  </div>
  <div class="dentry-body">
    <p class="dentry-bio">A short biography of the first entry, kept inside the character budget.</p>
    <p class="dentry-fact"><b>Funding</b> A short funding note.</p>
    <p class="dentry-fact"><b>Offers</b> A short offer line.</p>
    <p class="dentry-action"><a href="https://example.org/book-one">Book a session</a><span class="dentry-url">example.org/book-one</span></p>
  </div>
</div>

<div class="dentry" id="entry-two">
  <div class="dentry-head">
    <p class="dentry-name">Entry Two</p>
    <p class="dentry-place">Country B</p>
    <p class="dentry-role">Role Title, Institution Name</p>
  </div>
  <div class="dentry-rail">
    <p class="drail-label">Helps with</p>
    <ul class="drail-tags"><li>Tag A</li><li>Tag D</li></ul>
    <p class="drail-label">Available</p>
    <p class="drail-value">Under 2 h/week</p>
  </div>
  <div class="dentry-body">
    <p class="dentry-bio">A short biography of the second entry.</p>
    <p class="dentry-fact"><b>Funding</b> A short funding note.</p>
    <p class="dentry-fact"><b>Offers</b> A short offer line.</p>
    <p class="dentry-action"><a href="mailto:two@example.org">Email</a><span class="dentry-url">two@example.org</span></p>
  </div>
</div>

# Group Two

<section class="dgroup">
  <p class="dgroup-band">Second Field</p>
  <p class="dgroup-count">2 entries</p>
  <ul class="dgroup-index">
    <li><a href="#entry-three">Entry Three</a></li>
    <li><a href="#entry-four">Entry Four</a></li>
  </ul>
</section>

<div class="dentry" id="entry-three">
  <div class="dentry-head">
    <p class="dentry-name">Entry Three</p>
    <p class="dentry-place">Country C</p>
    <p class="dentry-role">Role Title, Institution Name</p>
  </div>
  <div class="dentry-rail">
    <p class="drail-label">Helps with</p>
    <ul class="drail-tags"><li>Tag B</li></ul>
    <p class="drail-label">Available</p>
    <p class="drail-value">2 to 5 h/week</p>
  </div>
  <div class="dentry-body">
    <p class="dentry-bio">A short biography of the third entry.</p>
    <p class="dentry-fact"><b>Funding</b> A short funding note.</p>
    <p class="dentry-fact"><b>Offers</b> A short offer line.</p>
    <p class="dentry-action"><a href="https://example.org/book-three">Book a session</a><span class="dentry-url">example.org/book-three</span></p>
  </div>
</div>

<div class="dentry" id="entry-four">
  <div class="dentry-head">
    <p class="dentry-name">Entry Four</p>
    <p class="dentry-place">Country D</p>
    <p class="dentry-role">Role Title, Institution Name</p>
  </div>
  <div class="dentry-rail">
    <p class="drail-label">Helps with</p>
    <ul class="drail-tags"><li>Tag C</li></ul>
    <p class="drail-label">Available</p>
    <p class="drail-value">Under 2 h/week</p>
  </div>
  <div class="dentry-body">
    <p class="dentry-bio">A short biography of the fourth entry.</p>
    <p class="dentry-fact"><b>Funding</b> A short funding note.</p>
    <p class="dentry-fact"><b>Offers</b> A short offer line.</p>
    <p class="dentry-action"><a href="mailto:four@example.org">Email</a><span class="dentry-url">four@example.org</span></p>
  </div>
</div>

<p class="dgroup-inline">Third Field</p>

<div class="dentry" id="entry-five">
  <div class="dentry-head">
    <p class="dentry-name">Entry Five</p>
    <p class="dentry-place">Country E</p>
    <p class="dentry-role">Role Title, Institution Name</p>
  </div>
  <div class="dentry-rail">
    <p class="drail-label">Helps with</p>
    <ul class="drail-tags"><li>Tag A</li></ul>
    <p class="drail-label">Available</p>
    <p class="drail-value">2 to 5 h/week</p>
  </div>
  <div class="dentry-body">
    <p class="dentry-bio">A short biography of the fifth entry.</p>
    <p class="dentry-fact"><b>Funding</b> A short funding note.</p>
    <p class="dentry-fact"><b>Offers</b> A short offer line.</p>
    <p class="dentry-action"><a href="mailto:five@example.org">Email</a><span class="dentry-url">five@example.org</span></p>
  </div>
</div>
