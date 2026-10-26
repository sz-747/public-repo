---
name: public-repo
description: Open-source a project or an agent skill as a public GitHub repository with nothing private in its files, file names, history, commit identities or settings, working on its own from a fresh clone, and keep it clean on every later push. Use when asked to make a repo public, open-source a project or app, publish a skill (or a set of skills) as its own repo, or check a repo before pushing it somewhere public.
---

# Public repo

Category: Workflow.

## Goal

A public repository that holds only what the owner meant to share and works on its own: no secrets, personal
details, private names, hosts, codes, machine paths, real user data or private commit identities in the
current files or anywhere in history, and nothing that depends on files left behind in the private source.
Every later push passes the same check before it leaves the machine.

Two kinds of release use this skill:

- **A project**: an app, site, library, tool or starter template.
- **A skill**: one agent skill folder (`SKILL.md` plus its scripts, references, tests), or a collection of
  skills, taken out of a private skills folder or project.

## Out of scope

- Making anything public without a yes. Creating a public repo, or changing a repo's visibility to public,
  each need the owner's explicit yes. Later pushes follow whatever the owner authorised for that repo; when
  unclear, ask.
- Choosing the licence. Offer options (MIT is the usual default) and let the owner decide.
- Rewriting or deleting the private source, legal review of third-party licences (flag them only), and
  publicity such as directory submissions or posts.

## Public contract and local overlay

Every release splits into two parts. Only the first goes in the repo.

| Public repo: the generic contract | Private local overlay: this owner's setup |
|---|---|
| What the project or skill does, its rules and its done-when | Personal workspace and machine paths (`/home/<you>/...`, `%USERPROFILE%\...`) |
| CLI interface: commands, flags, inputs, outputs, exit codes, error messages | API keys, tokens, passwords, OAuth secrets, session secrets |
| Setting **names** with placeholders (`.env.example`, `config.example.json`) and where they are read from | Local aliases: short names for this owner's paths, projects, accounts or machines |
| Defaults that suit anyone | Account defaults, real email addresses, contacts, team or project IDs, admin codes |
| The overlay's location and format, documented | The overlay file itself, with real values |

- **Where the overlay lives:** outside the repo (`~/.config/<tool>/`, or a private notes or skills repo), or in
  an ignored file inside it (`.env`, `*.local.json`, `local/`) with a matching `.gitignore` line committed.
  Only the `.example` version is committed.
- **How public code reads it:** command-line flag, then environment variable, then the overlay file, then a
  generic default. A missing required value stops with a message naming the setting. The code never falls back
  to the owner's real value, and the docs never show one.
- **Moving a private source into the open:** for each private value the scan or the review finds, decide
  *remove* (it was only an example) or *move* (the tool needs it): moved values go to the overlay and the code
  or skill refers to a setting name instead.
- **Without the overlay:** a fresh clone with no overlay still installs, passes its offline tests and explains
  which settings are needed for live use.

This skill follows the same split: its scanner is public, and each owner's deny list is their own overlay.

## Resources

Scanner (Python 3.11+, standard library only; paths are relative to this skill's folder):

```sh
python -B scripts/scan_public.py --repo <path> --allow-email <id>+<user>@users.noreply.github.com
```

- Checks tracked files (text and names), added lines and messages of every reachable commit, and every author
  and committer email. Categories: deny-list, secret (redacted in output), email, machine path, control
  character, risky file (`.env`, keys, databases, logs, `.vercel/`...), large file (over 5 MB), submodule,
  commit identity, broken link (a Markdown link to a file not in the repo), wikilink (`[[name]]`, which
  GitHub does not render), overlay committed (a top-level `local/` folder or a `*.local.*` file) and overlay
  not ignored (an `.env.example` or `config.example.json` whose real file `.gitignore` does not cover).
- **Private deny list (the scanner's overlay):** the owner's names, handles, organisation and client names,
  codes, hosts and private folder names, one case-insensitive regex per line, `#` comments allowed. Copy
  [`deny.example.txt`](deny.example.txt) to `~/.config/public-repo/deny.txt` (or `$XDG_CONFIG_HOME/...`), or
  point `PUBLIC_REPO_DENY` at one or more files (separated by `;` on Windows, `:` elsewhere). `--deny-file`
  adds more. Never commit a real deny list; it lists exactly what must stay private.
- `--allow-email` (repeatable) sets which commit identities pass and which emails may appear in files. Without
  it, only `@users.noreply.github.com` identities pass. Placeholder emails (`example.com`, `.test`) always pass.
- `--no-history` scans current files only (identities are still checked); `--no-default-deny` ignores the
  overlay; `--json <file>` saves findings.
- A line containing `public-scan: allow` is skipped. Use it only for a documented false positive.
- Exit codes: `0` clean (prints `clean: N tracked files ...`), `1` findings, `2` not a Git repo or an
  unreadable or invalid deny list.
- Tests (offline, throwaway repos): `python -B -m unittest discover -s tests -v`.

GitHub CLI (`gh`) creates and inspects the repo. GitHub's own secret scanning and push protection on public
repos are a second net, not a replacement for the scan.

## How to choose the route

Old history keeps every deleted secret and every private commit email, so the route matters more than the cleanup:

| Situation | Route |
|---|---|
| Default; always for a skill taken out of a private collection; any subset or de-branded copy | **Fresh repo.** Build the public tree in a new sibling folder, `git init`, set the repo-local identity to the GitHub noreply address before the first commit, commit in small steps. |
| A whole existing project repo, and a full-history scan is clean with acceptable identities | Flip the existing repo's visibility. |
| History must be kept but contains private material | Rewrite with `git filter-repo` only as a last resort, then rescan. |

Any real secret that was ever pushed anywhere public, or committed to history that becomes public, must be
rotated at its provider. Deleting it is not enough; clones, forks and caches keep it.

## Required outcomes

1. **Scope agreed:** project or skill; what goes public; the repo name and description; the licence; the
   commit identity (GitHub noreply, `<id>+<user>@users.noreply.github.com`, set with `git config user.email`
   in that repo).
2. **Public tree separate and self-contained:** built outside the private source, with the kind-specific
   points below done. Write files with file tools, not shell strings (see pitfalls).
3. **Deny list current:** anything private the public tree could mention (people, organisations, clients,
   hosting project names, domains, preview URLs, admin or event codes, private repo and folder names) is in
   the deny list. Patterns cannot guess these.
4. **Scanner clean:** every finding removed, replaced, or (false positives only) marked and explained.
5. **Manual review done**, for what the scanner cannot judge: read every file once, including README, comments,
   TODOs and docs that mention people, plans or internal decisions; images and screenshots (faces, names,
   open tabs, EXIF location); PDFs and notebook outputs; test fixtures that look like real people; lockfiles
   or config pointing at private registries; CI workflows using secrets or self-hosted runners; vendored or
   adapted code and its licence.
6. **Works from a fresh clone:** see the kind-specific check below.
7. **Published with a yes:** preferably `gh repo create <owner>/<name> --private --source . --push`, look at
   it on GitHub, then `gh repo edit --visibility public --accept-visibility-change-consequences`. Set the
   description and topics; turn off the wiki and projects if unused.
8. **Verified as public:** `gh repo view --json visibility,url` says PUBLIC; only intended branches and tags
   exist (`git ls-remote`); a fresh clone into a temp folder scans clean (this proves what is actually public).
9. **Kept clean:** before every later push, the scanner prints `clean` on the public repo. Commit small and keep
   the private source of truth and the public copy in step. Optionally add a local `.git/hooks/pre-push` that
   runs the scanner.

### README for humans

Apply this contract to every public project and skill repository. A nontechnical reader should be able to
skim the README and immediately understand the subject and why they would use it. Keep the main body to:

- **What it is:** a short, plain description of the thing being shared.
- **What it is used for:** concrete use cases, with a small example when it helps.
- **Evidence, when available:** demonstrated results, tests or measurements, with their limits. Omit this
  when there is no evidence; do not invent validation or imply broader proof than the checks establish.
- **How it is designed:** a couple of sentences and a simple diagram are usually enough. Technical detail
  is fine here when it helps explain the design. A separate architecture document, heading or rigid template
  is not required.

Move installation, dependency commands, configuration, authentication, running and testing instructions to
an agent-facing Markdown guide such as `INSTALL.md`. Link it once at the bottom with an unmistakable label,
for example **[AGENTS: READ THIS TO INSTALL](INSTALL.md)**. If setup must stay in the README, keep it in a
clearly labeled agent-only section at the bottom, after the human overview. Do not make humans read npm,
shell commands or lengthy setup details before they understand the project. Keep required license and
attribution notices concise and visible.

### Open-sourcing a project

- Real data replaced: seed files, fixtures, screenshots and sample CSVs use fictional people and values.
- Configuration by example: `.env.example` with names and placeholders only, real values in the local
  overlay; no `.vercel/`, `.netlify/` or other files that link to the owner's hosting accounts; no region,
  project or team IDs that only fit them.
- De-branded where the owner asked: product name, cookie and storage names, domains, logos, redirects.
- A human-facing README following the contract above, with a linked agent installation guide or an
  explicitly labeled setup section at the bottom.
- Fresh-clone check: clone, install from the lockfile, run the tests or start it with only `.env.example`
  values. Name anything that needs a real account (a database, an API key) in the installation guide.

### Open-sourcing a skill

- Layout: `SKILL.md` at the repo root for one skill, or `skills/<name>/SKILL.md` for several. Frontmatter
  `name` matches the folder name; `description` says what it does and when to use it.
- Generic contract only: the skill defines the outcome, the boundaries and any CLI interface; account names,
  defaults, contacts, credentials, workspace paths and aliases move to the local overlay (see above), and the
  skill names the settings it needs and where it reads them.
- No coupling to the private source: no links to private rules or sibling skills that are not published
  (bundle what is needed, or describe it in a sentence); no `[[wikilinks]]`; no owner names or machine paths;
  commands and tests run from the repo root, not from the private collection's root, and do not import from
  folders outside the repo.
- Provenance: if the skill was adapted from someone else's, keep their licence and credit them in the README.
- A short human-facing README following the contract above. The linked agent guide explains installation
  into the client's supported skills directory, required configuration, the entry point, and offline checks.
- Fresh-clone check: the scanner reports no broken links or wikilinks; the skill's tests pass when run from
  the clone root; a reader with only the clone can follow `SKILL.md` without anything from the owner's machine.

## Known pitfalls

From real releases:

- **A PowerShell string turned `` `t `` into a tab** inside a public Markdown file, changing the text. Write
  public files with file tools; the scanner's control-character check flags such characters.
- **A skill copied as-is still pointed back at its private collection.** A dry run that copied one private skill
  into a fresh repo scanned with 20 findings: "run from the root" instructions for the private collection, its
  folder paths in the script and tests, the owner's name, a private sources file and a link to an unpublished
  sibling skill. Expect to edit every skill before release.
- **Test fixtures trip the scanner.** Fake emails and paths planted on purpose in tests are flagged like real
  ones; mark those lines `public-scan: allow` with a comment saying they are fake.

## Done when

- The scanner printed `clean` on a fresh clone of the public repo, with the deny list loaded and identities
  allowed explicitly.
- The fresh-clone check for its kind (project or skill) passed, or the report names what could not run.
- Every private value is either removed or moved to the local overlay; the repo carries only setting names,
  placeholders and the overlay's documented location, and ignores the overlay file.
- The manual review list above was gone through, and anything not checked is named in the report.
- Any secret that was ever exposed has been rotated, or the report says it still needs rotating.
- The repo's visibility, branches and description match what the owner agreed.
- The README is skimmable by a nontechnical reader: purpose, use cases, available evidence, and a brief
  design explanation. Installation is one clear link or a labeled agent section at the bottom.

## Output

Report in chat:

```text
Public repo: https://github.com/<owner>/<name> (PUBLIC, <licence>)
Kind: project | skill | skill collection
Route: fresh repo | flipped existing | rewritten history
Commits: <n>, all by <identity>
Scan: clean: <n> tracked files (files and history, <n> deny rules), on a fresh clone
Fresh-clone check: <tests passed / app started / what could not run>
Local overlay: <location and setting names moved there, or none needed>
Manual review: done / not checked: <items>
Still to do: <licence decision, secret rotation, ...>
```
