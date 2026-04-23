# AGENTS.md - AI Agent Guidelines for This Repository

## Repository Overview

This is a **skills repository** containing AI agent capabilities (skills) that extend the functionality of AI coding assistants. Skills are defined in `.agents/skills/<skill-name>/SKILL.md` files using a specific format with YAML frontmatter.

## Project Structure

```
.agents/
├── skills/
│   ├── brainstorming/SKILL.md
│   ├── databases/SKILL.md
│   ├── documentation/SKILL.md
│   ├── executing-plans/SKILL.md
│   ├── ui-ux-pro-max/SKILL.md
│   ├── web-design-guidelines/SKILL.md
│   └── writing-plans/SKILL.md
skills-lock.json
```

## Available Skills

| Skill | Purpose |
|-------|---------|
| brainstorming | Creative work, feature planning, requirements exploration |
| databases | MongoDB and PostgreSQL operations, schemas, queries |
| documentation | Writing and reviewing documentation |
| executing-plans | Implementing multi-step plans with review checkpoints |
| ui-ux-pro-max | UI/UX design intelligence, 50+ styles, color palettes, accessibility |
| web-design-guidelines | Web interface guidelines compliance, accessibility audits |
| writing-plans | Creating specs and requirements documents |

## Build/Lint/Test Commands

This repository contains **no build, lint, or test commands** as it is not a traditional application codebase. It consists solely of markdown-based skill definitions.

- **No build required**: Skills are plain Markdown files with YAML frontmatter
- **No tests**: No test suite exists for this repository
- **No linting**: No code linting is applicable

## Code Style Guidelines

### Skill File Format

All skills follow this structure:

```yaml
---
name: <skill-name>
description: "<description>"
---

# Skill Title

## When to Apply

...

## Rule Categories by Priority

...

## Detailed Rules

...
```

### YAML Frontmatter

- Always use `---` delimiters at the top of skill files
- Include `name` (kebab-case) and `description` (1-2 sentences, concise)
- Keep description under 500 characters
- Do not use complex YAML structures (arrays, nested objects)

### Markdown Content

- Use ATX-style headers (`#`, `##`, `###`)
- Maximum header depth: `####`
- Use bullet points for lists
- Use tables for structured data
- Keep lines under 120 characters when possible
- Use code blocks with language identifiers for examples

### Naming Conventions

- Skill names: kebab-case (e.g., `ui-ux-pro-max`, `web-design-guidelines`)
- File names: lowercase with hyphens
- Section headers: Title Case
- References to skills: backtick-quoted (e.g., `brainstorming` skill)

### File Organization

Each skill directory should contain:
- `SKILL.md` - Main skill definition (required)
- `REFERENCE.md` - Optional reference materials
- `scripts/` - Optional helper scripts
- `data/` - Optional data files

### Best Practices for Skill Development

1. **Clear scope**: Define when the skill must/should be used and when to skip it
2. **Priority ordering**: Order rules by priority (1 = highest)
3. **Actionable rules**: Rules should be specific and actionable
4. **Examples**: Include concrete examples where helpful
5. **Cross-references**: Reference other skills when relevant

## Error Handling

- Skills are read-only documentation; no runtime errors possible
- If a skill file is malformed, the YAML frontmatter parsing will fail
- Always validate YAML syntax when editing frontmatter

## Working with This Repository

### Loading a Skill

Use the `skill` tool to load a skill when appropriate:

```python
skill(name="ui-ux-pro-max")  # For UI/UX tasks
skill(name="brainstorming")  # For planning/creative work
skill(name="databases")      # For database tasks
```

### Making Edits

1. Read the existing SKILL.md to understand structure
2. Follow the YAML frontmatter + Markdown format
3. Maintain consistent header hierarchy
4. Keep descriptions concise and actionable

### When to Use This Repository

- Loading skills for specific tasks (UI design, database work, planning)
- Reading skill documentation to understand capabilities
- Updating skill definitions to improve agent performance
- Adding new skills following the established format

## Additional Resources

- Skills are sourced from various GitHub repositories (see `skills-lock.json`)
- Some skills have additional scripts, data files, or reference materials
- Check individual SKILL.md files for detailed usage instructions
