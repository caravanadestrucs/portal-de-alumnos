# Skill Registry — portal-alumnos-fv

## Metadata

- **Generated**: 2026-06-19
- **Project**: portal-alumnos-fv
- **Persistence**: none (ephemeral)

---

## User-Level Skills

### ~/.config/opencode/skills/ (opencode skills)

These are all SDD pipeline skills (`sdd-*`) and shared conventions. They are excluded from the registry per registry rules (SDD skills are infrastructure, not application skills).

| Directory | Type | Note |
|-----------|------|------|
| `sdd-init/` | SDD pipeline | Init phase |
| `sdd-explore/` | SDD pipeline | Explore phase |
| `sdd-propose/` | SDD pipeline | Proposal phase |
| `sdd-spec/` | SDD pipeline | Specs phase |
| `sdd-design/` | SDD pipeline | Design phase |
| `sdd-tasks/` | SDD pipeline | Tasks phase |
| `sdd-apply/` | SDD pipeline | Apply phase |
| `sdd-verify/` | SDD pipeline | Verify phase |
| `sdd-archive/` | SDD pipeline | Archive phase |
| `_shared/` | Shared conventions | Openspec & Engram conventions |

### Other user-level directories

| Directory | Exists | Skills Found |
|-----------|--------|-------------|
| `~/.claude/skills/` | No | N/A |

---

## Project-Level Skills

### `.agents/skills/` (project skills)

| Skill | Description | Trigger | Files |
|-------|-------------|---------|-------|
| `brainstorming` | You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation. | Implicit | `SKILL.md`, `visual-companion.md`, `spec-document-reviewer-prompt.md` |
| `databases` | Work with MongoDB (document database, BSON documents, aggregation pipelines, Atlas cloud) and PostgreSQL (relational database, SQL queries, psql CLI, pgAdmin). Use when designing database schemas, writing queries and aggregations, optimizing indexes for performance, performing database migrations, configuring replication and sharding, implementing backup and restore strategies, managing database users and permissions, analyzing query performance, or administering production databases. | Implicit | `SKILL.md`, `references/mongodb-aggregation.md`, `references/mongodb-atlas.md`, `references/mongodb-crud.md`, `references/mongodb-indexing.md`, `references/postgresql-administration.md`, `references/postgresql-performance.md`, `references/postgresql-psql-cli.md`, `references/postgresql-queries.md` |
| `documentation` | Documentation. Use when writing docs or reviewing documentation. | Files: `*.md`, `README*`, `CHANGELOG*`, `docs/**`. Keywords: `doc`, `documentation`, `README`, `CHANGELOG`, `ADR` | `SKILL.md`, `REFERENCE.md` |
| `executing-plans` | Use when you have a written implementation plan to execute in a separate session with review checkpoints | Implicit | `SKILL.md` |
| `ui-ux-pro-max` | UI/UX design intelligence for web and mobile. Includes 50+ styles, 161 color palettes, 57 font pairings, 161 product types, 99 UX guidelines, and 25 chart types across 10 stacks. Actions: plan, build, create, design, implement, review, fix, improve, optimize, enhance, refactor. | Implicit | `SKILL.md` |
| `web-design-guidelines` | Review UI code for Web Interface Guidelines compliance. Use when asked to "review my UI", "check accessibility", "audit design", "review UX", or "check my site against best practices". | Keywords: review UI, accessibility, audit design, UX, best practices | `SKILL.md` |
| `writing-plans` | Use when you have a spec or requirements for a multi-step task, before touching code | Implicit | `SKILL.md`, `plan-document-reviewer-prompt.md` |

### Other project-level directories

| Directory | Exists | Skills Found |
|-----------|--------|-------------|
| `.claude/skills/` | No | N/A |

---

## Project Conventions

| File | Exists | Content |
|------|--------|---------|
| `AGENTS.md` | ✅ Yes | AI Agent guidelines for this repository. Lists available skills: `brainstorming`, `databases`, `documentation`, `executing-plans`, `ui-ux-pro-max`, `web-design-guidelines`, `writing-plans`. |
| `CLAUDE.md` | ❌ No | N/A |
| `.cursorrules` | ❌ No | N/A |
| `GEMINI.md` | ❌ No | N/A |
| `copilot-instructions.md` | ❌ No | N/A |

---

## Registry Summary

- **Total skills discovered**: 7 (project-level)
- **User-level skills (excluded)**: 9 SDD pipeline skills
- **Convention files**: 1 (`AGENTS.md`)
- **Skill sources**: `.agents/skills/` only
