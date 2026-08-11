# DevOps Sentinel Upgrade Plan

## Completed in this iteration

1. Establish `sentinel/` as canonical runtime package; leave legacy trees untouched for safe migration.
2. Extract authenticated incident operations into an application service used by MCP.
3. Make MCP responses structured, keep read-only tools as default, and preserve stdio entrypoint.
4. Create public TypeScript HTTP client package at `packages/client`.
5. Rename distribution metadata to `devops-sentinel-next` for new PyPI ownership.
6. Reduce default install weight by moving AI/CrewAI dependencies into the `ai` extra.
7. Rewrite public README around product value, architecture, MCP, npm client, safety, and release flow.

## Next iteration

- Add API v1 versioning and generated OpenAPI TypeScript types.
- Add MCP integration tests and tool-level authorization tests.
- Add approval tokens, audit records, and dry-run for remediation tools.
- Remove duplicate `src/` and top-level modules only after import audit.
- Publish package after account/name ownership checks.
