# GitHub Auth Runbook

Date: 2026-08-11

## Purpose

This runbook documents the supported local GitHub authentication boundary for
repo publishing work. It is policy/runbook-only and does not change any Git,
GitHub CLI, CI, branch-protection, credential, or repository behavior.

## Current Problem

Local `gh` and Git credentials can drift independently from repo code. When the
GitHub CLI token is invalid, expired, revoked, or missing, publish work can get
stuck in interactive prompts such as:

- preferred Git protocol: `HTTPS` or `SSH`;
- GitHub CLI authentication method: browser login or token paste.

That prompt is an environment/auth state problem, not a code-review blocker and
not evidence that a repo patch is wrong.

## Supported Local Protocol

Use HTTPS for this repo unless a separate operator decision switches the host to
SSH.

Supported local recovery sequence:

```bash
gh auth status
gh auth login --git-protocol https --web
gh auth setup-git
gh auth status
```

If `gh auth status` reports a stale account or invalid token, clear only the
GitHub CLI auth state, then repeat the supported login:

```bash
gh auth logout --hostname github.com
gh auth login --git-protocol https --web
gh auth setup-git
```

## Token Rules

- Do not paste GitHub tokens into chat, docs, work logs, commits, screenshots,
  or issue/PR text.
- Do not store tokens in this repository or under `.cbp_state/`.
- Prefer browser login for local interactive recovery.
- If a token must be used, paste it only into the GitHub CLI prompt or a local
  OS credential manager prompt, never into Codex/chat.
- Treat the ChatGPT Codex Connector/GitHub app and the local `gh` CLI as
  separate auth surfaces. Fixing one does not prove the other is authenticated.

## Publish Boundary

Authentication repair is allowed to restore the operator's ability to push or
open PRs, but it does not authorize:

- force-pushing over another branch without an explicit operator instruction;
- bypassing branch protection;
- merging with failing checks unless explicitly accepted;
- changing secrets, GitHub app permissions, or organization policy;
- changing repo code to work around a local credential problem.

## Verification

A local auth repair is considered verified only when:

- `gh auth status` reports an authenticated `github.com` account;
- `git remote -v` still points to the intended repository;
- a dry metadata command such as `gh repo view --json nameWithOwner,url`
  succeeds.

Do not treat this as permanent. GitHub sessions, tokens, browser grants, SSO,
and app permissions can expire or be revoked outside the repo.

## Hetzner Pull Auth

Hetzner checkout sync is a separate auth surface from the local laptop `gh`
session. Local `gh auth status` does not prove `/srv/cryptkeep/app` can fetch
from GitHub.

Observed failure mode on 2026-09-02:

- the Hetzner checkout is owned by `cryptkeep`;
- direct `cryptkeep@100.86.128.9` SSH can require an interactive Tailscale
  browser check;
- root SSH can reach the host, but root Git sees `/srv/cryptkeep/app` as a
  dubious-ownership repository unless commands run as `cryptkeep`;
- running Git as `cryptkeep` reaches the correct repository but cannot fetch
  the private HTTPS remote noninteractively;
- `gh` is not installed for the host user, and no GitHub SSH deploy key was
  present under `~cryptkeep/.ssh/`.

Preferred permanent fix:

1. Generate or install a dedicated SSH deploy key owned by `cryptkeep`.
2. Add only the public key to `Ddthomas415/CryptKeep` as a read-only deploy key.
3. Verify GitHub's SSH host key against GitHub's published documentation, then
   add it to `~cryptkeep/.ssh/known_hosts`.
4. Change only the Hetzner repo remote to
   `git@github.com:Ddthomas415/CryptKeep.git`.
5. Run `git fetch origin master` and `git merge --ff-only origin/master` as
   `cryptkeep`, with no service restart.

Do not copy a personal GitHub CLI token or browser token to Hetzner. Do not
enable deploy-key write access. Do not use a machine user or PAT unless the
deploy-key path is rejected by operator policy.

Explicit approval text for this host mutation:

```text
I approve provisioning a read-only GitHub deploy key on Hetzner for
/srv/cryptkeep/app pulls, adding the public key to Ddthomas415/CryptKeep
without write access, switching the Hetzner repo remote to SSH, and
fast-forwarding the checkout with no service restart.
```

This is high-risk credential/deploy work. Until that approval is given, the
safe action is documentation only.

## When To Stop

Stop and ask the operator for action if:

- browser login requires a device/browser step the operator must complete;
- SSO or organization approval is required;
- GitHub asks for a token and no local secure token source is available;
- the intended repository or account differs from `Ddthomas415/CryptKeep`.
