import csv
import subprocess
import os
import argparse
import random
import string

SETUP_SCRIPT_TEMPLATE = """#!/bin/bash
export DEBIAN_FRONTEND=noninteractive

# Update package lists
apt-get update

# Install basic dependencies (Git, Python, pip, curl, wget, tmux)
apt-get install -y git python3 python3-pip curl wget tmux

# Install Remote Desktop Environment (KDE Plasma), XRDP, and Samba
apt-get install -y kde-plasma-desktop xrdp dbus-x11 samba fuse3

# Install Google Chrome (Firefox snap doesn't work with XRDP)
wget -q -O /tmp/chrome.deb 'https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb'
apt-get install -y /tmp/chrome.deb
rm /tmp/chrome.deb

# Install rclone
curl https://rclone.org/install.sh | bash

# Allow non-root users to mount (required for rclone)
sed -i 's/#user_allow_other/user_allow_other/' /etc/fuse.conf

# Install Node.js (Version 20 LTS)
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# Install GitHub CLI (gh)
mkdir -p -m 755 /etc/apt/keyrings
wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null
chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null
apt-get update
apt-get install -y gh

# Install Claude Desktop (GUI)
curl -fsSL https://aaddrick.github.io/claude-desktop-debian/KEY.gpg | gpg --dearmor -o /usr/share/keyrings/claude-desktop.gpg
echo "deb [signed-by=/usr/share/keyrings/claude-desktop.gpg arch=amd64,arm64] https://aaddrick.github.io/claude-desktop-debian stable main" | tee /etc/apt/sources.list.d/claude-desktop.list
apt-get update
apt-get install -y claude-desktop

# Create student user and set password
useradd -m -s /bin/bash -G sudo student
echo "student:{password}" | chpasswd

# Install Claude Code (Native Installer) for the student
su - student -c "curl -fsSL https://claude.ai/install.sh | bash"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> /home/student/.bashrc

# Configure XRDP to use KDE Plasma
echo "exec startplasma-x11" > /home/student/.xsession
chown student:student /home/student/.xsession

# Clean up and Fix XRDP startwm.sh for KDE Plasma (Prevents Black Screen)
cat << 'WMEOF' > /etc/xrdp/startwm.sh
#!/bin/sh
if test -r /etc/profile; then
        . /etc/profile
fi
if test -r ~/.profile; then
        . ~/.profile
fi

unset DBUS_SESSION_BUS_ADDRESS
unset XDG_RUNTIME_DIR

exec startplasma-x11
WMEOF
chmod +x /etc/xrdp/startwm.sh

# Add xrdp user to ssl-cert group
adduser xrdp ssl-cert

# Configure XRDP for auto-login (skip login dialog entirely)
# - autorun=Xorg: auto-select the Xorg session type
# - hidelogwindow=true: hide the XRDP login dialog
# - Hardcode student credentials in [Xorg] section
# - Remove all other session types (Xvnc, vnc-any, neutrinordp-any)
sed -i 's/^autorun=$/autorun=Xorg/' /etc/xrdp/xrdp.ini
sed -i 's/^#hidelogwindow=true/hidelogwindow=true/' /etc/xrdp/xrdp.ini
sed -i '/^\[Xorg\]/,/^\[/ { s/^username=ask/username=student/; s/^password=ask/password={password}/ }' /etc/xrdp/xrdp.ini
sed -i '/^\[Xvnc\]/,$d' /etc/xrdp/xrdp.ini

# Start and enable XRDP
systemctl enable xrdp
systemctl restart xrdp

# Create a default projects directory for the student
mkdir -p /home/student/projects/my-first-project
mkdir -p /home/student/projects/GoogleDrive

# Copy authorized SSH keys from root to student so they can SSH in as 'student'
mkdir -p /home/student/.ssh
cp /root/.ssh/authorized_keys /home/student/.ssh/authorized_keys
chown -R student:student /home/student/.ssh
chmod 700 /home/student/.ssh
chmod 600 /home/student/.ssh/authorized_keys
chown -R student:student /home/student/projects

# Ensure the entire student home directory is owned by the student user
# (KDE Plasma creates config files as root during cloud-init, causing "not writable" errors on RDP login)
chown -R student:student /home/student

# Allow student to manage network without PolicyKit prompts on RDP login
cat << 'PKEOF' > /etc/polkit-1/rules.d/50-allow-network-manager.rules
polkit.addRule(function(action, subject) {
    if (action.id.indexOf("org.freedesktop.NetworkManager") === 0 && subject.user === "student") {
        return polkit.Result.YES;
    }
});
PKEOF

# Configure SMB Share
cat << 'EOF' >> /etc/samba/smb.conf

[workspace]
    path = /home/student/projects
    valid users = student
    read only = no
    browsable = yes
    create mask = 0755
    directory mask = 0755
EOF

# Set Samba password for student
(echo "{password}"; echo "{password}") | smbpasswd -s -a student

# Restart Samba
systemctl restart smbd
"""

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"Error running: {cmd}")
        print(result.stderr)
        return False, result.stderr
    return True, result.stdout

def generate_password(length=12):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def main():
    parser = argparse.ArgumentParser(description="Batch create Hetzner servers for students.")
    parser.add_argument("csv_file", help="Path to input CSV with 'Name' and 'Email' columns")
    parser.add_argument("--output", default="student_servers_output.csv", help="Path to output CSV")
    parser.add_argument("--keys-dir", default="student_keys", help="Directory to store generated SSH keys")
    args = parser.parse_args()

    os.makedirs(args.keys_dir, exist_ok=True)
    
    students = []
    with open(args.csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            students.append(row)
            
    out_fields = ["Name", "Email", "Server_Name", "IP_Address", "RDP_Password", "SSH_Key_Path"]
    with open(args.output, 'w', newline='', encoding='utf-8') as out_f:
        writer = csv.DictWriter(out_f, fieldnames=out_fields)
        writer.writeheader()

        for s in students:
            name = s.get('Name', '').strip()
            email = s.get('Email', '').strip()
            if not name:
                continue
                
            safe_name = name.lower().replace(' ', '-')
            server_name = f"student-{safe_name}"
            key_name = f"key-{safe_name}"
            key_path = os.path.join(args.keys_dir, key_name)
            
            # Generate unique password
            rdp_password = generate_password()
            
            print(f"Processing {name} ({email})...")
            
            # Write custom cloud-init script for this student
            setup_script_content = SETUP_SCRIPT_TEMPLATE.replace("{password}", rdp_password)
            setup_file_path = f"setup_{safe_name}.sh"
            with open(setup_file_path, "w") as f:
                f.write(setup_script_content)
            
            # 1. Generate SSH Key
            if not os.path.exists(key_path):
                run_cmd(f"ssh-keygen -t ed25519 -f '{key_path}' -N '' -C '{email}'")
            
            # 2. Upload SSH Key to Hetzner
            success, out = run_cmd(f"hcloud ssh-key list -o columns=name | grep -w '{key_name}'")
            if not success or key_name not in out:
                success, out = run_cmd(f"hcloud ssh-key create --name '{key_name}' --public-key-from-file '{key_path}.pub'")
                if not success:
                    print(f"Failed to create ssh key in Hetzner for {name}")
                    continue
                    
            # 3. Create server with cloud-init
            # Check if server already exists
            success, out = run_cmd(f"hcloud server list -o columns=name | grep -w '{server_name}'")
            if success and server_name in out:
                print(f"Server {server_name} already exists. Skipping creation.")
            else:
                cmd = f"hcloud server create --name '{server_name}' --type cpx31 --image ubuntu-24.04 --location ash --ssh-key '{key_name}' --user-data-from-file {setup_file_path}"
                print(f"Creating server {server_name}...")
                success, out = run_cmd(cmd)
                if not success:
                    print(f"Failed to create server {server_name}")
                    if os.path.exists(setup_file_path):
                        os.remove(setup_file_path)
                    continue
                
            # 4. Get IP
            success, ip_out = run_cmd(f"hcloud server ip '{server_name}'")
            ip_address = ip_out.strip() if success else "ERROR"
            
            print(f"Success! Server {server_name} IP: {ip_address}")
            
            writer.writerow({
                "Name": name,
                "Email": email,
                "Server_Name": server_name,
                "IP_Address": ip_address,
                "RDP_Password": rdp_password,
                "SSH_Key_Path": os.path.abspath(key_path)
            })

            # Cleanup custom setup script
            if os.path.exists(setup_file_path):
                os.remove(setup_file_path)

    print(f"\nAll done! Wrote results to {args.output}")

if __name__ == "__main__":
    main()
