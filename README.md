# marketplace-nu

A Claude Code plugin marketplace for student VPS provisioning and setup.

## Installation

```bash
# Add this marketplace to Claude Code
/plugin marketplace add jrenaldi79/marketplace-nu
```

## Available Plugins

### hetzner-student-servers

Batch-create Hetzner Cloud VPS instances for student classrooms.

```bash
/plugin install hetzner-student-servers@marketplace-nu
```

**For teachers.** Takes a CSV roster of students and provisions a fully configured VPS for each, complete with SSH keys, RDP passwords, KDE Plasma desktop, and pre-installed tools.

### student-claude-setup

Configure a student's local machine to connect to their Claude Code VPS.

```bash
/plugin install student-claude-setup@marketplace-nu
```

**For students.** Sets up SSH config, key permissions, tmux persistence, RDP shortcuts, and optional Google Drive sync.

## Requirements

- **Teachers:** Python 3, [Hetzner CLI](https://github.com/hetznercloud/cli) (`hcloud`)
- **Students:** Python 3
