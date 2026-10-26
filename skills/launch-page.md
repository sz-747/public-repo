---
name: public-repo-launch-page
description: Build and publish a one-page launch site for a public project on GitHub Pages, from a site/ folder in the same repo, with a direct download of the latest release, a one-prompt install for coding agents, and short clips of the real app. Part of the public-repo skill; load it from there when a public project needs a launch page, a release download, new showcase clips, or a check that the live page still matches the app.
---

# Launch page on GitHub Pages

Part of [public-repo](../SKILL.md). The root skill's scan, review and publish rules apply to everything here.
The page reuses the README's logo and app image (see [readme](readme.md)).

## Goal

A live page at `https://<owner>.github.io/<repo>/` that a visitor can act on in one step:

- it says what the project is in one sentence, and shows the real app working;
- its install action works: a setup prompt to paste into a coding agent, a download of the latest release, or
  both;
- it deploys from the repo on every change to the site, with no build step and no second repo;
- what it shows and what it downloads match the current version of the app.

## Out of scope

- Turning Pages on, adding or removing a custom domain, and creating a release each publish something, so
  each needs the owner's yes. Changes to the account's other repos (for example `<owner>.github.io`) need a
  separate yes.
- Domain registration and DNS. Explain what is needed; the owner does it at their registrar.
- Publicity: posts, directories, launch announcements.

## Decisions to keep

These came from a real launch. Each has its reason. Change one only when the owner asks.

### Where the page lives and how it deploys

- **`site/` in the project repo:** plain HTML, CSS and JavaScript, no build step. The scanner then covers the
  page too, and one commit can change the app and its page together.
- **Relative asset paths** (`assets/logo.png`, not `/assets/logo.png`). A project site is served under
  `/<repo>/`, so a path that starts with `/` breaks. The `og:image` is the exception: link previews need
  an absolute URL.
- **Deploy with GitHub Actions** (Pages source "GitHub Actions"), with a workflow such as
  `.github/workflows/pages.yml`:
  - triggers: push to `main` with paths `site/**` and the workflow file itself, plus `workflow_dispatch`;
  - permissions `contents: read`, `pages: write`, `id-token: write`, and a `pages` concurrency group;
  - steps `actions/checkout`, `actions/configure-pages`, `actions/upload-pages-artifact` with `path: site`,
    then `actions/deploy-pages`;
  - `if: ${{ !github.event.repository.private }}` on the job, because Pages on a private repo needs a paid
    plan. The workflow can then be committed before the repo goes public.
- **Turn Pages on** after the repo is public, with the owner's yes:
  `gh api -X POST repos/<owner>/<repo>/pages -f build_type=workflow`, then
  `gh workflow run pages.yml --repo <owner>/<repo>` for the first deploy.
- **Check the user site first.** A custom domain on the account's `<owner>.github.io` repo redirects every
  project site of that account to that domain. Run `gh api repos/<owner>/<owner>.github.io/pages --jq .cname`.
  If it returns a domain, ask the owner to choose: point the domain's DNS at GitHub Pages, or remove the
  custom domain. Removing it makes GitHub commit "Delete CNAME" to that repo, with the account's display
  name as the author.

### Download

- **Link straight to the file:** `https://github.com/<owner>/<repo>/releases/latest/download/<asset>.zip`,
  with the `download` attribute. The file downloads at once, with no stop on the GitHub release page, and the
  link follows each new release. Put a small "Release notes" link to `/releases/latest` beside it.
- **Keep the asset name the same in every release** (for example `<name>-windows.zip`). A version number in
  the name breaks the `latest/download` link.
- **Build the release from tracked files only:** a workflow on `v*` tags that runs
  `git archive --format=zip --prefix=<name>/ -o <asset>.zip HEAD` and then `gh release create`. The zip then
  holds exactly what the scanner checked; ignored overlay files cannot get in.
- **The link returns 404 until the first release exists.** Publish the first release before, or together
  with, the page.
- **Release after every user-facing change.** Bump each place that shows the version, commit, scan, then
  push the tag. Otherwise the page shows the new app and the download gives the old one.

### Install

- **Lead with a setup prompt for a coding agent** (the owner's choice): the main button copies a prompt to the
  clipboard ("Copy setup prompt for your AI agent"), and the download sits beside it. Further down, a card marked
  as recommended shows the full prompt with its own copy button, next to a download card.
- **The prompt points at the install guide by URL** (for example `.../blob/main/INSTALL.md`) and asks the agent
  to follow it step by step, ask before anything that needs admin rights, and report the guide's final checks.
- **The guide must work without a browser.** Give exact commands for every download (models, runtimes),
  every file location and every config change, and end with checks the agent can run. "Download it from the
  releases page" is not enough for an agent.
- **One prompt text.** The hero button, the card and the README use the same words. Keep a single source in
  the page (for example one `<pre>` that both buttons copy).
- **Copy with a fallback.** Use `navigator.clipboard.writeText`, fall back to a hidden textarea, and change the
  button's label for about 2 s to confirm.

### Showing the app

- **Short clips of the real app**, not mock-ups, recorded from the shipped UI with fictional demo data (the
  same data as the README image). For a web UI, record headless Chrome with Playwright, with the demo data
  injected before the page loads and a visible cursor.
- **MP4, not GIF, on the page:** H.264, `yuv420p`, `+faststart`, no audio, about 8 to 12 s each, with a poster
  JPG taken from the first frame. On one launch, four clips came to about 1.3 MB as MP4 and about 11 MB as GIF.
  Keep GIFs for the README or social posts if they are wanted.
- **One frame, tabs, one caption line:** a tab per area of the app; the active tab shows its progress; each
  clip moves on to the next when it ends. Clips are `muted playsinline` and play only while the frame is on
  screen (an `IntersectionObserver`). With `prefers-reduced-motion`, nothing autoplays and the video shows
  its controls.
- **An optional live demo in the hero** that shows the core action in a few seconds. It plays on its own,
  and a visitor can also try it (for example by holding a key or pressing the demo on touch screens). Any
  key handler skips text fields, buttons and links.
- **Keep a list of every place that shows the app:** the page's clips and posters, the README image, the
  `og:image` and any GIFs. When the UI changes, redo all of them in one change, with the same recorder and
  demo data.

### Page basics

- `<title>` and meta description; `og:title`, `og:description` and an absolute `og:image` (the README image);
  `theme-color`; the logo as favicon and in the header and footer.
- Works at phone width: no horizontal scroll at 390 px wide. Desktop and phone get the same content.
- Footer: the licence, credits for upstream projects, and the repo link.
- Every claim on the page (privacy, "runs offline", supported systems, download size) matches the README and
  the code.

## Verification

Run these on the live URL after each deploy (`gh run watch` until the Pages run succeeds), not only on the
local files:

1. The page returns 200 with the expected `<title>`, and its assets load.
2. In a real browser at 1280 px and 390 px wide: no console errors and no horizontal scroll; the clips play,
   tabs switch clips and captions, and a clip moves on to the next when it ends. Save a screenshot of each
   width.
3. The download link fetches the latest release's asset. Download it and check that it holds the current
   version (its version string and a file changed in the latest release).
4. The copy button puts the full prompt on the clipboard.
5. The scanner prints `clean` (root skill), and you looked at every new image and clip.

## Known pitfalls

From a real launch:

- **The page deployed but could not be reached:** the account's user site had a custom domain with no DNS
  records, so GitHub redirected the project site to a dead domain. The owner chose to remove the custom
  domain. Check this before turning Pages on.
- **The download button returned 404** until the first release was tagged.
- **The download gave the old app after a redesign.** The page and its clips showed the new UI, but
  `latest/download` still served the release built before it, until a new version was tagged.
- **The first download link opened the GitHub release page.** The owner wanted the file to download at once,
  so the link was changed to `releases/latest/download/<asset>.zip`.
- **The setup prompt's guide only linked to release pages.** An agent would have had to browse for the right
  files. The guide was rewritten with exact download and unzip commands.

## Done when

- The live page passes every verification step above, or the report names the steps that could not run.
- The release that `latest/download` serves matches the app that the page shows.
- Pages, any domain change and any release were done with the owner's yes.

## Output

```text
Launch page: https://<owner>.github.io/<repo>/ (deployed <commit>)
Download: <asset> from release <tag>, checked: <version and file seen>
Checks: desktop and phone, no errors / <what failed>
Showcase redone: <clips, posters, README image, og:image, GIFs>
Still to do: <DNS, first release, owner decisions>
```
