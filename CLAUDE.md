# marketplace-nu

## Project Overview

Claude Code plugin marketplace hosted at `jrenaldi79/marketplace-nu`. Contains plugins for provisioning and configuring student VPS environments.

## Structure

- `.claude-plugin/marketplace.json` — marketplace index listing all plugins
- `plugins/<name>/` — individual plugins, each with:
  - `.claude-plugin/plugin.json` — plugin manifest
  - `skills/<skill-name>/SKILL.md` — skill definition
  - `scripts/` — supporting scripts

## Adding a New Plugin

1. Create `plugins/<plugin-name>/` with the structure above
2. Add the plugin entry to `.claude-plugin/marketplace.json`
3. Bump the marketplace `metadata.version`

## Conventions

- Skill names use gerund form (verb + -ing)
- SKILL.md descriptions start with "Use when..."
- Scripts use `${CLAUDE_PLUGIN_ROOT}` for portable paths
- External dependencies are documented in Prerequisites sections
