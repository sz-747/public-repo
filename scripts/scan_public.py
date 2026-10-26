"""Scan a Git repository for anything that should not be public, before it is pushed to a public remote.

Checks tracked files (content and names), every reachable commit (added lines and messages) and every commit
identity. Built-in patterns catch common secrets, emails, machine paths and risky files; a private deny list
adds the owner's own names, hosts and codes, which no pattern can know. Markdown links that point outside the
repo, and wikilinks, are reported too: a project's docs or a skill copied out of a private tree often still
point at files that stay private.

The deny list is the owner's private local overlay and never lives in the scanned repo. Lookup order:
--deny-file (repeatable), then PUBLIC_REPO_DENY (paths separated by os.pathsep), then
$XDG_CONFIG_HOME/public-repo/deny.txt or ~/.config/public-repo/deny.txt.

Exit codes: 0 clean, 1 findings, 2 usage error (not a Git repo, unreadable deny file).
A line containing `public-scan: allow` is skipped; use it only for a documented false positive.
"""
import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from urllib.parse import unquote

ALLOW_MARK = 'public-scan: allow'
LARGE_BYTES = 5 * 1024 * 1024

SECRETS = [
    ('private key', r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    ('AWS key', r'\bAKIA[0-9A-Z]{16}\b'),
    ('GitHub token', r'\bgh[pousr]_[A-Za-z0-9]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{40,}\b'),
    ('Anthropic key', r'\bsk-ant-[A-Za-z0-9_-]{20,}'),
    ('OpenAI-style key', r'\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}'),
    ('Slack token', r'\bxox[abprs]-[A-Za-z0-9-]{10,}'),
    ('Google API key', r'\bAIza[0-9A-Za-z_-]{35}\b'),
    ('Stripe live key', r'\b[sr]k_live_[0-9A-Za-z]{16,}'),
    ('npm token', r'\bnpm_[A-Za-z0-9]{36}\b'),
    ('Vercel/OIDC token', r'VERCEL_OIDC_TOKEN\s*=\s*["\']?[A-Za-z0-9._-]{20,}'),
    ('JWT', r'\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'),
    ('URL with password', r'\b[a-z][a-z0-9+.-]*://[^\s/:@"\']+:[^\s/@"\']+@[^\s"\']+'),
    # A value counts only if it has a digit and no call or template syntax, so prose and code like
    # `token = sign(...)` pass while `SESSION_SECRET=9f2c...` does not.  public-scan: allow
    ('assigned secret', r'(?i)\b[A-Z0-9_]*(?:SECRET|PASSWORD|PASSWD|TOKEN|API_KEY|PRIVATE_KEY)[A-Z0-9_]*\s*[:=]\s*["\']?'
                        r'(?!<|\$\{|\$[A-Z_]|process\.env|os\.environ|change-?me|example|xxx)(?=[^\s"\'(),;]*\d)[^\s"\'(),;]{8,}'),
]
EMAIL = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
SAFE_EMAIL = re.compile(r'(?i)@(?:[a-z0-9-]+\.)*(?:example\.(?:com|org|net)|users\.noreply\.github\.com)$'
                        r'|\.(?:test|invalid|example|localhost)$|^(?:no-?reply|git)@')
PATHS = r'\b[A-Za-z]:\\(?:Users|dev|Documents|Projects|src)\\[^\s"\'<>|]+|/(?:Users|home)/[a-z][a-z0-9._-]+/'
CONTROL = r'[\x00-\x08\x0b\x0c\x0e-\x1f]'
RISKY_NAME = re.compile(r'(?i)(?:^|/)(?:\.env(?!\.(?:example|sample|template)$)[^/]*|.*\.(?:pem|key|p12|pfx|keystore|jks|sqlite3?|db|dump|bak|log)'
                        r'|id_[rd]sa[^/]*|id_ed25519[^/]*|\.npmrc|\.pypirc|\.netrc|credentials[^/]*|secrets?\.[a-z]+|\.DS_Store|Thumbs\.db)$'
                        r'|(?:^|/)\.(?:vercel|netlify|aws|ssh)/')
# Private local overlay files: real values for a public contract, never committed.
OVERLAY_NAME = re.compile(r'(?i)^local/|(?:^|/)[^/]+\.local(?:\.[a-z0-9]+)?$')
EXAMPLE_NAME = re.compile(r'(?i)^(?P<stem>.*?)[.-](?:example|sample|template)(?P<ext>\.[a-z0-9]+)?$')


def git(repo, *args, check=True):
    done = subprocess.run(['git', '-C', str(repo), *args], capture_output=True)
    if check and done.returncode:
        raise RuntimeError(done.stderr.decode('utf-8', 'replace').strip() or f'git {args[0]} failed')
    return done.stdout


def load_deny(paths):
    rules = []
    for path in paths:
        for n, line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(), 1):
            line = line.split(' #', 1)[0].strip()
            if line and not line.startswith('#'):
                try:
                    rules.append(re.compile(line, re.I))
                except re.error as exc:
                    raise ValueError(f'{path}:{n}: bad pattern {line!r}: {exc}') from exc
    return rules


def redact(text):
    return text[:4] + '...' + f'({len(text)} chars)' if len(text) > 8 else '***'


class Scanner:
    def __init__(self, deny, allow_emails):
        self.deny = deny
        self.allow = {e.lower() for e in allow_emails}
        self.secrets = [(name, re.compile(rx)) for name, rx in SECRETS]
        self.email, self.paths, self.control = re.compile(EMAIL), re.compile(PATHS), re.compile(CONTROL)

    def email_ok(self, email):
        return email.lower() in self.allow or bool(SAFE_EMAIL.search(email))

    def line(self, text):
        """Yield (category, shown text) for one line."""
        if ALLOW_MARK in text:
            return
        for rule in self.deny:
            for m in rule.finditer(text):
                yield 'deny-list', m.group(0)
        for name, rule in self.secrets:
            for m in rule.finditer(text):
                yield f'secret: {name}', redact(m.group(0))
        for m in self.email.finditer(text):
            if not self.email_ok(m.group(0)):
                yield 'email', m.group(0)
        for m in self.paths.finditer(text):
            yield 'machine path', m.group(0)
        if self.control.search(text):
            yield 'control character', repr(self.control.search(text).group(0))


MD_LINK = re.compile(r'!?\[[^\]\n]*\]\(<?([^)\s>]+)>?(?:\s+"[^"]*")?\)')
WIKILINK = re.compile(r'\[\[[^\]\n]+\]\]')


def markdown_links(name, text, tracked, dirs):
    """Yield (line, category, target) for links that will not work once only this repo is public.

    Private source trees often link to files that stay behind (hub rules, sibling skills, local overlays);
    wikilinks do not render on GitHub at all.
    """
    base = PurePosixPath(name).parent
    fenced = False
    for n, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(('```', '~~~')):
            fenced = not fenced
        if fenced or ALLOW_MARK in line:
            continue
        line = re.sub(r'`[^`]*`', '', line)  # inline code shows examples, not links
        for m in WIKILINK.finditer(line):
            yield n, 'wikilink', m.group(0)
        for m in MD_LINK.finditer(line):
            target = m.group(1)
            if re.match(r'[a-z][a-z0-9+.-]*:', target, re.I) or target.startswith(('#', '//')):
                continue
            rel = unquote(target.split('#', 1)[0].split('?', 1)[0])
            if not rel:
                continue
            parts = []
            for part in (PurePosixPath(rel[1:]) if rel.startswith('/') else base / rel).parts:
                if part == '..':
                    if not parts:
                        parts = None
                        break
                    parts.pop()
                elif part != '.':
                    parts.append(part)
            resolved = '/'.join(parts) if parts is not None else None
            if resolved is None or (resolved not in tracked and resolved not in dirs):
                yield n, 'broken link', target


def scan(repo, deny, allow_emails, history=True):
    repo = Path(repo).resolve()
    if git(repo, 'rev-parse', '--is-inside-work-tree', check=False).strip() != b'true':
        raise RuntimeError(f'not a Git work tree: {repo}')
    sc = Scanner(deny, allow_emails)
    findings, seen = [], set()

    def add(category, where, text):
        key = (category, text)
        if where.startswith('history') and key in seen:
            return
        seen.add(key)
        findings.append({'category': category, 'where': where, 'text': text})

    files = [f for f in git(repo, 'ls-files', '-z').decode('utf-8', 'replace').split('\0') if f]
    tracked = set(files)
    dirs = {str(p) for f in files for p in PurePosixPath(f).parents if str(p) != '.'} | {''}
    for f in files:
        for category, text in sc.line(f):
            add(category if category != 'control character' else 'file name', f, text)
        if OVERLAY_NAME.search(f):
            add('overlay committed', f, 'local overlay files hold real values; commit an .example instead')
        elif RISKY_NAME.search(f):
            add('risky file', f, f)
        example = EXAMPLE_NAME.match(f)
        if example:
            real = example['stem'] + (example['ext'] or '')
            ignored = subprocess.run(['git', '-C', str(repo), 'check-ignore', '-q', '--no-index', real]).returncode == 0
            if real not in tracked and not ignored:
                add('overlay not ignored', f, f'{real} is not in .gitignore, so real values could be committed')
        path = repo / f
        if not path.is_file():
            continue
        if path.stat().st_size > LARGE_BYTES:
            add('large file', f, f'{path.stat().st_size // 1024} KB')
        data = path.read_bytes()
        if b'\0' in data[:8192]:
            continue
        content = data.decode('utf-8', 'replace')
        for n, text in enumerate(content.splitlines(), 1):
            for category, shown in sc.line(text):
                add(category, f'{f}:{n}', shown)
        if f.lower().endswith(('.md', '.markdown')):
            for n, category, target in markdown_links(f, content, tracked, dirs):
                add(category, f'{f}:{n}', target)
    if (repo / '.gitmodules').is_file():
        add('submodule', '.gitmodules', 'submodules can point at private repos; check each URL')

    has_commits = git(repo, 'rev-parse', '--verify', '-q', 'HEAD', check=False).strip()
    if has_commits:
        idents = git(repo, 'log', '--all', '--format=%ae%n%ce').decode('utf-8', 'replace').split()
        for email in sorted(set(idents)):
            # noreply@github.com is GitHub itself, committing merges made on the website.
            ok = email.lower() in sc.allow if sc.allow else email.lower().endswith('@users.noreply.github.com')
            if not ok and email.lower() != 'noreply@github.com':
                add('commit identity', 'history', email)
    if has_commits and history:
        log = git(repo, 'log', '--all', '-p', '--no-color', '--no-ext-diff', '--format=@@commit %h%n%B%n@@end')
        commit, path, in_msg = '', '', False
        for raw in log.decode('utf-8', 'replace').splitlines():
            if raw.startswith('@@commit '):
                commit, path, in_msg = raw[9:], '', True
                continue
            if raw == '@@end':
                in_msg = False
                continue
            if in_msg:
                for category, shown in sc.line(raw):
                    add(category, f'history {commit} message', shown)
            elif raw.startswith('+++ '):
                path = raw[6:] if raw.startswith('+++ b/') else ''
            elif raw.startswith('+') and path:
                for category, shown in sc.line(raw[1:]):
                    add(category, f'history {commit} {path}', shown)
    return files, findings


def default_deny_files():
    """Overlay deny lists from the environment, or the per-user config file if it exists."""
    env = os.environ.get('PUBLIC_REPO_DENY', '').strip()
    if env:
        return [Path(p).expanduser() for p in env.split(os.pathsep) if p.strip()]
    config = Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config')
    path = config / 'public-repo' / 'deny.txt'
    return [path] if path.is_file() else []


def main(argv=None):
    ap = argparse.ArgumentParser(description='Scan a Git repo for anything that should not be public.')
    ap.add_argument('--repo', default='.', help='repository to scan (default: current directory)')
    ap.add_argument('--deny-file', action='append', default=[], help='extra private deny list, one regex per line')
    ap.add_argument('--no-default-deny', action='store_true',
                    help='skip PUBLIC_REPO_DENY and ~/.config/public-repo/deny.txt')
    ap.add_argument('--allow-email', action='append', default=[], help='commit identity or email that may appear')
    ap.add_argument('--no-history', action='store_true', help='scan only the current files, not past commits')
    ap.add_argument('--json', help='also write findings to this JSON file')
    args = ap.parse_args(argv)

    deny_files = ([] if args.no_default_deny else default_deny_files()) + list(args.deny_file)
    if not deny_files:
        print('note: no private deny list (set PUBLIC_REPO_DENY or create ~/.config/public-repo/deny.txt); '
              'only built-in checks ran', file=sys.stderr)
    try:
        deny = load_deny(deny_files)
        files, findings = scan(args.repo, deny, args.allow_email, history=not args.no_history)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 2
    for f in findings:
        print(f"{f['category']:<22} {f['where']}  {f['text']}")
    if args.json:
        Path(args.json).write_text(json.dumps({'files': len(files), 'deny_rules': len(deny),
                                               'findings': findings}, indent=2), encoding='utf-8')
    scope = 'files and history' if not args.no_history else 'files only'
    if findings:
        print(f'{len(findings)} finding(s) in {len(files)} tracked files ({scope}, {len(deny)} deny rules)')
        return 1
    print(f'clean: {len(files)} tracked files ({scope}, {len(deny)} deny rules)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
