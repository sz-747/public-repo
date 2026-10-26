# Agent installation and setup guide

## Install the skill

Clone this repository into the user's supported skills directory, or clone it elsewhere and copy the complete folder there. Keep `SKILL.md`, its scripts, tests, and referenced files together.

Common locations are `~/.agents/skills/public-repo/` for Codex and other compatible clients, `~/.claude/skills/public-repo/` for Claude Code, or the current project's skills folder. Use the client's actual configured location.

```sh
git clone https://github.com/sz-747/public-repo.git public-repo
cd public-repo
```

Read [SKILL.md](SKILL.md) as the skill entry point. It defines the publishing boundaries, required checks, and completion report. Installing this skill does not itself authorize publishing any project.

## Prerequisites

- Python 3.11 or newer. The scanner uses only the standard library.
- Git for repository and history checks.
- GitHub CLI (`gh`) authenticated to the intended account for repository creation and publishing.

## Configure a private deny list

Copy [deny.example.txt](deny.example.txt) to `~/.config/public-repo/deny.txt` and replace the examples with the owner's private names, hosts, codes, and folder names. The list is one case-insensitive regular expression per line; `#` comments are allowed. Keep the real list outside the public repository.

With `XDG_CONFIG_HOME` set, the default is `$XDG_CONFIG_HOME/public-repo/deny.txt`. Use `--deny-file` to add another list, or `PUBLIC_REPO_DENY` for one or more paths, separated by `;` on Windows or `:` elsewhere.

Use the owner's approved GitHub noreply identity for public commits. Do not publish private email addresses from local Git configuration.

## Run the scanner

Run from this skill's root. Replace the repository path and example identity with the intended values:

```sh
python -B scripts/scan_public.py --repo ../my-project --allow-email 123+me@users.noreply.github.com
```

Exit codes:

- `0`: clean.
- `1`: findings; secrets are redacted in output.
- `2`: usage error, such as an unreadable deny list or a path that is not a Git repository.

The scanner inspects tracked files and reachable commit history. Stage new files before scanning so links and new content are included. See [SKILL.md](SKILL.md) for additional flags, exceptions, manual review, fresh-clone checks, and publishing requirements.

## Verify the installation

Run the offline tests from the skill's root:

```sh
python -B -m unittest discover -s tests -v
```

Then scan the intended release with the private deny list loaded. Tests and a clean scan provide evidence for the checks they exercise; they do not replace review or grant publication authority.
