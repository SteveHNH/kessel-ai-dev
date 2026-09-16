# kessel-ai-dev

Custom bot runner for the Kessel team, built on [dev-bot](https://github.com/RedHatInsights/platform-frontend-ai-dev) (platform-frontend-ai-dev).

This repo contains instance-specific configuration only — the bot code lives in the `dev-bot` submodule.

## Structure

```
├── setup.sh                          # Instance setup (runs during Docker build)
├── deploy/
│   └── template.yaml                 # OpenShift deploy template (bot-only)
├── instance/
│   └── kessel/
│       └── agent/
│           ├── mcp.json              # MCP server config (Jira)
│           ├── project-repos.json    # Repos this instance works on
│           └── personas/
│               ├── backend/          # inventory-api, inventory-consumer
│               ├── sdk-go/           # kessel-sdk-go
│               ├── sdk-py/           # kessel-sdk-py
│               ├── sdk-java/         # kessel-sdk-java
│               ├── sdk-ruby/         # kessel-sdk-ruby
│               ├── sdk-node/         # kessel-sdk-node
│               ├── sdk-browser/      # kessel-sdk-browser
│               └── tooling/          # kessel-kafka-connect
└── dev-bot/                          # Submodule → platform-frontend-ai-dev
```

## Jira labels and repos

The bot picks up tickets that have **two kinds of labels**:

1. **Primary label** — set via `BOT_LABEL` in `deploy/template.yaml`. Marks tickets as eligible for this deployment.
2. **`repo:<name>`** — on the Jira ticket. Tells the bot which repo(s) to clone. Must match a key in the instance's `project-repos.json`.

| Jira primary label | Instance config | `repo:` label | Upstream repo |
|--------------------|-----------------|---------------|---------------|
| `hcc-ai-kessel` | `instance/kessel/agent/` | `repo:inventory-api` | [project-kessel/inventory-api](https://github.com/project-kessel/inventory-api) |
| `hcc-ai-kessel` | `instance/kessel/agent/` | `repo:inventory-consumer` | [project-kessel/inventory-consumer](https://github.com/project-kessel/inventory-consumer) |
| `hcc-ai-kessel` | `instance/kessel/agent/` | `repo:kessel-kafka-connect` | [project-kessel/kessel-kafka-connect](https://github.com/project-kessel/kessel-kafka-connect) |
| `hcc-ai-kessel` | `instance/kessel/agent/` | `repo:kessel-sdk-go` | [project-kessel/kessel-sdk-go](https://github.com/project-kessel/kessel-sdk-go) |
| `hcc-ai-kessel` | `instance/kessel/agent/` | `repo:kessel-sdk-py` | [project-kessel/kessel-sdk-py](https://github.com/project-kessel/kessel-sdk-py) |
| `hcc-ai-kessel` | `instance/kessel/agent/` | `repo:kessel-sdk-java` | [project-kessel/kessel-sdk-java](https://github.com/project-kessel/kessel-sdk-java) |
| `hcc-ai-kessel` | `instance/kessel/agent/` | `repo:kessel-sdk-ruby` | [project-kessel/kessel-sdk-ruby](https://github.com/project-kessel/kessel-sdk-ruby) |
| `hcc-ai-kessel` | `instance/kessel/agent/` | `repo:kessel-sdk-node` | [project-kessel/kessel-sdk-node](https://github.com/project-kessel/kessel-sdk-node) |
| `hcc-ai-kessel` | `instance/kessel/agent/` | `repo:kessel-sdk-browser` | [project-kessel/kessel-sdk-browser](https://github.com/project-kessel/kessel-sdk-browser) |
| `hcc-ai-kessel` | `instance/kessel/agent/` | `repo:parsec` | [project-kessel/parsec](https://github.com/project-kessel/parsec) |
| `hcc-ai-kessel` | `instance/kessel/agent/` | `repo:kessel-ai-dev` | [project-kessel/kessel-ai-dev](https://github.com/project-kessel/kessel-ai-dev) |
| `hcc-ai-kessel` | `instance/kessel/agent/` | `repo:docs` | [project-kessel/docs](https://github.com/project-kessel/docs) |
| `hcc-ai-kessel` | `instance/kessel/agent/` | `repo:starlark-unified-schema` | [project-kessel/starlark-unified-schema](https://github.com/project-kessel/starlark-unified-schema) |

To add a repo:

1. Fork it under the bot account and add an entry to the instance's `project-repos.json`:

   ```json
   "my-repo": {
     "url": "https://github.com/platex-rehor-bot/my-repo",
     "upstream": "https://github.com/project-kessel/my-repo.git"
   }
   ```

2. Label the Jira ticket with `repo:my-repo` (bare name) or `repo:project-kessel/my-repo` (org-prefixed — resolved via the upstream URL).

3. Rebuild and redeploy the image so the updated `project-repos.json` is baked in.

Multiple `repo:` labels on one ticket are supported for cross-repo work. A ticket without a matching `repo:` label is skipped.

## Build

```bash
git submodule update --init --recursive
docker build -f dev-bot/Dockerfile.runner -t kessel-ai-dev:local .
```

## Updating dev-bot

```bash
cd dev-bot && git pull origin master && cd ..
git add dev-bot
git commit -m "chore: update dev-bot submodule"
```

## CI/CD

Built and deployed via [Konflux](https://konflux-ci.dev/). Pipeline definitions live in `.tekton/`.

- **Push to main** → builds and pushes to the production Quay repo
- **Pull requests** → builds a temporary image to `quay.io/redhat-user-workloads/...` (5-day expiry)

## Deployment

Deployed to the shared `platform-frontend-ai-dev` namespace via app-interface. Uses the shared proxy, memory server, and Vault secrets from the primary instance. See the deploy template for resource configuration.

Default `BOT_CONFIG_PATH` is `instance/kessel`. Set this in app-interface if overriding the baked-in config with a remote config repo.

See [dev-bot/docs/onboarding-new-instance.md](dev-bot/docs/onboarding-new-instance.md) for full onboarding steps.
