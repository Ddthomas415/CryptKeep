# Docker Compose Disposition Proof - 2026-08-24

## Scope

Read-only proof for the Docker-compose disposition portion of the deployment
backlog. No containers were started, stopped, built, pulled, or removed.

This does not close the server systemd installation proof.

## Decision Being Verified

`phase1_research_copilot/` is treated as an optional sidecar/archived companion,
not as a required root runtime dependency.

The root Docker Compose startup must therefore render without the companion
backend by default, while allowing the operator to opt into the sidecar
explicitly with `COMPOSE_PROFILES=phase1-companion`.

## Evidence

Command:

```bash
docker compose -f docker/docker-compose.yml config --services
```

Result:

```text
dashboard
```

Command:

```bash
COMPOSE_PROFILES=phase1-companion docker compose -f docker/docker-compose.yml config --services
```

Result:

```text
dashboard
backend
```

Command:

```bash
./.venv/bin/python -m pytest -q tests/test_companion_repo_dependency.py
```

Result:

```text
2 passed in 0.10s
```

## Conclusion

The Docker-compose disposition is resolved for the root runtime:

- default Compose startup does not require the companion backend;
- the companion backend remains available only through the explicit
  `phase1-companion` profile;
- the policy is documented in `docs/COMPANION_REPO_DEPENDENCY.md`;
- the behavior is pinned by `tests/test_companion_repo_dependency.py`.

Remaining deployment proof is server installation/post-install evidence for
the packaged systemd units. This checkpoint does not install units, reload
systemd, restart services, or assert host readiness.
