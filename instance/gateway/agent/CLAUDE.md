# Gateway Instance

## Routing

All work → `gateway-config` persona. Repo: `app-interface` (GitLab). MRs not PRs. Branch: `master`.

Tickets involving Clowder Dependency Endpoints or clowder migrations -> `clowder-v2-assessment` first. Only hand off to `clowder-v2-migration` when assessment produces a verified migration packet with no decision-required fields. For ref provisioning or cutover, also read `personas/clowder-v2/provisioning.md`.

## Ticket gate

Claim ticket = OK. But validate info BEFORE opening MR.

**NSGW needs:** service name, cluster(s), k8s svc name, API path, HTTP/gRPC, port (if ≠8000/9800), gRPC svc name (if gRPC).

**EWGW needs:** NSGW fields + principal(s) (`<issuer>/<subject>`), methods (if gRPC/restricted).

**Missing info →** claim ticket, comment on Jira listing missing fields, tag reporter. May open draft MR with placeholders. Do NOT mark done. Work next ticket.

## Done = confirmed working

Merged MR ≠ done. Done = reporter confirms working OR Jira moved to Closed.

On merge → move Jira to Release Pending + comment tagging reporter: "@reporter MR merged. Please confirm the route works as expected so I can close this." Do NOT close. Wait for confirmation.

## Knowledge order

1. Search memory for matching recipe
2. Match → use it, skip SOPs
3. No match → read SOPs: `docs/tenant-services/console.redhat.com/app-sops/hcc/`
4. SOPs insufficient → Jira comment, ask human

## Memory rules

Store **recipes** (general patterns). Never specific instances.

Good: "gRPC NSGW needs GRPCRoute + method_service var"
Bad: "Added quickstarts to hccs01ue1 with backend_name quickstarts"

New pattern found → store recipe. Learned refinement → update existing recipe.
