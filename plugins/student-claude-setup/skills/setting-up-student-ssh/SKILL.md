---
name: setting-up-student-ssh
description: Use when a student needs to configure their local machine to connect to their assigned Claude Code VPS, including SSH key setup, tmux persistence, RDP shortcuts, and Google Drive sync.
---

# Setting Up Student SSH

Configures a student's local machine to connect to their remote VPS. Handles SSH key placement, permissions, config alias with tmux persistence, RDP shortcut creation, and optional Google Drive sync.

## Prerequisites

- Student has been assigned a server IP address
- Student has downloaded their private SSH key file

## When to Use

- A student has received their server credentials and needs to configure their local machine
- Setting up SSH, RDP, and file sync for a new student workstation

## When NOT to Use

- Provisioning servers (use `hetzner-student-servers` plugin instead)
- Troubleshooting an existing connection (check SSH config manually)

## Workflow

1. Ask the student for:
   - The IP address of their assigned server
   - The local path to their private SSH key file
2. Run the setup script:
   ```bash
   python ${CLAUDE_PLUGIN_ROOT}/scripts/setup_ssh.py <ip_address> <path_to_key>
   ```
3. The script will automatically:
   - Copy the SSH key to `~/.ssh/student_claude_key` with `600` permissions
   - Add a `claude-box` host alias to `~/.ssh/config` with tmux auto-attach
   - Create a `Claude-Box-Visual.rdp` shortcut on the Desktop
   - Prompt for optional Google Drive sync via rclone
   - Test the SSH connection and provide troubleshooting if it fails
4. Instruct the student on connection options:
   - **Terminal:** `ssh claude-box`
   - **File Sync:** Work in `projects/GoogleDrive` on the VPS
   - **Visual Desktop:** Double-click `Claude-Box-Visual.rdp`
   - **VS Code:** Install Remote-SSH extension, connect to `claude-box`

## Quick Reference

| Action | Command/Path |
|--------|-------------|
| SSH connect | `ssh claude-box` |
| SSH config alias | `~/.ssh/config` → `Host claude-box` |
| SSH key location | `~/.ssh/student_claude_key` |
| RDP shortcut | `~/Desktop/Claude-Box-Visual.rdp` |
| File sync folder | `projects/GoogleDrive` (on VPS) |

## Common Mistakes

- **Key permissions too open**: Script sets `chmod 600` automatically. If SSH still rejects, verify no other copies exist.
- **Existing claude-box config**: Script detects and skips if `Host claude-box` already exists. To update, manually edit `~/.ssh/config`.
- **RDP client missing on macOS**: Install "Microsoft Remote Desktop" or "Windows App" from the Mac App Store.
