## Kessel Docs Guidelines

You are working on `project-kessel/docs`, the public Kessel documentation site. This
repository is an Astro 5 and Starlight site with TypeScript, Tailwind CSS, Zod
frontmatter validation, Mermaid diagrams, and the `starlight-openapi` integration.
Treat it as a documentation project, not a runtime service. Follow the repository's
`AGENTS.md`, `CLAUDE.md`, and linked guidelines as the source of truth.

### Before changes

1. Read the ticket and its acceptance criteria. Escalate if the requested content or
   target audience is unclear.
2. Read `AGENTS.md`, `CLAUDE.md`, and the relevant guidance under `src/content/docs/`
   and `src/examples/` before editing content.
3. Read `docs/sources.yaml` before deriving documentation from another repository. Use
   its repository metadata and URLs to locate source code and API definitions.
4. Keep changes within the requested documentation scope. Do not modify source service
   repositories as part of a docs change unless the ticket explicitly requires it.

### Public documentation boundary

- This repository contains public Kessel documentation for external service providers.
- Do not add Red Hat-specific credentials, hosted-environment configuration, internal
  onboarding, operational runbooks, monitoring procedures, or other private content.
- Internal content belongs in the separate InScope documentation repository. Escalate
  when a request mixes public and internal documentation.

### Content conventions

- Use `.mdx` when a page needs Astro components such as `Aside`, `Tabs`, `CodeExamples`,
  or `LinkCard`; use `.md` for plain Markdown.
- Include `title` and `description` in every page's frontmatter and use `sidebar.order`
  when navigation ordering is needed.
- Follow the Diataxis model and place current content under the appropriate
  `building-with-kessel` or `running-kessel` section. Put deprecated v1beta1 material
  under `building-with-kessel/archive/` with a deprecation notice.
- New API documentation must use v1beta2 paths and namespaces. Do not introduce
  v1beta1 references outside the archive.
- The HTTP API reference is generated from the upstream inventory-api OpenAPI schema.
  Do not vendor or duplicate that schema in this repository.

### Code examples and security

- Keep important example code, including error handling, inside the region markers
  consumed by the `CodeExamples` component.
- Use the established region syntax for each language and preserve the repository's
  example naming conventions.
- Never include real credentials. Use placeholders such as `your-client-id` and
  `<PASSWORD>`.
- TLS examples must load CA certificates and must not disable certificate verification.

### Validation

- Check the Node.js version requirements before running Node commands and use the
  instance's nvm guidance when a version file or engine constraint is present.
- Install dependencies when needed, then run `npm run build`. This runs `astro check`
  and `astro build` and matches the pull request CI gate.
- Run `./scripts/check-links.sh` when changing external documentation links, if the
  script is available in the checkout.
- Fix TypeScript errors, frontmatter validation errors, broken references, and build
  failures before opening a pull request.

### What not to do

- Do not add backend, database, or application runtime code to this repository.
- Do not place internal Red Hat operational content in the public site.
- Do not duplicate protobuf definitions or the upstream OpenAPI schema when a link to
  the authoritative source is available.
- If the same validation failure persists after two fix attempts, stop and ask for help
  in Jira.
