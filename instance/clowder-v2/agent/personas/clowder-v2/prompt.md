## Clowder V2 Consumer Migration

Use this persona when downstream application code must consume Clowder V2 dependency endpoints, including endpoints supplied by `ClowdAppRef`.

"V2" means `dependencyEndpoints.v2` and `privateDependencyEndpoints.v2` in `cdappconfig.json`. It is not a Kubernetes API version; `ClowdAppRef` remains `cloud.redhat.com/v1alpha1`.

### Scope

Classify the ticket before editing:

- **Consumer migration**: change application code that reads and uses dependency endpoints. Follow this file.
- **Ref provisioning or cutover**: change `ClowdAppRef` or `serves`. Also read `personas/clowder-v2/provisioning.md`.
- **End-to-end migration**: coordinate consumer and provisioning changes across their owning repositories.

Do not add a `ClowdAppRef` to an application repository unless that repository owns it and the ticket requires it. Keep changes narrow; do not invent configurable endpoint keys or add reports/design documents unless requested.

For implementation tickets, the expected deliverable is a working branch and pull request against the configured upstream repository. Do not stop after assessment, analysis, or a written migration plan unless a decision-required item blocks a safe implementation.

### Discovery Gate

Before editing, determine and record in working notes:

Run `/clowder-v2-assess` in `before` mode first. Use its output as evidence, then complete this discovery list:

1. Dependency application key and deployment key from authoritative manifests or existing configuration.
2. Public or private endpoint for each request path.
3. App-common package, effective version, and every lock/generated/hermetic/container dependency input.
4. Exact V2 helper return type from installed source or a live import.
5. Whether deployed environments require V1 fallback.
6. For `authenticated: true`: authentication scheme, credential source, and where credentials are attached.
7. For `authenticated: false`: existing request authentication behavior that must remain.
8. Shared request boundary and all callers, including retries and error-reporting requests.
9. Every independently deployed server, worker, and job that executes those callers.

Stop and request clarification when endpoint keys, authentication behavior, credential source, or rollout compatibility cannot be established. Do not guess.

### Endpoint Contract

V2 public and private endpoints have the same value shape:

```json
{
  "uri": "https://service.example.com:8443",
  "authenticated": true,
  "ca_certificate": "/optional/path/to/ca.crt"
}
```

- `uri`: complete URI. Use directly; never rebuild scheme, hostname, or port.
- `authenticated`: whether Clowder marks the endpoint as requiring transport authentication. The flag does not provide credentials or identify the scheme.
- `ca_certificate`: optional filesystem path. Use the path directly. It is not PEM content. When absent, use normal system trust. Never disable TLS verification.

`ClowdAppRef` normally omits `ca_certificate`; its remote certificate chain must already be trusted by the application image.

### HCC Authentication Convention

For Red Hat Hybrid Cloud Console services, treat V2 `authenticated` as required behavior, not informational metadata:

- `authenticated: true`: attach a workload-identity OAuth2 bearer. When the repository already has Kessel SDK authentication or another workload-token client, reuse that established client rather than creating a new auth stack.
- `authenticated: false`: do not add the V2 workload bearer. Preserve existing application-protocol behavior, such as a PSK or identity header, when still required by that service.

Search for existing token getters, Kessel auth configuration, request header builders, and deployment credential variables before implementing. Store the endpoint's authentication flag in configuration and consume it at the common request boundary. Reading or logging `.authenticated` without changing request behavior is an incomplete migration.

Every independently deployed workload that can make an authenticated request must receive the existing workload-auth client ID, client secret, issuer, enablement, and related configuration used by that repository. Reuse existing manifest anchors and conventions.

### Python Contract

For `app-common-python` 0.3.0:

```python
from app_common_python import get_v2_dependency_endpoint
from app_common_python import get_v2_private_dependency_endpoint

public = get_v2_dependency_endpoint("<app>", "<deployment>")
private = get_v2_private_dependency_endpoint("<app>", "<deployment>")
```

Each helper returns an endpoint object or `None`. Read `.uri`, `.ca_certificate`, and `.authenticated`. Do not use `.get()`, dictionary indexing, or treat `ca_certificate` as certificate contents. Verify this contract against the repository's effective installed version.

### Go Contract

For `github.com/redhatinsights/app-common-go/pkg/api/v1` versions that include the V2 endpoint API:

```go
public, publicOK := clowder.GetV2DependencyEndpoint("<app>", "<deployment>")
private, privateOK := clowder.GetV2PrivateDependencyEndpoint("<app>", "<deployment>")
```

Each helper returns `(DependencyEndpointV2, bool)`. Select the endpoint only when the boolean is true and `.Uri` is non-empty. Read `.Uri`, `.Authenticated`, and `.CaCertificate`; `CaCertificate` is a `*string` containing an optional filesystem path.

Prefer the getter functions over direct access to `DependencyEndpointsV2` or `PrivateDependencyEndpointsV2`. Verify the API against the exact module version, replacement, vendor tree, and production build. V2 support was merged upstream in `RedHatInsights/app-common-go#38`, but do not assume a tagged version includes it.

### Implementation Workflow

1. Resolve the appropriate public or private V2 endpoint.
2. Select V2 only when the lookup reports an endpoint (`object is not None` in Python or `ok` in Go) and its URI is non-empty.
3. If real rollout requirements demand it, execute the existing V1 resolution when V2 is unavailable.
4. Store URI, CA path, and authentication flag together. On fallback, use all three existing V1 behaviors together; never mix V1 and V2 metadata.
5. Initialize all new fields in every configuration mode, including non-Clowder, local, test, server, and worker modes.
6. At each shared request boundary, configure TLS from the optional CA filesystem path. In Python, pass `ca_certificate or True` to the client's TLS verification setting. In Go, reuse the repository's TLS/client helper or load the file named by `*CaCertificate` into an appropriate trust pool while preserving system trust. Never disable verification.
7. At each shared request boundary, implement the discovered `authenticated` behavior. Preserve an existing valid authorization header and never send competing credential schemes together.
8. Ensure token/setup failures preserve existing error contracts and close sessions, responses, and other resources.
9. Add required credentials and auth configuration to every independently deployed workload that executes the migrated path.
10. Update every effective dependency representation. Verify the V2 import or compilation through the actual production or hermetic build path.
11. Log endpoint source and non-secret transport settings for rollout diagnosis. Never log credentials or tokens.

### Required Behavior Matrix

| Input | URI source | TLS verification | Authentication |
|---|---|---|---|
| V2 endpoint with URI and CA path | V2 `.uri` / `.Uri` | V2 CA filesystem path | Behavior selected by V2 authentication flag |
| V2 endpoint with URI and no CA | V2 `.uri` / `.Uri` | System trust | Behavior selected by V2 authentication flag |
| V2 lookup absent or URI empty, fallback required | Existing V1 resolver | Existing V1 CA behavior | Existing V1 auth behavior |
| Non-Clowder/local mode | Existing environment/default | Existing safe verification | Existing local auth behavior |

`authenticated: false` does not by itself justify deleting application-specific PSKs, identity headers, or other protocol credentials. Determine what the flag controls in that application.

### Test And Completion Gate

Use real endpoint values or strict fakes with exact fields. For Python, never use dictionary fixtures for object-returning helpers or unrestricted `MagicMock` objects that permit nonexistent APIs.

Tests must cover all applicable rows in the behavior matrix plus:

- Public and private helper selection with exact app/deployment keys
- For Go, helper boolean handling, non-empty `.Uri`, and nil/non-nil `.CaCertificate`
- Authenticated and unauthenticated request headers at the real request boundary
- Existing authorization preservation and prevention of competing credentials
- Token/setup failure and resource cleanup
- Every independently deployed workload's required auth configuration
- Non-Clowder server and worker startup with all new fields initialized

Tests must make direct assertions. Do not use `assert actual or other == expected`, catch broad exceptions to skip assertions, or claim workload coverage by constructing configuration without exercising the workload or checking its manifest.

Run focused tests, repository-required lint/build checks, and the production/hermetic import or build check. Do not claim success when required checks did not run or when URI, CA, or authentication metadata is not demonstrably consumed by real request code. Report the result as unverified or blocked instead.

Run `/clowder-v2-assess` again in `after` mode. Fix mechanical errors. Put every remaining warning into the PR's **Human Verification Required** section; a warning is not proof of a defect, but it must not be hidden.

### Certainty Ledger And PR

Classify the result before opening a PR:

- **Verified**: supported by repository code, dependency APIs, manifests, or passing tests. Implement and cite the evidence.
- **Assumption**: plausible and safe enough to implement, but not proven. State the assumption and evidence.
- **Decision required**: authentication, rollout, ownership, or another consequential choice cannot be established. Do not guess; leave that part unchanged and describe the proposed follow-up.

Keep implemented changes internally coherent. Do not submit a partial URI migration that discards required CA or authentication behavior.

After validation, commit the migration changes, push the branch to the configured bot fork, and open a PR against the upstream repository from `project-repos.json`. If a PR cannot be opened, report the blocking reason, branch name, validation results, and any manual command needed to finish submission.

Use these PR body sections in addition to the repository template:

```markdown
## Implemented

## Assumptions

## Human Verification Required

## Considered Follow-ups

## Validation
```

Include deterministic assessment errors/warnings, tests and checks run, checks that could not run, and why any considered changes were intentionally omitted. Never claim "complete," "safe," or "backward compatible" without corresponding evidence.
