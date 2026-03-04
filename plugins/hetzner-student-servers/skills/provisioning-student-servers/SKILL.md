---
name: provisioning-student-servers
description: Use when a teacher needs to batch-create Hetzner Cloud VPS instances for a class of students from a CSV of names and emails, with SSH keys, RDP passwords, and cloud-init provisioning.
---

# Provisioning Student Servers

Automates batch creation of Hetzner Cloud VPS instances for student classrooms. Each server gets a unique SSH key, RDP password, KDE Plasma desktop, and pre-installed dev tools (Node.js, Claude Code, GitHub CLI, rclone).

## Prerequisites

- `hcloud` CLI installed and authenticated
- Python 3.x installed

## When to Use

- Teacher has a CSV roster of students (Name, Email) and needs VPS instances provisioned
- Setting up a new classroom or cohort with remote development environments

## When NOT to Use

- Managing existing servers (use `hcloud` directly)
- Single-server setup (use `hcloud server create` manually)

## Input CSV Format

```csv
Name,Email
John Doe,john@example.com
Jane Smith,jane@example.com
```

## Workflow

1. Ask the user for the path to their CSV file containing students' names and emails.
2. Run the provisioning script:
   ```bash
   python ${CLAUDE_PLUGIN_ROOT}/scripts/create_servers.py <path_to_csv>
   ```
3. The script will automatically:
   - Generate an Ed25519 SSH key per student in `student_keys/`
   - Upload the public key to Hetzner
   - Create a `cpx31` server (Ubuntu 24.04, Ashburn) per student
   - Run cloud-init installing Node.js, Claude Code, Claude Desktop, GitHub CLI, rclone, KDE Plasma + XRDP
   - Create a `student` Linux user with a unique RDP password
   - Output `student_servers_output.csv` with server names, IPs, RDP passwords, and SSH key paths
4. Report the output CSV path and `student_keys/` directory to the user for distribution.

## Quick Reference

| Item | Value |
|------|-------|
| Server type | `cpx31` (4 cores, 8GB RAM, x86) |
| Image | Ubuntu 24.04 |
| Location | Ashburn (`ash`) |
| Desktop | KDE Plasma + XRDP |
| Output | `student_servers_output.csv` |

## Common Mistakes

- **Duplicate server names**: Script checks for existing servers and skips. No action needed.
- **Missing hcloud auth**: Run `hcloud context create` first to authenticate.
- **CSV encoding issues**: Ensure UTF-8 encoding. The script handles BOM (`utf-8-sig`).
