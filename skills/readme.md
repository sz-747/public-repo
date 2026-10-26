---
name: public-repo-readme
description: Write and maintain the README of a public project repo so that its first screen shows the project's logo, name, one-line pitch and an image of the real app, and every later section is accurate. Part of the public-repo skill; load it from there when a public project needs a README, a new screenshot, or a check that the README still matches the app.
---

# Public README

Part of [public-repo](../SKILL.md). The root skill's scan, review and publish rules apply to everything here.

## Goal

A README that a stranger understands from its first screen on GitHub, and that stays true as the project
changes:

1. The **logo**, centred.
2. The project **name** as the only `<h1>`, centred.
3. A **one-line pitch**, centred: what it is and the main thing it does for the reader.
4. An **image of the real app** as people will see it (a screenshot or short GIF), centred.
5. Then the human-facing body from the root skill's "README for humans" contract: what it is (with a short
   feature list), what it is used for, evidence when there is any, how it is designed, privacy (when
   anything leaves the user's machine), licence and credits. Install, configure, run and test go in an
   agent-facing guide such as `INSTALL.md`, linked once at the bottom with an unmistakable label.

A library or a command-line tool with no window uses a terminal capture or a short code example as item 4.

## Out of scope

- Designing a new logo or brand. If the project has none, ask the owner. Do not invent a mark and present it
  as the project's logo.
- Mock-ups or design concepts in place of the real app. Item 4 always shows the shipped product.
- Publishing. A README change is pushed like any other change: scanner clean first (root skill).

## The header

Use HTML so that GitHub centres it. Image paths are relative to the repo root and point at tracked files:

```html
<p align="center">
  <img src="assets/logo.png" alt="<Name> logo" width="104">
</p>

<h1 align="center"><Name></h1>

<p align="center">
  <One sentence: what it is.><br>
  <One sentence: what it does for the reader.>
</p>

<p align="center">
  <img src="docs/screenshot.png" alt="<What the image shows, in words>" width="900">
</p>
```

- **Logo file:** a square PNG with a transparent background, at least 256 px, committed in the repo (for
  example `assets/logo.png`). When the logo is drawn by a script or kept as an SVG, commit that source too
  and name it in the README, so the logo can be redrawn. Reuse the same file for the launch page's favicon
  and header (see [launch-page](launch-page.md)).
- **Displayed size:** the logo at about 100 px wide; the app image at 900 px wide. Capture each image at
  least as wide as its displayed width (wider is fine), or it looks blurry.
- **Alt text** says what the image shows ("Home screen: the dictation banner, then recent dictations"),
  not "screenshot".

## The app image

- **The real product, current version.** Capture the shipped UI, not a design file. Retake the image in the
  same change as any UI change it shows. An out-of-date image is a defect, like a wrong command.
- **Fictional data only.** Load demo data with an invented user name, invented contacts and invented
  content. Do not paint over or crop real data; capture again with demo data instead. Check the whole frame
  for the owner's name, a greeting, notifications, open tabs, file paths, account avatars, calendar entries
  and the clock.
- **Reproducible.** Take it with a script (for example headless Chrome through Playwright on a web UI, with
  the demo data injected before the page loads), at the app's real window size, and keep that script and
  its demo data. Then the next capture takes one command. The script may live outside the public repo; if
  it is committed, its data must be fictional and scan clean.
- **One theme.** Show the theme most users see. Mention the other one in the feature list if it matters.
- **Size:** a PNG under about 300 KB; a GIF under about 5 MB (the scanner flags files over 5 MB). A short
  loop is useful only when the motion is the point. Otherwise use a still image.
- **Reuse:** the same image is the launch page's `og:image`, the preview picture that link previews show.
- **Manual review:** the scanner cannot read pixels. Open the final image and look at it before every push
  that adds or changes it. Strip EXIF metadata from photos.

## The body

- **Feature list:** one bullet per feature, starting with a bold phrase that names the feature, then one or
  two sentences on what it does. A feature that sends data off the machine says so in its bullet, and says
  whether it is off by default.
- **Install, configure, run, test:** in the agent guide (for example `INSTALL.md`), not the README body: exact
  commands, in that order, from the repo root, with the shell named. The README links to the guide once at
  the bottom. If the launch page offers a setup prompt for a coding agent, the guide is what it points at,
  and the README may show the same prompt next to that link.
- **Settings:** name each setting and the file or screen where it is changed. Real values are never shown
  (root skill: public contract and local overlay).
- **Privacy table** when anything leaves the user's machine: one row per feature, with where its data goes.
  Check every row against the code, not against an older README.
- **Links:** relative links to files in the repo, absolute links to everything else. The scanner reports
  links to files that are not in the repo.
- **Licence and credits:** the licence, and the upstream projects that the code is forked from or adapted
  from, with their licences.

## Known pitfalls

From real releases:

- **The owner's name was in the app screenshot**, in a "Welcome back, <name>" greeting. It was painted out
  first. The image was then retaken with demo data, which is the fix.
- **The screenshot went stale twice:** once when a page was split into separate pages, once after a
  redesign. Each time, the README, the launch page's preview image and the launch page's clips all showed the
  old UI until they were captured again. Keep a list of every place that shows the app (see
  [launch-page](launch-page.md)) and redo all of them together.
- **A privacy line was wrong.** It said that a connected calendar was read only when an AI agent asked. The
  app also read the calendar for two other features. Read the code for every privacy claim.

## Done when

- The first screen on GitHub shows the logo, the name, the pitch and the current app, and every image loads
  (look at the repo page on GitHub, not only the local file).
- The image shows the current UI with fictional data only, and you looked at it in full.
- Install and setup live in the linked agent guide, and every command in it was run from a fresh clone, or the
  report names those that were not.
- The scanner prints `clean` (root skill).

## Output

Report: the README sections changed, which images were added or retaken and how (script and demo data),
what was looked at by eye, and which commands were not run.
