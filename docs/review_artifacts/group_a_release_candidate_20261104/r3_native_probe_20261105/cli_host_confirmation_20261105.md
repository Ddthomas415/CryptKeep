# Docker signature confirmation on the host

Bot relation: BOT_RULES; runtime configuration not checked.

Role: AUDITOR. Checked 2026-11-05T20:57:28Z, HEAD `82b5f216e`. One bounded
read-only host verification outside the earlier restricted environment. No
Docker execution, daemon contact, downloads, repairs or service changes.

**SHOWN:** Docker Desktop metadata still says 4.98.0, build 245422. The CLI
SHA256 before and after the host checks was
`e6bb967adc3e97c9a9027aa7a1b83691789630cb26a4bbcddd2e8353a8a89ea4`, identical
to the CLI in the earlier restricted-environment receipt. All three actual
`/usr/bin/codesign --verify --strict --verbose=2` checks returned exit 0 and
reported valid on disk and satisfying the designated requirement:

| Target | Host result |
|---|---|
| `/usr/bin/true` | Apple system control passed |
| `/Applications/Docker.app/Contents/Resources/bin/docker` | CLI passed |
| `/Applications/Docker.app` | App bundle passed |

The earlier failure did **not** reproduce on the host for the same CLI bytes.
This supersedes the earlier result as evidence about host signature verification;
it does not identify the exact restriction that produced the earlier error or
independently authenticate an upstream installer. A repair is not supported by
the current evidence. The stopped test receipt remains historically correct.

**Wrapper correction (O-110):** the first command wrapper expanded Perl's
`@ARGV` too early, leaving its inner program `alarm 8; exec `. Its printed
status markers were not evidence that verification ran and were discarded.
A local `printf` smoke test reproduced the interpolation and verified literal
passing of the child argument list. The corrected invocation produced actual
fingerprints, version/build and per-target verification output. There was one
actual host verification pass, with 8-second limits per command. No Linux fixture
ran. The outer wrapper's exit alone is not an acceptance signal.

**Next:** use the host-verified CLI digest as the proposed updated input for a
new, separately approved R3 attempt. The reviewed packet remains unchanged
(`9027d7ddcdca0b45c639c64156af15c32418cf221fdde890049a34434d84f95c`). Recheck
both hashes before any daemon calls. Keep the existing proposal's two metadata
checks, one cached-image disposable container, no network/downloads, 180-second
target including owned cleanup, and no automatic retry. Do not reset the prior
attempt or repair Docker to reach this test.

**UNVERIFIED:** daemon reachability, cached image availability, installed runtime
behavior, separate publisher-release/notarization proof, and Linux fixture results.
Source acceptance is unchanged; R3 remains INCOMPLETE. No source tests were run
because the operation was a read-only identity check, not a code change.

What do I know that could change the owner's decision that I have not yet said?
There is no current signature-based reason to replace Docker. Authorizing another
isolated test is distinct from authorizing a repair, restart or deployment.
