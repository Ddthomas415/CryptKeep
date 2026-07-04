# CryptKeep Server Secrets and Rotation Model

Status: `POLICY_DOCUMENTED`

## Purpose

Define how server-side secrets are introduced, used, rotated, and audited before
any capped-live deployment. This document does not authorize live trading or
prove that a server secret injection drill has been run.

## Scope

This model applies to:

- exchange API credentials;
- cloud provider API tokens;
- Tailscale or private-network enrollment material;
- alert delivery credentials and webhook URLs;
- GitHub Actions release/signing secrets;
- external AI provider keys when explicitly enabled;
- dashboard or operator authentication secrets.

Public paper-data runs that require no credentials remain out of scope, except
that they must not accidentally copy live credentials onto a paper host.

## Current Boundary

SHOWN:

- Desktop/paper operation may use OS keyring or environment variables.
- Hetzner paper-host guidance forbids copying live exchange credentials.
- External AI copilot guidance forbids sending secrets, tokens, private SSH
  material, or raw account credentials to providers.

UNVERIFIED:

- No capped-live server secret injection rehearsal has been executed.
- No server-side rotation drill has been recorded.
- No proof packet currently shows that live secrets stay out of logs, deployment
  records, and evidence artifacts during a real server deployment.

## Storage Authority

Use this order of preference:

1. Managed secret store or OS keyring on the target host.
2. Process environment injected by a supervised service manager.
3. Local `.env` file only for private, single-host operation when protected by
   filesystem permissions and explicitly excluded from Git.

Never store secrets in:

- Git-tracked files;
- campaign manifests;
- strategy YAML files;
- evidence JSON/JSONL;
- deployment records;
- shell command arguments;
- chat messages or work-log prose;
- screenshots or terminal captures.

## Injection Rules

Server deployment units must reference secret names, not secret values.

Acceptable examples:

- `EnvironmentFile=/etc/cryptkeep/cryptkeep.env` with `0600` permissions;
- `LoadCredential=` or an equivalent service-manager credential mechanism;
- OS-keyring lookup performed inside the process;
- GitHub Actions secrets for CI signing/release jobs only.

Before capped live, the launch packet must show:

- which mechanism is used on the server;
- file ownership and permissions if an environment file is used;
- a redacted status command proving required keys are present;
- no secret values in service files, logs, evidence, or deployment records.

## Rotation Triggers

Rotate immediately when:

- a token or key is pasted into chat, terminal output, Git, or a document;
- a host, laptop, or CI environment with secret access is compromised;
- a collaborator or tool no longer needs access;
- a provider reports suspicious activity;
- a branch or artifact accidentally exposes a credential-bearing config.

Rotate on a scheduled basis before capped live:

- cloud provider read/write tokens: short-lived, per provisioning window;
- exchange trading keys: at least quarterly or after every material access
  change;
- alert/webhook tokens: at least semiannually;
- CI signing/notarization secrets: according to provider certificate expiry and
  any release-automation incident.

## Rotation Procedure

1. Create the replacement credential at the provider with the minimum required
   scope.
2. Store it through the approved hidden prompt, secret store, or protected
   environment path.
3. Restart only the services that need the new credential.
4. Run a redacted status/preflight command that proves the credential is usable
   without printing it.
5. Revoke the old credential at the provider.
6. Record a decision/deployment note with provider, scope, operator, timestamp,
   verification command, and revocation confirmation. Do not record the secret.

For emergency exposure, revoke first unless doing so would make a running
paper/live safety loop blind. If immediate revoke would break safety visibility,
halt trading, preserve logs, then revoke.

## Required Redaction

Any operator-facing command that touches secrets must redact:

- token-like values;
- URLs with embedded credentials;
- authorization headers;
- private key material;
- webhook URLs;
- account IDs when combined with credentials.

Evidence and alert payloads may include non-secret labels such as provider name,
scope class, key-present boolean, last rotation date, and last verification
timestamp.

## Launch-Gate Proof Required

Before capped-live approval, record a proof packet that shows:

- a fresh server secret inventory with values redacted;
- one non-production rotation drill or a production rotation with revocation
  confirmation;
- a grep/log scan over the deployment packet and current evidence artifacts for
  known secret patterns;
- service restart or reload proof after rotation;
- exchange/cloud provider scope confirmation;
- rollback path if a rotated credential fails.

Until that packet exists, server secret handling remains a capped-live blocker.

