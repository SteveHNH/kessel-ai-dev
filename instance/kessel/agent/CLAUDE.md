# Kessel Instance — Additional Instructions

## Persona routing

When loading personas (workflow step 6), use the repo key from `project-repos.json` / `repo:` label. **Repo key wins over generic tech-stack heuristics** (`go.mod` → backend, `package.json` → frontend, etc.).

| Repo key | Persona | Do NOT load |
|----------|---------|-------------|
| `inventory-api` | `backend` | — |
| `inventory-consumer` | `backend` | — |
| `kessel-kafka-connect` | `tooling` | `backend` |
| `kessel-sdk-go` | `sdk-go` | `backend` |
| `kessel-sdk-py` | `sdk-py` | `backend` |
| `kessel-sdk-java` | `sdk-java` | `backend` |
| `kessel-sdk-ruby` | `sdk-ruby` | `backend` |
| `kessel-sdk-node` | `sdk-node` | `frontend` |
| `kessel-sdk-browser` | `sdk-browser` | `frontend` |
| `parsec` | `parsec` | `backend` |
| `kessel-ai-dev` | `infra` | `backend`, `tooling` |
| `docs` | `docs` | `backend`, `infra`, `tooling` |
| `starlark-unified-schema` | `starlark` | `backend` |

For `kessel-sdk-*` repos, load **only** the mapped persona. Do not load `backend`, `frontend`, or other SDK language personas.
For `parsec`, load **only** the `parsec` persona. Do not load `backend`.
For `kessel-ai-dev`, load **only** the `infra` persona. Do not load `backend` or `tooling`.
For `docs`, load **only** the `docs` persona. Do not load `backend`, `infra`, or `tooling`.
For `starlark-unified-schema`, load **only** the `starlark` persona. Do not load `backend`.

## Version Management

This instance has **nvm** (Node) and **goenv** (Go) version managers installed. Use them to match the version required by each repo.

### Node.js (nvm)

Before working on a repo with `package.json`, check its `.nvmrc` or `engines.node` field and switch if needed:

```bash
nvm use          # reads .nvmrc if present
nvm install 20   # install + switch to Node 20
nvm use default  # back to default (22)
```

Default: Node.js 22 LTS. Available globally via `/usr/local/bin/node`.

### Go (goenv)

Before working on a repo with `go.mod`, check the `go` directive and switch if needed:

```bash
goenv versions                    # list installed versions
goenv install 1.23.0              # install a new version
goenv global 1.23.0               # set as default
goenv local 1.24.2                # set for current directory only
```

Pre-installed: Go 1.24.2 (default), 1.25.7. Available globally via `/usr/local/bin/go`.

### When to switch

- `go.mod` says `go 1.23` → `goenv install 1.23.x && goenv local 1.23.x`
- `.nvmrc` says `20` → `nvm use 20` (installs automatically if missing)
- No version file → use the defaults

### Python

Python 3.12 is the default (`python3`). SDK repos may require 3.11+ per `pyproject.toml`.

### Java / Ruby

Java (Maven) and Ruby (Bundler) are not pre-installed in this image. For `kessel-sdk-java` and `kessel-sdk-ruby`, run validation in CI if local tooling is unavailable. Do not block on missing local JDK/Ruby unless setup has been added to `setup.sh`.
