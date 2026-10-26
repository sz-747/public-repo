# Public Repo

Public Repo is an agent skill that helps you share a project or skill on GitHub while keeping private information out.

Use it when you want to publish something from a private workspace, check a repository before making it public, or check later updates before pushing them. It looks for secrets, personal details, machine paths, and private settings in both the current files and past commits. You can supply a private list of names, hosts, and codes that must stay out.

The skill defines the release workflow, and a Python scanner checks files, history, and commit identities. Public files are separated from local settings, and the workflow checks a fresh clone to verify what was actually published.

```text
private source -> public copy -> scan + review -> publish -> check fresh clone
                                     ^
                             private deny list
```

The scanner has offline tests for files, history, identities, and local settings. It cannot guarantee that every private detail will be caught: the workflow also requires manual review and your approval to publish.

[MIT license](LICENSE)

**[AGENTS: READ THIS TO INSTALL AND SET UP PUBLIC REPO](INSTALL.md)**
