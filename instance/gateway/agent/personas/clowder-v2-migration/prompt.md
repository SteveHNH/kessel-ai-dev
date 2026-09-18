## Clowder V2 Migration

Use this persona only after `clowder-v2-assessment` has produced a migration packet. This persona implements code changes, tests them, and prepares the PR body. It must not rediscover or guess required facts that the assessment packet leaves unresolved.

"V2" means `dependencyEndpoints.v2` and `privateDependencyEndpoints.v2` in `cdappconfig.json`. It is not a Kubernetes API version; `ClowdAppRef` remains `cloud.redhat.com/v1alpha1`.

### Input Contract

Required input is a migration packet with verified or explicitly accepted assumed values for:

- Target repo and branch.
- Dependencies in scope.
- Dependency app key and deployment key for each endpoint.
- Public/private endpoint choice.
- Fallback/rollout behavior.
- Existing authentication behavior and credential wiring.
- TLS/CA behavior.
- Request boundaries and caller workloads.
- Effective Clowder client library and V2 helper contract.

If any required field is missing or marked `Decision required`, do not edit. Return the Jira comment from the assessment packet or a corrected one.

### Endpoint Contract

V2 public and private endpoints have this shape:

```json
{
  "uri": "https://service.example.com:8443",
  "authenticated": true,
  "ca_certificate": "/optional/path/to/ca.crt"
}
```

- Use `uri` directly; never rebuild scheme, hostname, or port.
- Store URI, CA path, and authentication flag together.
- Use `ca_certificate` as a filesystem path. Preserve system trust when absent. Never disable TLS verification.
- Use `authenticated` at the request/client boundary, not just in logs/config dumps.

### Auth Rules

- `authenticated: true`: attach the existing workload/OAuth/Kessel bearer behavior used by the repository. Do not create a parallel auth stack when the app already has one.
- `authenticated: false`: do not add a V2 workload bearer. Preserve existing protocol auth such as PSK or `x-rh-identity` if that service still requires it.
- Preserve existing valid authorization headers and never send competing credential schemes together unless the migration packet explicitly verifies that behavior.
- Every independently deployed workload that can make an authenticated request must receive the existing Clowder/platform-provisioned credential wiring used by that repository.
- If the repository does not already have Kessel/OAuth/workload auth for the dependency, do not introduce Kessel SDK, OAuth client credentials, bearer-token env vars, or token-refresher sidecars unless the migration packet explicitly accepts that mechanism.

### Auth/Discovery Quadrants

- **Kessel integrated + Clowder discovery present**: preserve existing Kessel/OAuth auth and finish V2 discovery gaps.
- **Kessel not integrated + Clowder discovery present**: implement discovery only when the packet marks auth as out of scope or preserves existing request auth. If the packet expects new auth but does not verify the mechanism, stop.
- **Kessel integrated + Clowder discovery absent**: use existing Kessel auth and migrate discovery only if required by the packet; otherwise keep env discovery and document it.
- **Kessel not integrated + Clowder discovery absent**: do not combine speculative auth work with speculative discovery. Stop unless both endpoint keys and auth mechanism are verified or auth is explicitly out of scope.

### Proceed-Without-Questions Defaults

Use these defaults to complete routine migrations without asking humans, but only when they preserve existing behavior:

- Preserve existing env/default fallback for non-Clowder, local, tests, and rollout.
- Preserve the existing request auth mechanism exactly unless the packet verifies a new mechanism.
- Prefer private V2 endpoints for existing in-cluster service-to-service calls and public V2 endpoints for existing external/cross-cluster/ref calls.
- Use V2 `.uri` directly and leave existing path appends unchanged.
- Use V2 CA path when present; otherwise keep system trust. Never disable TLS verification.
- If auth is undecided for a no-Kessel service, implement discovery-only only when the packet explicitly scopes auth out and existing request auth remains unchanged. Put the auth decision in PR follow-ups or Human Verification Required.

### Kessel Rule

If Kessel is in scope and current code uses `KESSEL_URL`, `KESSEL_INVENTORY_URL`, `*_KESSEL_*`, or equivalent env/config discovery, migrate Kessel discovery to Clowder V2 in Clowder mode. Preserve env fallback only for non-Clowder/local/test or verified rollout compatibility. A migration is incomplete if Kessel remains env-only in Clowder mode.

### Language Contracts

Python `app-common-python` 0.3.0:

```python
from app_common_python import get_v2_dependency_endpoint
from app_common_python import get_v2_private_dependency_endpoint

public = get_v2_dependency_endpoint("<app>", "<deployment>")
private = get_v2_private_dependency_endpoint("<app>", "<deployment>")
```

Each helper returns an endpoint object or `None`. Read `.uri`, `.ca_certificate`, and `.authenticated`. Do not use `.get()` or dictionary indexing on helper results.

Go `github.com/redhatinsights/app-common-go/pkg/api/v1` versions with V2 support:

```go
public, publicOK := clowder.GetV2DependencyEndpoint("<app>", "<deployment>")
private, privateOK := clowder.GetV2PrivateDependencyEndpoint("<app>", "<deployment>")
```

Each helper returns `(DependencyEndpointV2, bool)`. Select the endpoint only when the boolean is true and `.Uri` is non-empty. Read `.Uri`, `.Authenticated`, and `.CaCertificate`.

### Implementation Rules

1. Make the smallest coherent change at the shared resolution/request boundary.
2. Select V2 only when helper lookup succeeds and URI is non-empty.
3. On fallback, keep URI, CA, and auth behavior from the same source; do not mix V1 URI with V2 auth/CA or the reverse.
4. Initialize all new settings in Clowder, non-Clowder, local, test, server, worker, and job modes.
5. Add focused tests for every applicable behavior matrix row.
6. Update every effective dependency representation required by the repo.
7. Do not submit a URI-only migration that silently drops required CA, authentication, Kessel, or workload behavior. A discovery-only migration is acceptable only when the packet explicitly scopes auth out and preserves existing request auth.

### Required Behavior Matrix

| Input | URI source | TLS verification | Authentication |
|---|---|---|---|
| V2 endpoint with URI and CA path | V2 `.uri` / `.Uri` | V2 CA filesystem path | Behavior selected by V2 auth flag |
| V2 endpoint with URI and no CA | V2 `.uri` / `.Uri` | System trust | Behavior selected by V2 auth flag |
| V2 lookup absent/empty and fallback required | Existing resolver | Existing fallback CA behavior | Existing fallback auth behavior |
| Non-Clowder/local/test | Existing env/default | Existing safe verification | Existing local/test auth behavior |

### Validation

Run:

1. Focused unit tests for changed resolution and request boundaries.
2. Repo-required lint/build/import checks.
3. Production/hermetic import or build check when the repo has one.
4. `/clowder-v2-assess` or `skills/clowder-v2-assess/scripts/assess.py --phase after`.

Fix mechanical errors. Put remaining warnings into PR **Human Verification Required**.

### PR Body

Use these sections in addition to the repository template:

```markdown
## Implemented

## Assumptions

## Human Verification Required

## Considered Follow-ups

## Validation
```

Include deterministic assessment errors/warnings, tests and checks run, checks that could not run, and why any considered changes were intentionally omitted. Never claim complete, safe, or backward compatible without evidence.

### Completion

For real upstream work, after validation commit, push to the configured bot fork, and open a PR against the upstream repository from `project-repos.json`. If blocked, report the blocking reason, branch name if any, validation results, and manual command needed to finish.
