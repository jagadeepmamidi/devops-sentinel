# Antigravity Agent Rules

## General Behavior
- Prefer minimal, targeted changes over broad refactors.
- Do not introduce new dependencies unless explicitly requested.
- Do not modify configuration, environment variables, or secrets unless explicitly requested.
- Always explain intent before applying large or risky changes.

---

## Skill Invocation Policy
Skills are capabilities, not defaults.
They MUST NOT be invoked automatically.

If a task is ambiguous, ask the user before invoking any skill.

---

## web-design-guidelines
- Invoke ONLY when the user explicitly asks for:
  - UI review
  - accessibility review
  - web interface guidelines
  - frontend audit
- MUST NOT run during:
  - feature development
  - bug fixing
  - refactoring
  - backend-only tasks
- This skill is REVIEW-ONLY.
- Do NOT modify code unless the user explicitly asks to apply fixes.

---

## vercel-react-best-practices
- Invoke ONLY when the user explicitly asks for:
  - React best practices
  - component review
  - hooks review
  - React performance review
- MUST NOT run during:
  - feature implementation
  - bug fixing
  - rapid prototyping
- This skill is REVIEW-FIRST.
- Apply code changes ONLY with explicit permission.

---

## supabase-postgres-best-practices
- Invoke ONLY when the user explicitly asks for:
  - database review
  - postgres best practices
  - supabase schema review
  - RLS review
  - SQL performance audit
- MUST NOT run automatically.
- STRICTLY REVIEW-ONLY.
- MUST NOT:
  - apply migrations
  - modify schemas
  - change RLS policies
  - execute SQL
- Provide recommendations only, never direct changes unless explicitly requested.

---

## Safety Defaults
- Never assume production access.
- Never apply destructive operations.
- When in doubt, stop and ask.
