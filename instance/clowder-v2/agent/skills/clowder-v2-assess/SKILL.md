---
name: clowder-v2-assess
description: >
  Deterministically inventories and checks Clowder V2 consumer migrations,
  producing evidence and human-review warnings for the PR description.
when_to_use: >
  Run before and after any migration involving Clowder V2 dependency endpoints,
  ClowdAppRef consumers, dependencyEndpoints.v2, or privateDependencyEndpoints.v2.
user-invocable: true
allowed-tools:
  - "Bash(python3 .claude/skills/clowder-v2-assess/scripts/assess.py *)"
  - Read
---

## Workflow

From the target repository, run discovery before editing:

```bash
python3 .claude/skills/clowder-v2-assess/scripts/assess.py --phase before --repo . --output /tmp/clowder-v2-before.md
```

After implementation and tests, run validation:

```bash
python3 .claude/skills/clowder-v2-assess/scripts/assess.py --phase after --repo . --output /tmp/clowder-v2-after.md
```

Exit codes:

- `0`: no deterministic errors; warnings may still require human review.
- `1`: mechanical errors found. Fix them before presenting the migration as complete.
- `2`: the assessment itself could not run.

Read both reports. Use their evidence to build the PR certainty ledger. The helper checks syntax and repository evidence only; it does not decide application-specific authentication, rollout, or resource ownership.
