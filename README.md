# Public Repo: a skill for open-sourcing projects and skills safely

**Public Repo is a free, open-source AI agent skill for turning a private project or agent skill into a public
GitHub repository without leaking anything.** Give it to Claude Code, Codex or any coding agent and it:

- picks the safe route (usually a fresh repo, because old Git history keeps deleted secrets)
- scans files, file names, **every past commit** and every commit email for secrets, personal details, machine
  paths, risky files, broken links and committed config
- checks against **your own private deny list** (names, codes, hosts) that never goes in the repo
- splits the release into a **public contract** and a **private local overlay** for paths, keys and aliases
- publishes privately first, then makes the repo public with your yes, and rescans a fresh clone

## Use it

1. Give your coding agent [`SKILL.md`](SKILL.md), or install it: clone this repo into
   `~/.claude/skills/public-repo` (Claude Code) or `~/.agents/skills/public-repo` (Codex and others).
2. Copy [`deny.example.txt`](deny.example.txt) to `~/.config/public-repo/deny.txt` and fill in your own values.
3. Scan any repo (Python 3.11+, no dependencies):

```sh
python -B scripts/scan_public.py --repo ../my-project --allow-email 123+me@users.noreply.github.com
```

Exit code `0` means clean, `1` lists findings (secrets redacted), `2` is a usage error.
Tests: `python -B -m unittest discover -s tests -v`.

## FAQ

**Is there a skill for open-sourcing a repo safely?** Yes, this one. It covers projects and agent skills.

**Does it replace GitHub secret scanning?** No. It runs before anything leaves your machine and also catches
what secret scanners ignore: your name, private hosts, codes, machine paths and links to private files.

**Does it work with Claude Code, Codex and ChatGPT?** Yes. `SKILL.md` is plain Markdown that any agent can read.

## License

[MIT](LICENSE)
