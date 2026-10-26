"""Offline tests for scripts/scan_public.py. Each test builds a throwaway Git repo; values planted are fake."""
import io
from contextlib import redirect_stderr, redirect_stdout
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / 'scripts'))
import scan_public as sp  # noqa: E402

NOREPLY = '1+tester@users.noreply.github.com'
PRIVATE = 'me@private.dev'  # fake address for tests; public-scan: allow
FAKE_KEY = 'ghp_' + 'a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8'


class Repo:
    def __init__(self, root, email=NOREPLY):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.run('init', '-q', '-b', 'main')
        self.run('config', 'user.name', 'tester')
        self.run('config', 'user.email', email)
        self.run('config', 'core.autocrlf', 'false')

    def run(self, *args):
        subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True)

    def commit(self, files, message='change'):
        for name, body in files.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if body is None:
                self.run('rm', '-q', name)
            else:
                path.write_bytes(body if isinstance(body, bytes) else body.encode('utf-8'))
                self.run('add', name)
        self.run('commit', '-q', '-m', message)


def cats(findings):
    return {f['category'] for f in findings}


class ScanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Repo(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def scan(self, deny=(), allow=(), history=True):
        return sp.scan(self.repo.root, [sp.re.compile(d, sp.re.I) for d in deny], list(allow), history)[1]

    def test_clean_repo(self):
        self.repo.commit({'README.md': '# Demo\nMail hello@example.com.\n', '.env.example': 'API_KEY=\n',
                          '.gitignore': '.env\n'})
        self.assertEqual(self.scan(), [])

    def test_secret_is_redacted(self):
        self.repo.commit({'config.js': f'const t = "{FAKE_KEY}";\n'})
        found = [f for f in self.scan() if f['category'] == 'secret: GitHub token']
        self.assertEqual(found[0]['where'], 'config.js:1')
        self.assertNotIn(FAKE_KEY, found[0]['text'])

    def test_deny_list_email_and_path(self):
        self.repo.commit({'notes.md': 'Ask Jane Roe at jane@realco.io, files in C:\\Users\\jane\\proj\n'})  # public-scan: allow
        self.assertEqual(cats(self.scan(deny=['jane roe'])), {'deny-list', 'email', 'machine path'})

    def test_secret_removed_later_is_still_in_history(self):
        self.repo.commit({'a.txt': f'token {FAKE_KEY}\n'})
        self.repo.commit({'a.txt': 'nothing here\n'}, 'clean up')
        found = self.scan()
        self.assertTrue(any(f['where'].startswith('history ') and f['category'] == 'secret: GitHub token' for f in found))
        self.assertEqual(self.scan(history=False), [])

    def test_commit_message_and_identity(self):
        other = Repo(Path(self.tmp.name) / 'other', email=PRIVATE)
        other.commit({'x.txt': 'hi\n'}, 'Code for ACME-42')
        found = sp.scan(other.root, [sp.re.compile('ACME-42')], [], True)[1]
        self.assertIn(('commit identity', PRIVATE), {(f['category'], f['text']) for f in found})
        self.assertIn('history', {f['where'].split(' ')[0] for f in found if f['category'] == 'deny-list'})
        self.assertNotIn('commit identity', cats(sp.scan(other.root, [], [PRIVATE], True)[1]))

    def test_risky_files_and_allow_marker(self):
        self.repo.commit({'.env': 'X=1\n', 'data/app.sqlite': b'\0bin', 'deploy/.vercel/project.json': '{}',
                          'doc.md': 'Example: me@corp.com  <!-- public-scan: allow -->\n'})
        risky = {f['where'] for f in self.scan() if f['category'] == 'risky file'}
        self.assertEqual(risky, {'.env', 'data/app.sqlite', 'deploy/.vercel/project.json'})
        self.assertNotIn('email', cats(self.scan()))

    def test_placeholders_are_not_secrets(self):
        self.repo.commit({'.gitignore': '.env*\n!.env.example\n', '.env.example': 'SESSION_SECRET=change-me\nDATABASE_URL=${DATABASE_URL}\nAPI_TOKEN=<your token>\n',
                          'cfg.py': 'PASSWORD = os.environ["PASSWORD"]\n',
                          'auth.js': '// a missing secret: sessions would break\nconst token = sign(payload, 3600);\n'})
        self.assertEqual(self.scan(), [])
        self.repo.commit({'deploy.sh': 'SESSION_SECRET=9f2c41aa07be55d1\n'})  # fake; public-scan: allow
        self.assertIn('secret: assigned secret', cats(self.scan()))

    def test_skill_links_that_stay_private(self):
        self.repo.commit({
            'SKILL.md': ('---\nname: demo\n---\nSee [refs](references/guide.md), [folder](references/), '
                         '[top](/README.md#use), [web](https://example.com/x) and [mail](mailto:a@example.com).\n'
                         'Rules in [soul](../../SOUL.md) and [sibling](../deep-research/SKILL.md), '
                         'related: [[deep-research]].\n```md\n[example](not/here.md)\n```\n'
                         'Inline examples like `[[name]]` and `[x](gone.md)` are not links.\n'),
            'references/guide.md': 'Back to [skill](../SKILL.md).\n',
            'README.md': '# Demo\n'})
        found = {(f['category'], f['text']) for f in self.scan()}
        self.assertEqual(found, {('broken link', '../../SOUL.md'), ('broken link', '../deep-research/SKILL.md'),
                                 ('wikilink', '[[deep-research]]')})

    def test_local_overlay(self):
        self.repo.commit({'.env.example': 'API_TOKEN=\n', 'config.example.json': '{}\n', '.gitignore': '.env\n',
                          'local/aliases.md': 'work = some path\n', '.claude/settings.local.json': '{}\n'})
        found = {(f['category'], f['where']) for f in self.scan()}
        self.assertEqual(found, {('overlay not ignored', 'config.example.json'),
                                 ('overlay committed', 'local/aliases.md'),
                                 ('overlay committed', '.claude/settings.local.json')})

    def test_control_character(self):
        self.repo.commit({'guide.md': 'Run\tthe\x07 script\n'})
        self.assertIn('control character', cats(self.scan()))

    def test_cli_exit_codes(self):
        self.repo.commit({'ok.md': 'fine\n'})
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            self.assertEqual(sp.main(['--repo', str(self.repo.root), '--no-default-deny']), 0)
        self.assertIn('clean: 1 tracked files', out.getvalue())
        self.assertIn('no private deny list', err.getvalue())
        self.repo.commit({'bad.md': 'reach me: someone@private.dev\n'})  # public-scan: allow
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(sp.main(['--repo', str(self.repo.root), '--no-default-deny']), 1)
        with redirect_stderr(io.StringIO()):
            self.assertEqual(sp.main(['--repo', str(Path(self.tmp.name) / 'missing'), '--no-default-deny']), 2)

    def test_deny_list_overlay_lookup(self):
        """The deny list is read from outside the repo: env var first, then the per-user config file."""
        self.repo.commit({'README.md': 'Built by Codename Falcon.\n'})
        overlay = Path(self.tmp.name) / 'overlay'
        (overlay / 'public-repo').mkdir(parents=True)
        (overlay / 'public-repo' / 'deny.txt').write_text('# private\ncodename falcon  # project name\n')
        saved = {k: os.environ.get(k) for k in ('PUBLIC_REPO_DENY', 'XDG_CONFIG_HOME')}
        try:
            os.environ.pop('PUBLIC_REPO_DENY', None)
            os.environ['XDG_CONFIG_HOME'] = str(overlay)
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(sp.main(['--repo', str(self.repo.root), '--no-history']), 1)
            self.assertIn('deny-list', out.getvalue())
            os.environ['PUBLIC_REPO_DENY'] = str(overlay / 'missing.txt')
            with redirect_stderr(io.StringIO()):
                self.assertEqual(sp.main(['--repo', str(self.repo.root)]), 2)
        finally:
            for k, v in saved.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)


if __name__ == '__main__':
    unittest.main()
